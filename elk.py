"""
If you choose to run the ELK-stack in a local docker container, this script will install
the stack and start the container.
"""
import subprocess
import os
from shutil import copyfile


def check_git():
    try:
        subprocess.run(['git', '--version'])
    except FileNotFoundError:
        print('Git was not found. Please install it.')
        return False
    return True


def check_dockercompose():
    try:
        subprocess.run(['docker-compose', '--version'])
    except FileNotFoundError:
        subprocess.run(['pip', 'install', 'docker-compose'])
    return True


def get_elk_stack():
    # check if git is present
    if not check_git():
        return False
    # change to the correct path
    old_wd = os.getcwd()
    os.chdir(os.path.join(os.path.dirname(__file__), 'metacatalog2/elk'))

    # if stack-docker exists, update, else clone
    if os.path.exists('stack-docker'):
        os.remove('stack-docker/docker-compose.yml')
        os.remove('stack-docker/.env')
        os.chdir('stack-docker')
        subprocess(['git', 'pull', 'origin', 'master'])
        os.chdir('../')
    else:
        subprocess.run(['git', 'clone', 'https://github.com/elastic/stack-docker.git'])

    # make a new dir and save the original docker-compose.yml
    os.mkdir('stack-docker/old-docker-compose')
    copyfile('docker-compose.yml', 'stack-docker/docker-compose.yml')
    copyfile('.env', 'stack-docker/.env')

    # restore the original wd
    os.chdir(old_wd)
    print('The ELK stack is installed. Run it using the \'run\' keyword ')

    return True


def run_elk():
    # check if the stack was already installed
    path = os.path.join(os.path.dirname(__file__), 'metacatalog2/elk/stack-docker')
    if not os.path.exists(path):
        print('The docker-stack is not installed, run get_elk_stack first.')
        return False
    else:
        # got to the location
        old_wd = os.getcwd()
        os.chdir(path)

    # if docker compose is installed, run the stack
    if check_dockercompose():
        subprocess.run(['docker-compose', 'up', '-d'])

    # restore original wd
    os.chdir(old_wd)
    print('ELK is running on localhost\nelasticsearch  https://localhost:9200\nkibana         https://localhost:5601')

    return True


if __name__ == '__main__':
    import sys
    if 'install' in sys.argv or 'update' in sys.argv:
        get_elk_stack()
    if 'run' in sys.argv:
        run_elk()

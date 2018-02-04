"""
If you choose to run the ELK-stack in a local docker container, this script will install
the stack and start the container.
"""
import subprocess
import os
from shutil import copyfile

from elasticsearch import Elasticsearch
from elasticsearch import AuthenticationException


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
    print('ELK is running on localhost\nelasticsearch  http://localhost:9200\nkibana         http://localhost:5601')

    return True


def elk_health():
    # get user and password
    user = 'elastic'
    # get password, a bit dirty...
    # TODO this should be moved into the flask app config object.
    with open(os.path.join(os.path.dirname(__file__), 'metacatalog2/elk/.env',), 'r') as f:
        env = f.read()
    for line in env.split('\n'):
        if line.split('=')[0].strip() == 'ELASTIC_PASSWORD':
            pw = line.split('=')[1].strip()

    # init a ES object.
    # TODO host and port need to be set from the config in the main app
    es = Elasticsearch(['http://%s:%s@localhost:9200' % (user, pw)])
    print('Elasticsearch status:\n')
    try:
        print(es.cat.health())
    except AuthenticationException as e:
        print('Failed!\n\n%s' % str(e))

    return True


if __name__ == '__main__':
    import sys
    if 'install' in sys.argv or 'update' in sys.argv:
        get_elk_stack()
    if 'run' in sys.argv:
        run_elk()
        elk_health()
    elif 'status' in sys.argv or 'health' in sys.argv:
        elk_health()

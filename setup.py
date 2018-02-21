from setuptools import setup, find_packages


def readme():
    with open('README.rst') as f:
        return f.read().strip()


def version():
    with open('VERSION') as f:
        return f.read().strip()


def requirements():
    with open('requirements.txt') as f:
        return f.read().strip().split('\n')


def classifiers():
    with open('classifiers.txt') as f:
        return f.read().strip().split('\n')


setup(name='metacatalog2',
      license='MIT',
      version=version(),
      author='Mirko Mälicke',
      author_email='mirko.maelicke@kit.edu',
      description='Metadata catalog for environmental data',
      long_description=readme(),
      classifiers=classifiers(),
      install_requirements=requirements(),
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False
)
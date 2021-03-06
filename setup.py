# -*- coding: utf-8 -*-

from setuptools import (
    find_packages,
    setup,
)

def readfile(path):
    with open(path, 'r') as stream:
        content = stream.read()
        if hasattr(path, 'decode'):
            content = content.decode('utf-8')
        return content

version = readfile('gitmesh_deploy/version.txt').strip()
readme = readfile('README.rst').strip()

setup(
    name='gitmesh-deploy',
    version=version,
    url='https://github.com/smartmob-project/pushy',
    maintainer='Nicolas Mivielle',
    maintainer_email='nm@smartmob.org',
    description='Something that will push your code',
    long_description=readme,
    packages=find_packages(),
    package_data={
        'gitmesh_deploy': [
            'version.txt',
        ],
    },
    entry_points={
        'gitmesh.post_receive': [
            'gitmesh_deploy = gitmesh_deploy:post_receive'
        ],
        'gitmesh.post_update': [],
    },
)

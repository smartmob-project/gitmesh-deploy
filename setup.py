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

setup(
    name='gitmesh_deploy',
    version=version,
    url='https://github.com/smartmob-project/pushy',
    maintainer='Nicolas Mivielle',
    maintainer_email='sonic1200@gmail.com',
    description='Something that will push your code',
    long_description='no',
    packages=find_packages(),
    package_data={
        'gitmesh_deploy': [
            'version.txt',
        ],
    },
    entry_points={
        'gitmesh.post_receive': ["gitmesh_deploy = gitmesh_deploy:post_receive"],
        'gitmesh.post_update': [],
    },
)

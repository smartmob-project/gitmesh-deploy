# -*- coding: utf-8 -*-

import pkg_resources

version = pkg_resources.resource_string('gitmesh_deploy', 'version.txt')
version = version.decode('utf-8').strip()
"""Package version (as a dotted string)."""


def post_receive(updates):
    print("hello")
    update = updates.get('refs/heads/master')
    if update:
        new_sha = update[1]
        print('Deploying "%s".' % new_sha)

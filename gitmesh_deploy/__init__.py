# -*- coding: utf-8 -*-


import aiohttp
import asyncio
import json
import os
import pkg_resources
import subprocess
import tempfile
import urllib.parse


version = pkg_resources.resource_string('gitmesh_deploy', 'version.txt')
version = version.decode('utf-8').strip()
"""Package version (as a dotted string)."""


async def check_output(command):
    if isinstance(command, list):
        command = ' '.join([
            "'%s'" % arg for arg in command
        ])
    process = await asyncio.create_subprocess_shell(
        command,
        stdin=None,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    output, _ = await process.communicate()
    output = output.decode('utf-8').strip()
    status = await process.wait()
    if status != 0:
        raise subprocess.CalledProcessError(status, command, output)
    return output


async def post_receive(updates):
    """gitmesh post-receive hook."""

    # Deploy only what comes into the master branch.
    update = updates.get('refs/heads/master')
    if update:
        # Resolve hook configuration.
        storage = os.environ['GITMESH_DEPLOY_STORAGE']
        smartmob_agent = os.environ['GITMESH_DEPLOY_SMARTMOB_AGENT']
        app = os.environ['GITMESH_DEPLOY_SMARTMOB_APP']
        with aiohttp.ClientSession() as session:

            # Archive the requested commit.
            _, path = tempfile.mkstemp('.zip')
            await check_output(
                'git archive %s --output="%s"' % (update[1], path)
            )

            # Upload the archive.
            #
            # TODO: generate a random name for the archive?
            archive_url = urllib.parse.urljoin(storage, 'archive-123')
            with open(path, 'rb') as stream:
                data = stream.read()
            async with session.put(archive_url, data=data) as r:
                assert r.status == 201

            # Start the remote process.
            #
            # TODO: contact orchestrator for formation.
            req = json.dumps({
                'app': app,
                'node': '1',
                'source_url': archive_url,
                'process_type': 'web',
                'env': {},
            }).encode('utf-8')
            async with session.get(smartmob_agent) as r:
                assert r.status == 200
                index = await r.json()
            async with session.post(index['create'], data=req) as r:
                assert r.status == 201

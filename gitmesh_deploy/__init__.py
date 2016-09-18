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

    # Access the request ID to forward it to other services.
    request_id = os.environ.get('GITMESH_REQUEST_ID', '?')

    # Deploy only what comes into the master branch.
    update = updates.get('refs/heads/master')
    if update:
        _, new_sha = update

        # Resolve hook configuration.
        storage = os.environ['GITMESH_DEPLOY_STORAGE']
        smartmob_agent = os.environ['GITMESH_DEPLOY_SMARTMOB_AGENT']
        app = os.environ['GITMESH_DEPLOY_SMARTMOB_APP']
        with aiohttp.ClientSession() as session:

            # Archive the requested commit.
            _, path = tempfile.mkstemp('%s.zip' % new_sha)
            await check_output(
                'git archive %s --output="%s"' % (new_sha, path)
            )

            # Upload the archive.
            name = os.path.basename(path)
            archive_url = urllib.parse.urljoin(storage, name)
            with open(path, 'rb') as stream:
                data = stream.read()
            head = {
                'content-type': 'application/zip',
                'x-request-id': request_id,
            }
            async with session.put(archive_url, data=data, headers=head) as r:
                assert r.status in (201, 204)

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
            head = {
                'content-type': 'application/json',
                'x-request-id': request_id,
            }
            async with session.get(smartmob_agent, headers=head) as r:
                assert r.status == 200
                assert r.headers['x-request-id'] == request_id
                index = await r.json()
            url = index['create']
            async with session.post(url, data=req, headers=head) as r:
                assert r.status == 201
                assert r.headers['x-request-id'] == request_id

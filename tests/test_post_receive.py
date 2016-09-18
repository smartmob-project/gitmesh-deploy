# -*- coding: utf-8 -*-


import aiohttp
import io
import os
import pytest
import subprocess
import sys
import zipfile

from gitmesh_deploy import post_receive, check_output
from unittest import mock


@pytest.mark.asyncio
async def test_check_output_success():
    output = await check_output([
        sys.executable, '-c', 'print("Hello!")',
    ])
    assert output.strip() == 'Hello!'


@pytest.mark.asyncio
async def test_check_output_failure():
    with pytest.raises(subprocess.CalledProcessError) as exc:
        print(await check_output([
            sys.executable, '-c', 'import sys; print("Hello!"); sys.exit(2)',
        ]))
    assert exc.value.returncode == 2


@pytest.mark.asyncio
async def test_post_receive_with_empty_dictionnary():
    await post_receive({})


@pytest.mark.asyncio
async def test_post_receive_with_other_branch_than_master():
    await post_receive({'refs/heads/branch': ('a', 'b')})


@pytest.mark.asyncio
async def test_post_receive_with_master(file_server, http_client,
                                        mock_agent, repository):

    # Run the post-receive hook.
    env = {
        'GITMESH_DEPLOY_STORAGE': file_server,
        'GITMESH_DEPLOY_SMARTMOB_AGENT': mock_agent,
        'GITMESH_DEPLOY_SMARTMOB_APP': 'foo',
        'GITMESH_REQUEST_ID': 'MY-REQUEST-ID',
    }
    with mock.patch.dict(os.environ, env):
        await post_receive({
            'refs/heads/master': ('0' * 40, 'HEAD'),
        })
        with aiohttp.ClientSession() as session:

            # Access the archive queued in the mock server.
            async with session.get(mock_agent) as r:
                assert r.status == 200
                index = await r.json()
            async with session.get(index['pending']) as r:
                assert r.status == 200
                pending = await r.json()
            pending = pending['pending']
            assert len(pending) == 1
            source_url = pending[0].pop('source_url')
            assert pending[0] == {
                'app': 'foo',
                'node': '1',
                'process_type': 'web',
                'env': {},
            }

            # Download the archive.
            async with session.get(source_url) as r:
                assert r.status == 200
                archive = await r.read()

            # Check its contents.
            with zipfile.ZipFile(io.BytesIO(archive)) as archive:
                assert archive.namelist() == ['README.txt']

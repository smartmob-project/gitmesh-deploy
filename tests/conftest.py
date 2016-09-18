# -*- coding: utf-8 -*-


import aiohttp.web
import os
import pytest
import testfixtures

from contextlib import contextmanager
from subprocess import check_output


@pytest.yield_fixture
def http_client(event_loop):
    with aiohttp.ClientSession() as session:
        yield session


@pytest.yield_fixture
def storage():
    with testfixtures.TempDirectory(create=True) as directory:
        yield directory.path
        directory.cleanup()


@pytest.yield_fixture
def file_server(event_loop, storage):
    host = '127.0.0.1'
    port = 8081

    async def upload(request):
        """Naive file upload."""
        path = os.path.join(storage, request.match_info['path'])
        data = await request.read()
        with open(path, 'wb') as stream:
            stream.write(data)
        return aiohttp.web.Response(status=201, headers={
            'x-request-id': request.headers.get('x-request-id', '?'),
        })

    # Prepare a simple unprotected file sharing app.
    app = aiohttp.web.Application(loop=event_loop)
    app.router.add_static('/', storage)
    app.router.add_route('PUT', '/{path:.+}', upload)

    # Start listening for connections.
    handler = app.make_handler()
    server = event_loop.run_until_complete(event_loop.create_server(
        handler, host, port,
    ))

    # Let the test run.
    yield 'http://%s:%d/' % (host, port)

    # Close up shop.
    server.close()
    event_loop.run_until_complete(server.wait_closed())
    event_loop.run_until_complete(handler.finish_connections(1.0))
    event_loop.run_until_complete(app.finish())


@pytest.yield_fixture
def mock_agent(event_loop, storage):
    host = '127.0.0.1'
    port = 8082

    requests = []

    async def index(request):
        return aiohttp.web.json_response({
            'create': '%s://%s%s' % (
                request.scheme,
                request.host,
                request.app.router['create-process'].url(),
            ),
            'pending': '%s://%s%s' % (
                request.scheme,
                request.host,
                request.app.router['pending'].url(),
            ),
        }, headers={
            'x-request-id': request.headers.get('x-request-id', '?'),
        })

    async def deploy(request):
        requests.append(await request.json())
        return aiohttp.web.Response(status=201, headers={
            'x-request-id': request.headers.get('x-request-id', '?'),
        })

    async def pending(request):
        return aiohttp.web.json_response({
            'pending': requests,
        }, headers={
            'x-request-id': request.headers.get('x-request-id', '?'),
        })

    # Prepare a simple unprotected file sharing app.
    app = aiohttp.web.Application(loop=event_loop)
    app.router.add_route('GET', '/', index, name='index')
    app.router.add_route('POST', '/create-process',
                         deploy, name='create-process')
    app.router.add_route('GET', '/pending', pending, name='pending')

    # Start listening for connections.
    handler = app.make_handler()
    server = event_loop.run_until_complete(event_loop.create_server(
        handler, host, port,
    ))

    # Let the test run.
    yield 'http://%s:%d/' % (host, port)

    # Close up shop.
    server.close()
    event_loop.run_until_complete(server.wait_closed())
    event_loop.run_until_complete(handler.finish_connections(1.0))
    event_loop.run_until_complete(app.finish())


@contextmanager
def cwd(new_cwd):
    old_cwd = os.getcwd()
    os.chdir(new_cwd)
    try:
        yield
    finally:
        os.chdir(old_cwd)


@pytest.yield_fixture
def repository():
    with testfixtures.TempDirectory(create=True) as directory:

        # Move into the directory.
        with cwd(directory.path):

            # Prepare a new git repository and add some contents.
            check_output(['git', 'init'])
            check_output(['git', 'config', 'user.name', '"py.test"'])
            check_output([
                'git', 'config', 'user.email', '"noreply@example.org"',
            ])
            with open('README.txt', 'w') as stream:
                stream.write('Hello, world!')
            check_output(['git', 'add', 'README.txt'])
            check_output(['git', 'commit', '-m', '"Starts project."'])

            # Let the test run.
            yield

        # Remove anything created in this folder.
        directory.cleanup()

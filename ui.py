"""HTML UI entry point. Run: uvicorn ui:app --reload"""
import os
import sys
import threading
import time
import urllib.request
import webbrowser
from contextlib import asynccontextmanager
from pathlib import Path

from starlette.applications import Starlette
from starlette.responses import FileResponse, JSONResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
# Windows consoles may default to an encoding that cannot print model answers.
# Configure the presentation process before loading the unchanged backend.
for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, 'reconfigure'):
        stream.reconfigure(encoding='utf-8', errors='backslashreplace')

from app.main import app as backend

ROOT = Path(__file__).resolve().parent


def browser_url():
    def option(name, default):
        for index, value in enumerate(sys.argv):
            if value.startswith(name + '='):
                return value.split('=', 1)[1]
            if value == name and index + 1 < len(sys.argv):
                return sys.argv[index + 1]
        return default
    host = option('--host', os.getenv('UVICORN_HOST', '127.0.0.1'))
    if host in ('0.0.0.0', '::'):
        host = '127.0.0.1'
    if ':' in host and not host.startswith('['):
        host = f'[{host}]'
    port = option('--port', os.getenv('UVICORN_PORT', '8000'))
    return f'http://{host}:{port}'


def open_when_ready():
    url = browser_url()
    for _ in range(120):
        try:
            with urllib.request.urlopen(url + '/_ui/ready', timeout=1) as response:
                if response.status == 200:
                    webbrowser.open_new_tab(url)
                    return
        except OSError:
            time.sleep(0.5)


@asynccontextmanager
async def lifespan(app):
    async with backend.router.lifespan_context(backend):
        if os.getenv('FOLIO_OPEN_BROWSER', '1').lower() not in ('0', 'false', 'no'):
            threading.Thread(target=open_when_ready, daemon=True).start()
        yield


async def home(request):
    return FileResponse(ROOT / 'index.html')


async def ready(request):
    return JSONResponse({'ready': True})


app = Starlette(routes=[
    Route('/', home),
    Route('/_ui/ready', ready),
    Mount('/static', app=StaticFiles(directory=ROOT / 'static')),
    Mount('/', app=backend),
], lifespan=lifespan)


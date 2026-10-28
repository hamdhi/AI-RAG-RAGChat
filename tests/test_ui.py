"""Check the UI adapter in isolation from external AI and vector services."""
import importlib.util
import os
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from starlette.testclient import TestClient


class UiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        mock_backend = types.ModuleType('app.main')
        mock_backend.app = FastAPI()

        @mock_backend.app.post('/grok/query/')
        async def answer(question: str):
            return {'Question': question, 'Answer': 'Verified answer', 'Context': 'Page 1: Context'}

        spec = importlib.util.spec_from_file_location('folio_test_ui', Path(__file__).parent.parent / 'ui.py')
        cls.ui = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'app.main': mock_backend}):
            spec.loader.exec_module(cls.ui)

    def test_page_assets_and_api(self):
        with patch.dict(os.environ, {'FOLIO_OPEN_BROWSER': '0'}):
            with TestClient(self.ui.app) as client:
                page = client.get('/')
                self.assertEqual(page.status_code, 200)
                self.assertIn('Chat with your documents', page.text)
                for path in ('/static/style.css', '/static/app.js', '/docs', '/openapi.json', '/_ui/ready'):
                    self.assertEqual(client.get(path).status_code, 200, path)
                result = client.post('/grok/query/', params={'question': 'What matters?'})
                self.assertEqual(result.json()['Answer'], 'Verified answer')
                self.assertEqual(client.get('/missing').status_code, 404)

    def test_browser_url(self):
        with patch.object(sys, 'argv', ['uvicorn', 'ui:app', '--host', '0.0.0.0', '--port=8080']):
            self.assertEqual(self.ui.browser_url(), 'http://127.0.0.1:8080')

    def test_browser_waits_for_readiness(self):
        with patch.object(self.ui, 'browser_url', return_value='http://127.0.0.1:8000'), patch.object(self.ui.urllib.request, 'urlopen') as request, patch.object(self.ui.webbrowser, 'open_new_tab') as browser:
            request.return_value.__enter__.return_value.status = 200
            self.ui.open_when_ready()
            request.assert_called_once_with('http://127.0.0.1:8000/_ui/ready', timeout=1)
            browser.assert_called_once_with('http://127.0.0.1:8000')


if __name__ == '__main__':
    unittest.main()


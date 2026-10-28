const test = require('node:test');
const assert = require('node:assert/strict');
const { marked } = require('../static/vendor/marked.min.js');

test('formats a typical structured model answer', () => {
  const html = marked.parse('# Overview\n\nA **clear** answer with `inline code`.\n\n- First idea\n- Second idea\n\n1. Read\n2. Understand\n\n```python\nprint("hello")\n```\n\n| Topic | Value |\n| --- | --- |\n| Pages | 5 |', {gfm: true, breaks: true});
  for (const element of ['<h1>', '<strong>', '<code>', '<ul>', '<ol>', '<pre>', '<table>']) assert.ok(html.includes(element), element);
  assert.ok(html.includes('language-python'));
});

test('preserves code indentation and escapes code markup', () => {
  const html = marked.parse('```html\n  <script>alert(1)</script>\n```');
  assert.ok(html.includes('  &lt;script&gt;'));
  assert.ok(!html.includes('<script>'));
});

test('separates paragraphs and preserves intentional line breaks', () => {
  const html = marked.parse('First paragraph.\n\nSecond paragraph.\nAnother line.', {breaks: true});
  assert.equal((html.match(/<p>/g) || []).length, 2);
  assert.ok(html.includes('<br>'));
});

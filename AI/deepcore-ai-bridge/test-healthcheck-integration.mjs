import test from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { fileURLToPath } from 'node:url';

const model = 'deepseek-ai/DeepSeek-V4-Flash';
async function fixture(returnedContent) {
  const server = createServer((req, res) => {
    res.setHeader('content-type', 'application/json');
    if (req.url === '/v1/models') {
      res.end(JSON.stringify({ data: [{ id: model }] }));
    } else if (req.url === '/v1/chat/completions') {
      res.end(JSON.stringify({ choices: [{ message: { content: returnedContent } }] }));
    } else {
      res.statusCode = 404;
      res.end('{}');
    }
  });
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
  return server;
}
async function runProbe(text) {
  const server = await fixture(text);
  const port = server.address().port;
  const child = spawn(process.execPath, ['local-inference-health-check.mjs'], {
    cwd: fileURLToPath(new URL('.', import.meta.url)),
    env: { ...process.env, DEEPCORE_AI_BASE_URL: 'http://127.0.0.1:' + port + '/v1', DEEPCORE_AI_MODEL: model },
  });
  let output = '';
  child.stdout.on('data', d => { output += d.toString(); });
  child.stderr.on('data', d => { output += d.toString(); });
  const [exit] = await once(child, 'exit');
  await new Promise(resolve => server.close(resolve));
  return { exit, output };
}
test('actual health-check process accepts exact sentinel', async () => {
  const result = await runProbe('DEEPCORE_LOCAL_AI_OK');
  assert.equal(result.exit, 0, result.output);
  assert.match(result.output, /PREFLIGHT PASS/);
});
test('actual health-check process rejects arbitrary model output', async () => {
  const result = await runProbe('unrelated but nonempty');
  assert.equal(result.exit, 1, result.output);
  assert.match(result.output, /PREFLIGHT FAIL/);
});

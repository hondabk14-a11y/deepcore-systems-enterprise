import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { openTaskFileStore } from './task-file-store.mjs';
import { createTaskWorkflow } from './task-workflow.mjs';
const input = { id: 'one', fileName: 'example.mjs', source: 'sensitive source', instructions: 'review' };
const adapter = { review: async () => 'No findings.' };
const decision = t => ({ approved: true, actor: 'test-reviewer', sourceHash: t.sourceHash, proposalHash: t.proposalHash });
function fixture(t) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'deepcore-task-test-'));
  const stores = [];
  t.after(() => { for (const s of stores) s.close(); fs.rmSync(dir, { recursive: true, force: true }); });
  return { dir, open() { const store = openTaskFileStore(dir); stores.push(store); return store; } };
}
test('approval survives reopen with exact history and private snapshot', async t => {
  const f = fixture(t), store = f.open();
  const flow = createTaskWorkflow({ adapter, store });
  flow.submit(input);
  const approved = flow.decide(input.id, decision(await flow.review(input.id, input)));
  store.close();
  const restored = createTaskWorkflow({ adapter, store: f.open() });
  assert.deepEqual(restored.get(input.id), approved);
  assert.throws(() => restored.submit(input));
  assert.equal(fs.statSync(path.join(f.dir, 'tasks.json')).mode & 0o077, 0);
  assert.equal(fs.readFileSync(path.join(f.dir, 'tasks.json'), 'utf8').includes(input.source), false);
});
test('interrupted process locks storage and recovers reviewing task once after manual unlock', t => {
  const f = fixture(t);
  const script = `import { createTaskWorkflow } from ${JSON.stringify(new URL('./task-workflow.mjs', import.meta.url).href)};
import { openTaskFileStore } from ${JSON.stringify(new URL('./task-file-store.mjs', import.meta.url).href)};
const input = ${JSON.stringify(input)};
const flow = createTaskWorkflow({ adapter: { review: () => new Promise(() => {}) }, store: openTaskFileStore(${JSON.stringify(f.dir)}) });
flow.submit(input); flow.review(input.id, input); process.exit(0);`;
  const result = spawnSync(process.execPath, ['--input-type=module', '-e', script], { encoding: 'utf8', timeout: 5000 });
  assert.equal(result.status, 0, result.stderr);
  assert.throws(() => f.open(), /locked/);
  // Child termination is verified before operator-style lock removal.
  fs.rmdirSync(path.join(f.dir, '.writer-lock'));
  const store = f.open();
  const recovered = createTaskWorkflow({ adapter, store }).get(input.id);
  assert.equal(recovered.state, 'failed');
  assert.equal(recovered.error, 'REVIEW_INTERRUPTED');
  assert.equal(recovered.history.at(-1).type, 'review_interrupted');
  store.close();
  assert.deepEqual(createTaskWorkflow({ adapter, store: f.open() }).get(input.id), recovered);
});
test('exclusive writer and one workflow attachment prevent lost updates', t => {
  const f = fixture(t), store = f.open();
  createTaskWorkflow({ adapter, store });
  assert.throws(() => f.open(), /locked/);
  assert.throws(() => createTaskWorkflow({ adapter, store }), /already attached/);
});
test('invalid JSON and checksum mismatch block startup', t => {
  const f = fixture(t);
  for (const data of ['{', JSON.stringify({ version: 1, payload: '[]', checksum: 'wrong' })]) {
    fs.writeFileSync(path.join(f.dir, 'tasks.json'), data, { mode: 0o600 });
    const store = f.open();
    assert.throws(() => createTaskWorkflow({ adapter, store }), /corrupt/);
    store.close();
  }
});
test('valid checksum cannot bypass task schema or approval validation', t => {
  const f = fixture(t);
  const submitted = createTaskWorkflow({ adapter }).submit(input);
  for (const tasks of [[{ ...submitted, state: 'approved' }], [submitted, submitted], [{ ...submitted, source: 'forbidden' }], [{ ...submitted, history: [] }]]) {
    const payload = JSON.stringify(tasks);
    fs.writeFileSync(path.join(f.dir, 'tasks.json'), JSON.stringify({ version: 1, payload, checksum: createHash('sha256').update(payload).digest('hex') }), { mode: 0o600 });
    const store = f.open();
    assert.throws(() => createTaskWorkflow({ adapter, store }));
    store.close();
  }
});
test('failed submission or review-intent save cannot dispatch a provider request', async () => {
  let calls = 0, saves = 0;
  const flow = createTaskWorkflow({ adapter: { review: async () => { calls++; return 'ok'; } }, store: { load: () => [], save: () => { if (++saves === 2) throw new Error('disk full'); } } });
  flow.submit(input);
  await assert.rejects(flow.review(input.id, input), /storage unavailable/);
  assert.equal(calls, 0);
  assert.throws(() => flow.get(input.id), /storage unavailable/);
  const fail = createTaskWorkflow({ adapter, store: { load: () => [], save: () => { throw new Error('disk full'); } } });
  assert.throws(() => fail.submit(input), /storage unavailable/);
});
test('approval write failure preserves last durable awaiting-approval state', async () => {
  let disk = [], fail = false;
  const flow = createTaskWorkflow({ adapter, store: { load: () => disk, save: tasks => { if (fail) throw new Error('disk full'); disk = structuredClone(tasks); } } });
  flow.submit(input);
  const reviewed = await flow.review(input.id, input);
  fail = true;
  assert.throws(() => flow.decide(input.id, decision(reviewed)), /storage unavailable/);
  assert.equal(disk[0].state, 'awaiting_approval');
  assert.throws(() => flow.get(input.id), /storage unavailable/);
});
test('filesystem rename failure preserves previous snapshot and removes temporary file', t => {
  const f = fixture(t), store = f.open();
  const flow = createTaskWorkflow({ adapter, store });
  flow.submit(input);
  const before = fs.readFileSync(path.join(f.dir, 'tasks.json'), 'utf8');
  fs.renameSync(path.join(f.dir, 'tasks.json'), path.join(f.dir, 'saved.json'));
  fs.mkdirSync(path.join(f.dir, 'tasks.json'));
  fs.writeFileSync(path.join(f.dir, 'tasks.json', 'block'), 'block');
  assert.throws(() => flow.submit({ ...input, id: 'two' }), /storage unavailable/);
  assert.equal(fs.readFileSync(path.join(f.dir, 'saved.json'), 'utf8'), before);
  assert.equal(fs.readdirSync(f.dir).some(n => n.endsWith('.tmp')), false);
});
test('symlink snapshots and non-private directories are rejected', t => {
  const f = fixture(t);
  fs.writeFileSync(path.join(f.dir, 'other.json'), '[]', { mode: 0o600 });
  fs.symlinkSync(path.join(f.dir, 'other.json'), path.join(f.dir, 'tasks.json'));
  const store = f.open();
  assert.throws(() => createTaskWorkflow({ adapter, store }), /corrupt/);
  store.close();
  fs.chmodSync(f.dir, 0o755);
  assert.throws(() => f.open(), /private/);
});
test('review completion write failure does not become an approvable task', async () => {
  let disk = [], saves = 0;
  const flow = createTaskWorkflow({ adapter, store: { load: () => disk, save: tasks => { if (++saves === 3) throw new Error('disk full'); disk = structuredClone(tasks); } } });
  flow.submit(input);
  await assert.rejects(flow.review(input.id, input), /storage unavailable/);
  assert.equal(disk[0].state, 'reviewing');
  const restored = createTaskWorkflow({ adapter, store: { load: () => disk, save: tasks => { disk = structuredClone(tasks); } } });
  assert.equal(restored.get(input.id).error, 'REVIEW_INTERRUPTED');
});

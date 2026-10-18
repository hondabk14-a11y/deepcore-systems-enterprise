import test from 'node:test';
import assert from 'node:assert/strict';
import { createTaskWorkflow } from './task-workflow.mjs';

const input = { id: 'task-1', fileName: 'example.mjs', source: 'export const n = 1;', instructions: 'Review correctness' };
const make = (review = async () => 'Proposed correction') => createTaskWorkflow({ adapter: { review } });
const decision = (t, approved = true) => ({ approved, actor: 'local-reviewer', proposalHash: t.proposalHash, sourceHash: t.sourceHash });

test('submission, review and approval bind the exact source and proposal', async () => {
  const flow = make();
  flow.submit(input);
  const reviewed = await flow.review(input.id, input);
  assert.equal(reviewed.state, 'awaiting_approval');
  const approved = flow.decide(input.id, decision(reviewed));
  assert.equal(approved.state, 'approved');
  assert.deepEqual(approved.history.map(e => e.type), ['submitted', 'reviewing', 'review_completed', 'approved']);
  assert.equal('source' in approved, false);
  assert.throws(() => flow.decide(input.id, decision(reviewed)));
});
test('rejects changed input before calling the adapter', async () => {
  let calls = 0;
  const flow = make(async () => { calls++; return 'review'; });
  flow.submit(input);
  await assert.rejects(flow.review(input.id, { ...input, source: 'changed' }));
  await assert.rejects(flow.review(input.id, { ...input, instructions: 'changed' }));
  assert.equal(calls, 0);
});
test('rejects duplicate IDs, premature approval and stale proposal hashes', async () => {
  const flow = make();
  flow.submit(input);
  assert.throws(() => flow.submit(input));
  assert.throws(() => flow.decide(input.id, {}));
  const t = await flow.review(input.id, input);
  assert.throws(() => flow.decide(input.id, { ...decision(t), proposalHash: 'stale' }));
  assert.throws(() => flow.decide(input.id, { ...decision(t), sourceHash: 'stale' }));
  assert.equal(flow.decide(input.id, decision(t, false)).state, 'rejected');
});
test('provider failures are sanitized and cannot be approved', async () => {
  const flow = make(async () => { throw new Error('secret-provider-detail'); });
  flow.submit(input);
  const t = await flow.review(input.id, input);
  assert.equal(t.state, 'failed');
  assert.equal(JSON.stringify(t).includes('secret-provider-detail'), false);
  assert.throws(() => flow.decide(input.id, decision(t)));
});
test('only one concurrent review can start', async () => {
  let finish;
  const flow = make(() => new Promise(resolve => { finish = resolve; }));
  flow.submit(input);
  const first = flow.review(input.id, input);
  await assert.rejects(flow.review(input.id, input));
  finish('review');
  assert.equal((await first).state, 'awaiting_approval');
});
test('returned snapshots cannot mutate internal state', () => {
  const flow = make();
  const t = flow.submit(input);
  t.state = 'approved';
  t.history.length = 0;
  assert.equal(flow.get(input.id).state, 'submitted');
  assert.equal(flow.get(input.id).history.length, 1);
});

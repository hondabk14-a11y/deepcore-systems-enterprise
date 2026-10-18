import test from 'node:test';
import assert from 'node:assert/strict';
import { createReviewAdapter } from './src/review-adapter.mjs';
import { createTaskWorkflow } from './task-workflow.mjs';

const input = { id: 'one', fileName: 'example.mjs', source: 'export const n = 1;', instructions: 'Review correctness' };
function setup(create, options = {}) {
  return createTaskWorkflow({ adapter: createReviewAdapter({
    client: { responses: { create } }, model: 'offline-model', ...options,
  }) });
}
test('real adapter connects submission to review and content-bound approval', async () => {
  const calls = [];
  const flow = setup(async (...args) => { calls.push(args); return { output_text: 'No findings.' }; });
  flow.submit(input);
  const reviewed = await flow.review(input.id, input);
  assert.equal(reviewed.state, 'awaiting_approval');
  assert.equal(reviewed.proposal, 'No findings.');
  assert.equal(calls.length, 1);
  assert.equal(calls[0][0].store, false);
  assert.equal(calls[0][0].instructions, input.instructions);
  assert.ok(calls[0][0].input.includes(input.source));
  assert.deepEqual(calls[0][1], { timeout: 30000, maxRetries: 0 });
  const approved = flow.decide(input.id, { approved: true, actor: 'test-reviewer', sourceHash: reviewed.sourceHash, proposalHash: reviewed.proposalHash });
  assert.equal(approved.state, 'approved');
  assert.equal(calls.length, 1);
});
test('adapter byte limit fails the task without dispatch', async () => {
  let calls = 0;
  const flow = setup(async () => { calls++; return { output_text: 'ok' }; }, { maxSourceBytes: 1 });
  flow.submit(input);
  assert.equal((await flow.review(input.id, input)).state, 'failed');
  assert.equal(calls, 0);
});
test('shared adapter rate limit covers separate concurrent tasks', async () => {
  let finish;
  let calls = 0;
  const flow = setup(() => { calls++; return new Promise(resolve => { finish = resolve; }); }, { maxRequests: 1, now: () => 1000 });
  flow.submit(input);
  flow.submit({ ...input, id: 'two' });
  const first = flow.review(input.id, input);
  const second = await flow.review('two', input);
  assert.equal(second.state, 'failed');
  assert.equal(calls, 1);
  finish({ output_text: 'ok' });
  assert.equal((await first).state, 'awaiting_approval');
});
test('provider errors and empty output cannot produce approvable tasks', async () => {
  for (const create of [
    async () => { throw Object.assign(new Error('sensitive-provider-detail'), { status: 401 }); },
    async () => ({ output_text: ' ' }),
  ]) {
    const flow = setup(create);
    flow.submit(input);
    const result = await flow.review(input.id, input);
    assert.equal(result.state, 'failed');
    assert.equal(result.proposal, undefined);
    assert.equal(JSON.stringify(result).includes('sensitive-provider-detail'), false);
    assert.throws(() => flow.decide(input.id, { approved: true, actor: 'test-reviewer', sourceHash: result.sourceHash }));
  }
});

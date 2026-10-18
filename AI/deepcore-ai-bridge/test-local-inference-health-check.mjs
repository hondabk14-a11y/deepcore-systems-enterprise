import test from 'node:test';
import assert from 'node:assert/strict';
import { EXPECTED_HEALTH_RESPONSE, validateModels, validateCompletion } from './src/local-inference-contract.mjs';

const expectedModel = 'deepseek-ai/DeepSeek-V4-Flash';

test('accepts expected model advertisement', () => {
  assert.doesNotThrow(() => validateModels({ data: [{ id: expectedModel }] }, expectedModel));
});

test('rejects missing expected model', () => {
  assert.throws(() => validateModels({ data: [{ id: 'other-model' }] }, expectedModel), /expected model not advertised/);
});

test('rejects malformed model advertisement', () => {
  assert.throws(() => validateModels({ data: null }, expectedModel), /expected model not advertised/);
});

test('accepts exact chat completion sentinel', () => {
  assert.doesNotThrow(() => validateCompletion({ choices: [{ message: { content: EXPECTED_HEALTH_RESPONSE } }] }));
});

test('rejects malformed chat completion', () => {
  assert.throws(() => validateCompletion({ choices: [] }), /expected health-check response/);
});

test('rejects unrelated nonempty responses', () => {
  assert.throws(() => validateCompletion({ choices: [{ message: { content: 'any nonempty text' } }] }), /expected health-check response/);
});

test('rejects near matches, including injected prefixes and trailing text', () => {
  for (const content of [' ' + EXPECTED_HEALTH_RESPONSE, EXPECTED_HEALTH_RESPONSE + '\n', 'OK: ' + EXPECTED_HEALTH_RESPONSE, EXPECTED_HEALTH_RESPONSE + ' extra']) {
    assert.throws(() => validateCompletion({ choices: [{ message: { content } }] }), /expected health-check response/);
  }
});

import test from "node:test";
import assert from "node:assert/strict";

const expectedModel = "deepseek-ai/DeepSeek-V4-Flash";

function validateModels(body) {
  const ids = Array.isArray(body?.data) ? body.data.map((model) => model?.id) : [];
  if (!ids.includes(expectedModel)) throw new Error("expected model not advertised");
}

function validateCompletion(body) {
  const content = body?.choices?.[0]?.message?.content;
  if (typeof content !== "string" || content.length === 0) {
    throw new Error("missing completion content");
  }
}

test("accepts expected model advertisement", () => {
  assert.doesNotThrow(() => validateModels({ data: [{ id: expectedModel }] }));
});

test("rejects missing expected model", () => {
  assert.throws(() => validateModels({ data: [{ id: "other-model" }] }));
});

test("accepts a valid chat completion", () => {
  assert.doesNotThrow(() => validateCompletion({ choices: [{ message: { content: "DEEPCORE_LOCAL_AI_OK" } }] }));
});

test("rejects malformed chat completion", () => {
  assert.throws(() => validateCompletion({ choices: [] }));
});

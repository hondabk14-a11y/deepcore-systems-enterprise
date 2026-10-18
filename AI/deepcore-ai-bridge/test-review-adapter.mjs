import test from "node:test";
import assert from "node:assert/strict";
import { createReviewAdapter, ReviewError } from "./src/review-adapter.mjs";

const request = { fileName: "CORE/module.py", source: "print('safe')", instructions: "Read-only review." };
function adapterWith(create, extra = {}) {
  return createReviewAdapter({ client: { responses: { create } }, model: "test-model", ...extra });
}

test("creates bounded, non-persistent advisory Responses request", async () => {
  const calls = [];
  const adapter = adapterWith(async (...args) => {
    calls.push(args);
    return { output_text: "No findings." };
  });
  assert.equal(await adapter.review(request), "No findings.");
  assert.deepEqual(calls, [[{
    model: "test-model", instructions: "Read-only review.",
    input: "Review this file: CORE/module.py\n\n--- SOURCE ---\nprint('safe')\n--- END SOURCE ---",
    store: false,
  }, { timeout: 30_000, maxRetries: 0 }]]);
});

test("enforces UTF-8 byte-size limit before dispatch", async () => {
  let calls = 0;
  const adapter = adapterWith(async () => { calls++; return { output_text: "ok" }; }, { maxSourceBytes: 4 });
  await assert.rejects(adapter.review({ ...request, source: "😀😀" }), (error) => error.code === "INPUT_TOO_LARGE");
  assert.equal(calls, 0);
});

test("rejects missing inputs and invalid configuration", async () => {
  assert.throws(() => createReviewAdapter({ model: "test" }), (error) => error.code === "CONFIGURATION");
  const adapter = adapterWith(async () => ({ output_text: "ok" }));
  await assert.rejects(adapter.review({ ...request, instructions: "" }), (error) => error.code === "INVALID_INPUT");
  assert.throws(() => adapterWith(async () => ({}), { maxRequests: 0 }), (error) => error.code === "CONFIGURATION");
});

test("limits simultaneous calls and permits requests after the window", async () => {
  let clock = 1_000;
  let calls = 0;
  const adapter = adapterWith(async () => { calls++; return { output_text: "ok" }; },
    { maxRequests: 2, windowMs: 60_000, now: () => clock });
  const results = await Promise.allSettled([adapter.review(request), adapter.review(request), adapter.review(request)]);
  assert.deepEqual(results.map((r) => r.status), ["fulfilled", "fulfilled", "rejected"]);
  assert.equal(results[2].reason.code, "RATE_LIMIT");
  assert.equal(calls, 2);
  clock += 60_000;
  assert.equal(await adapter.review(request), "ok");
  assert.equal(calls, 3);
});

test("sanitizes provider failures and rejects empty responses", async () => {
  for (const [status, code] of [[401, "PROVIDER_AUTH"], [403, "PROVIDER_AUTH"], [429, "PROVIDER_RATE_LIMIT"], [500, "PROVIDER_UNAVAILABLE"]]) {
    const adapter = adapterWith(async () => { throw Object.assign(new Error("secret=do-not-print"), { status }); });
    await assert.rejects(adapter.review(request), (error) => error instanceof ReviewError && error.code === code && !error.message.includes("secret"));
  }
  const adapter = adapterWith(async () => ({ output_text: " " }));
  await assert.rejects(adapter.review(request), (error) => error.code === "INVALID_RESPONSE");
});

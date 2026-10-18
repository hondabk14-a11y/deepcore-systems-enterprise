import test from "node:test";
import assert from "node:assert/strict";
import { isLocalEndpoint } from "./src/local-endpoint.mjs";

test("accepts documented local inference URLs including /v1", () => {
  for (const url of ["http://127.0.0.1:8000/v1", "http://localhost:30000/v1", "http://[::1]:8000/v1"]) {
    assert.equal(isLocalEndpoint(url), true, url);
  }
});

test("does not treat remote services or lookalike hosts as local", () => {
  for (const url of [
    "https://openrouter.ai/api/v1",
    "https://localhost.evil.example/v1",
    "https://127.0.0.1.evil.example/v1",
    "not-a-url"
  ]) {
    assert.equal(isLocalEndpoint(url), false, url);
  }
});

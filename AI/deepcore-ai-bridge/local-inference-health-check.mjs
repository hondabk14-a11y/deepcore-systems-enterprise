#!/usr/bin/env node

import process from "node:process";
import { EXPECTED_HEALTH_RESPONSE, validateModels, validateCompletion } from "./src/local-inference-contract.mjs";

const baseURL = (process.env.DEEPCORE_AI_BASE_URL || "http://127.0.0.1:8000/v1").replace(/\/$/, "");
const expectedModel = process.env.DEEPCORE_AI_MODEL || "deepseek-ai/DeepSeek-V4-Flash";

async function readJSON(url, options = {}) {
  const response = await fetch(url, options);
  const text = await response.text();
  let body;
  try {
    body = JSON.parse(text);
  } catch {
    throw new Error(`non-JSON response from ${url}: HTTP ${response.status}`);
  }
  if (!response.ok) {
    throw new Error(`HTTP ${response.status} from ${url}: ${JSON.stringify(body)}`);
  }
  return body;
}

try {
  const models = await readJSON(`${baseURL}/models`);
  validateModels(models, expectedModel);

  const completion = await readJSON(`${baseURL}/chat/completions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: expectedModel,
      messages: [{ role: "user", content: `Return exactly: ${EXPECTED_HEALTH_RESPONSE}` }],
      max_tokens: 16,
      temperature: 0,
    }),
  });

  validateCompletion(completion);

  console.log(`LOCAL AI PREFLIGHT PASS model=${expectedModel} endpoint=${baseURL}`);
} catch (error) {
  console.error(`LOCAL AI PREFLIGHT FAIL: ${error.message}`);
  process.exitCode = 1;
}

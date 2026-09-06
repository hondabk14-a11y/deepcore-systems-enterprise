#!/usr/bin/env node

import process from "node:process";

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
  const ids = Array.isArray(models.data) ? models.data.map((model) => model?.id) : [];
  if (!ids.includes(expectedModel)) {
    throw new Error(`expected model not advertised: ${expectedModel}`);
  }

  const completion = await readJSON(`${baseURL}/chat/completions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: expectedModel,
      messages: [{ role: "user", content: "Return exactly: DEEPCORE_LOCAL_AI_OK" }],
      max_tokens: 16,
      temperature: 0,
    }),
  });

  const content = completion?.choices?.[0]?.message?.content;
  if (typeof content !== "string" || content.length === 0) {
    throw new Error("chat completion response has no non-empty choices[0].message.content");
  }

  console.log(`LOCAL AI PREFLIGHT PASS model=${expectedModel} endpoint=${baseURL}`);
} catch (error) {
  console.error(`LOCAL AI PREFLIGHT FAIL: ${error.message}`);
  process.exitCode = 1;
}

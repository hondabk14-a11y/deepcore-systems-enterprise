#!/usr/bin/env node

import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import dotenv from "dotenv";
import OpenAI from "openai";

dotenv.config({ path: path.resolve(process.cwd(), ".env") });

const target = process.argv[2];
if (!target) {
  console.error("Usage: npm run review -- <path-to-file>");
  process.exit(2);
}

const baseURL = process.env.DEEPCORE_AI_BASE_URL || "https://api.openai.com/v1";
const normalizedBaseURL = baseURL.replace(/\/$/, "");
const isLocal = /^(https?:\/\/)?(localhost|127\.0\.0\.1)(:\d+)?\/?$/i.test(baseURL);
const isOpenRouter = /(^|:\/\/)(www\.)?openrouter\.ai(\/|$)/i.test(baseURL);
const apiKey = isOpenRouter
  ? process.env.OPENROUTER_API_KEY
  : process.env.OPENAI_API_KEY || (isLocal ? "deepcore-local" : "");

if (!apiKey) {
  console.error(`${isOpenRouter ? "OPENROUTER_API_KEY" : "OPENAI_API_KEY"} is not set. Create a local .env from .env.example.`);
  process.exit(2);
}

const model = process.env.DEEPCORE_AI_MODEL || "gpt-6-astra";
const absoluteTarget = path.resolve(process.cwd(), target);
const source = await fs.readFile(absoluteTarget, "utf8");

const defaultHeaders = isOpenRouter
  ? {
      "HTTP-Referer": process.env.OPENROUTER_HTTP_REFERER || "https://github.com/hondabk14-a11y/deepcore-systems-enterprise",
      "X-Title": process.env.OPENROUTER_X_TITLE || "DeepCore Systems Enterprise AI Bridge",
    }
  : undefined;

const client = new OpenAI({
  apiKey,
  baseURL: normalizedBaseURL,
  defaultHeaders,
});

const instructions = `You are the DeepCore Systems Enterprise engineering reviewer.

Repository rules:
- Treat event history as authoritative and preserve deterministic replay.
- Fail closed on malformed, unauthorized, unverifiable, or invariant-violating input.
- Never weaken authentication, authorization, signature verification, certificate validation,
  replay protection, consensus safety, or ledger invariants.
- AI is advisory. It must not become ledger authority or key custody.
- Never request, expose, or invent secrets, private keys, wallet seeds, credentials, or API tokens.
- Do not claim production readiness without executable evidence.

Review the supplied source for correctness, security, determinism, failure handling, and tests.
Do not modify files. Return findings with severity, evidence, and concrete remediation steps.`;

const response = await client.responses.create({
  model,
  instructions,
  input: `Review this file: ${target}\n\n--- SOURCE ---\n${source}\n--- END SOURCE ---`,
});

console.log(response.output_text);

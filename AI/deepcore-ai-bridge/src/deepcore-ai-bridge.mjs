#!/usr/bin/env node

import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";
import dotenv from "dotenv";
import OpenAI from "openai";
import { isLocalEndpoint } from "./local-endpoint.mjs";
import { createReviewAdapter, ReviewError } from "./review-adapter.mjs";

dotenv.config({ path: path.resolve(process.cwd(), ".env") });

const target = process.argv[2];
if (!target) {
  console.error("Usage: npm run review -- <path-to-file>");
  process.exit(2);
}

const baseURL = (process.env.DEEPCORE_AI_BASE_URL || "https://api.openai.com/v1").replace(/\/+$/, "");
let endpoint;
try {
  endpoint = new URL(baseURL);
} catch {
  console.error("AI REVIEW FAIL [CONFIGURATION]: Invalid AI endpoint.");
  process.exit(2);
}
const isLocal = isLocalEndpoint(baseURL);
const isOpenRouter = endpoint.origin === "https://openrouter.ai" && endpoint.pathname.startsWith("/api/v1");
const isOfficial = endpoint.origin === "https://api.openai.com" && endpoint.pathname.startsWith("/v1");
if (!isLocal && !isOpenRouter && !isOfficial) {
  console.error("AI REVIEW FAIL [CONFIGURATION]: Unapproved AI endpoint. Use OpenAI, OpenRouter, or loopback inference.");
  process.exit(2);
}
const apiKey = isOpenRouter
  ? process.env.OPENROUTER_API_KEY
  : isLocal ? (process.env.DEEPCORE_LOCAL_AI_API_KEY || "deepcore-local") : process.env.OPENAI_API_KEY;
if (!apiKey) {
  console.error((isOpenRouter ? "OPENROUTER_API_KEY" : "OPENAI_API_KEY") + " is not configured in the server-side environment.");
  process.exit(2);
}

const model = process.env.DEEPCORE_AI_MODEL || "gpt-6-astra";
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
  timeout: 30_000,
  maxRetries: 0,
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

try {
  const repositoryRoot = await fs.realpath(path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../.."));
  const sourcePath = await fs.realpath(path.resolve(process.cwd(), target));
  const relative = path.relative(repositoryRoot, sourcePath).replaceAll(path.sep, "/");
  if (!relative || relative === ".." || relative.startsWith("../") || path.isAbsolute(relative)) {
    throw new ReviewError("FILE_POLICY", "Review target must be a repository file.");
  }
  const components = relative.split("/");
  if (components.some((component) => /^(secrets?|credentials?|wallets?|\.ssh)$/i.test(component)) ||
      /^(\.env(?:\.|$)|id_rsa$|id_ed25519$)/i.test(components.at(-1)) ||
      /\.(pem|key|p12|pfx|jks)$/i.test(relative)) {
    throw new ReviewError("FILE_POLICY", "Sensitive paths cannot be sent for AI review.");
  }
  const stat = await fs.stat(sourcePath);
  if (!stat.isFile() || stat.size > 128 * 1024) {
    throw new ReviewError("INPUT_TOO_LARGE", "Review target must be a regular file of at most 128 KiB.");
  }
  const source = await fs.readFile(sourcePath, "utf8");
  const adapter = createReviewAdapter({ client, model });
  console.log(await adapter.review({ fileName: relative, source, instructions }));
} catch (error) {
  const safeError = error instanceof ReviewError ? error : new ReviewError("REVIEW_FAILED", "Unable to load source or complete AI review.");
  console.error("AI REVIEW FAIL [" + safeError.code + "]: " + safeError.message);
  process.exitCode = 1;
}

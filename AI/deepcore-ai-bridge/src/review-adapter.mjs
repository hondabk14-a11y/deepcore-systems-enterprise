/** A bounded, advisory-only Responses API adapter. This is not an HTTP server. */
export class ReviewError extends Error {
  constructor(code, message) {
    super(message);
    this.name = "ReviewError";
    this.code = code;
  }
}

export function createReviewAdapter({
  client,
  model,
  now = () => Date.now(),
  maxRequests = 6,
  windowMs = 60_000,
  maxSourceBytes = 128 * 1024,
} = {}) {
  if (typeof client?.responses?.create !== "function" || typeof model !== "string" || !model.trim()) {
    throw new ReviewError("CONFIGURATION", "AI review client and model must be configured server-side.");
  }
  if (!Number.isSafeInteger(maxRequests) || maxRequests < 1 ||
      !Number.isSafeInteger(windowMs) || windowMs < 1 ||
      !Number.isSafeInteger(maxSourceBytes) || maxSourceBytes < 1 || typeof now !== "function") {
    throw new ReviewError("CONFIGURATION", "Invalid AI review limits.");
  }

  let issuedAt = [];
  return Object.freeze({
    async review({ fileName, source, instructions } = {}) {
      if (typeof fileName !== "string" || !fileName.trim() ||
          typeof source !== "string" || !source.trim() ||
          typeof instructions !== "string" || !instructions.trim()) {
        throw new ReviewError("INVALID_INPUT", "A source file and review instructions are required.");
      }
      if (Buffer.byteLength(source, "utf8") > maxSourceBytes) {
        throw new ReviewError("INPUT_TOO_LARGE", "Source exceeds the AI review size limit.");
      }

      const time = now();
      if (!Number.isFinite(time)) {
        throw new ReviewError("CONFIGURATION", "Invalid AI review clock.");
      }
      issuedAt = issuedAt.filter((timestamp) => time >= timestamp && time - timestamp < windowMs);
      if (issuedAt.length >= maxRequests) {
        throw new ReviewError("RATE_LIMIT", "AI review rate limit reached. Try again later.");
      }
      // Reserve the slot before awaiting so simultaneous requests share the same limit.
      issuedAt.push(time);

      try {
        const response = await client.responses.create({
          model,
          instructions,
          input: "Review this file: " + fileName + "\n\n--- SOURCE ---\n" + source + "\n--- END SOURCE ---",
          store: false,
        }, { timeout: 30_000, maxRetries: 0 });
        if (typeof response?.output_text !== "string" || !response.output_text.trim()) {
          throw new ReviewError("INVALID_RESPONSE", "AI provider returned no usable review.");
        }
        return response.output_text;
      } catch (error) {
        if (error instanceof ReviewError) throw error;
        // Never propagate provider messages: they may contain tokens or source text.
        if (error?.status === 401 || error?.status === 403) {
          throw new ReviewError("PROVIDER_AUTH", "AI provider authentication or access was rejected.");
        }
        if (error?.status === 429) {
          throw new ReviewError("PROVIDER_RATE_LIMIT", "AI provider rate limit reached.");
        }
        throw new ReviewError("PROVIDER_UNAVAILABLE", "AI provider request failed.");
      }
    },
  });
}

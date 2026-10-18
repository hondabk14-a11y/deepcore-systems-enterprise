/** Validate the minimal OpenAI-compatible local inference health contracts. */
export const EXPECTED_HEALTH_RESPONSE = 'DEEPCORE_LOCAL_AI_OK';

export function validateModels(body, expectedModel) {
  const ids = Array.isArray(body?.data) ? body.data.map((model) => model?.id) : [];
  if (!ids.includes(expectedModel)) {
    throw new Error(`expected model not advertised: ${expectedModel}`);
  }
}

export function validateCompletion(body) {
  const content = body?.choices?.[0]?.message?.content;
  if (content !== EXPECTED_HEALTH_RESPONSE) {
    throw new Error('chat completion did not return the expected health-check response');
  }
}

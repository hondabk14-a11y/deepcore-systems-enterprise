/** Return true only for an HTTP(S) loopback AI backend, including /v1 paths. */
export function isLocalEndpoint(baseURL) {
  try {
    const url = new URL(baseURL);
    return (url.protocol === 'http:' || url.protocol === 'https:') &&
      ['localhost', '127.0.0.1', '[::1]'].includes(url.hostname);
  } catch {
    return false;
  }
}

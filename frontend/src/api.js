const BASE = import.meta.env.VITE_API_URL || '';

export async function api(path, { token, ...options } = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 90000);
  try {
    const response = await fetch(`${BASE}/api${path}`, {
      ...options,
      signal: controller.signal,
      headers: { ...(token ? { 'X-Session-ID': token } : {}), ...options.headers },
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(
        typeof body.detail === 'string'
          ? body.detail
          : `Request failed (${response.status}). Check the backend terminal.`
      );
    }
    return response.headers.get('Content-Type')?.includes('application/pdf')
      ? response.blob()
      : response.json();
  } catch (e) {
    if (e.name === 'AbortError') throw new Error('The request timed out. Try again.');
    if (e instanceof TypeError) throw new Error('Cannot reach the backend. Check that the API is running and the API URL is correct.');
    throw e;
  } finally {
    clearTimeout(timer);
  }
}
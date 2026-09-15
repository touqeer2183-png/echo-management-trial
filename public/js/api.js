async function api(path, data) {
  const response = await fetch('/api/' + path, {
    method: data === undefined ? 'GET' : 'POST',
    headers: {'Content-Type': 'application/json'},
    body: data === undefined ? undefined : JSON.stringify(data)
  });
  const body = await response.json();
  if (!response.ok) {
    if (response.status === 401 && path !== 'login') window.dispatchEvent(new Event('session-expired'));
    const error = new Error(body.error || 'Request failed');
    error.status = response.status; throw error;
  }
  return body;
}

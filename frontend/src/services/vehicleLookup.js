/** Consulta exacta por un criterio; la vista controla cancelación y tiempo máximo. */
export async function lookupVehicle (apiBase, field, value, signal) {
  const query = new URLSearchParams({ field, value })
  const response = await fetch(`${apiBase}/vehicles/lookup/?${query}`, { credentials: 'include', signal })
  const data = await response.json().catch(() => null)
  return { status: response.status, data }
}

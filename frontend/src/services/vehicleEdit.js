/** PATCH del contrato VEH-EDIT: la vista decide timeout y mensajes, sin exponer ID/VIN editables. */
export async function editVehicle (apiBase, vehicleId, fields, csrfToken, signal) {
  const response = await fetch(`${apiBase}/vehicles/${vehicleId}/`, {
    method: 'PATCH', credentials: 'include', signal,
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
    body: JSON.stringify(fields)
  })
  const data = await response.json().catch(() => null)
  return { status: response.status, data }
}

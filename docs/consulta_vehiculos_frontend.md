# Proceso frontend: consulta de vehículos

Fecha: 2026-11-03. SPEC: VEH-CONSULTA-001. Responsabilidad: frontend. Estado: implementado; comprobación visual integrada pendiente del coordinador.

## Reglas aplicadas

Orquestador 1.3.0; frontend 1.2.0; seguridad 1.1.0; documentación frontend 1.0.0. Se conserva Vue Options API, JavaScript y CSS propios conforme a la excepción de compatibilidad de la guía frontend. No se instalaron dependencias ni se migró a Vuetify/TypeScript.

## Solicitud y proceso

Antes, consultar vehículos requería entrar al perfil de un cliente y abrir Vehículo(s) asociados. Ese recorrido permanece disponible.

Ahora ADMIN y RECEPCION disponen de Consultar vehículo en el menú lateral y en los accesos rápidos del panel. El usuario elige VIN, placa o ID, escribe el valor y envía la consulta. El resultado muestra la ficha del vehículo junto al cliente y taller asociados. Si la API responde 404, se presenta Vehículo no encontrado. El ID automático existente se muestra también en el detalle de vehículos asociados y en la confirmación de registro; nunca se solicita manualmente al crear el vehículo.

## Contrato acordado

GET /api/vehicles/lookup/?field=vin|plate|id&value=... con credentials: include. Búsqueda exacta; espacios exteriores retirados y VIN/placa convertidos a mayúsculas. La validación autoritativa corresponde al backend.

Respuesta 200: vehicle incluye id, plate, brand, model, vin, year, version, color, mileage, status y created_at; client contiene id/full_name y workshop contiene id/name. El frontend muestra kilometraje 0 como 0 km y null como No registrado.

- 401: limpiar sesión visual y volver al acceso.
- 403: mensaje de falta de permiso.
- 404: estado Vehículo no encontrado.
- 422: errores fields.field/fields.value junto a los controles y mensaje general.
- Red, timeout, respuesta inválida o error servidor: mensaje sencillo sin detalles técnicos.

## Pantalla y estados

El selector Buscar por tiene opciones VIN, Placa e ID del vehículo. El campo de búsqueda cambia su etiqueta y longitud máxima (17, 9 o 19 caracteres). Consultar vehículo se deshabilita mientras se consulta o si el valor está vacío. No existe una lista general automática: la pantalla inicial invita a introducir un criterio.

Hay estados inicial, carga, error, no encontrado y resultado. Al modificar criterio/valor o abandonar la pantalla se limpian resultados anteriores. Una generación de solicitud y la identidad del usuario impiden que respuestas tardías repueblen la ficha; AbortController cancela la petición y aplica un máximo de espera de 15 segundos. Al cambiar usuario o cerrar sesión también se invalida la consulta. No se guardan términos ni datos en localStorage/sessionStorage.

## Archivos y trazabilidad

- frontend/src/main.js: REQ-001, REQ-002, REQ-003, BR-001; acceso, formulario, estados, visualización de relaciones e ID, limpieza de ciclo de consulta.
- frontend/src/services/vehicleLookup.js: REQ-001; petición GET y respuesta conforme al contrato.
- frontend/src/style.css: REQ-002; disposición de formulario y ficha adaptable al ancho.

Se conservan el registro, los vehículos asociados y la eliminación previa del botón Administrar estatus. No se modifica el backend, el esquema ni los datos desde esta tarea frontend.

## Evidencia ejecutada

- docker compose exec -T frontend npm run build: correcto, Vite transformó 13 módulos y generó dist/.
- Compilación explícita de la cadena template de main.js con @vue/compiler-dom dentro del contenedor: correcta.

Estas comprobaciones acreditan compilación, no el recorrido HTTP real ni la aceptación completa. No se conectó a BD ni se crearon datos. Revisión visual de escritorio/móvil, respuesta real de API y pruebas de cada criterio quedan a cargo de la validación integrada del coordinador. No se declara lint: no hay script configurado.

## Seguridad y pendientes

La información se muestra con interpolación escapada; no hay HTML del usuario ni persistencia local. Los accesos visuales usan el permiso compartido; el servidor mantiene la autorización efectiva. No se muestran errores técnicos de red o del servidor. No se añadieron CR ni funcionalidades ajenas.

## Validación integrada del coordinador - 2026-11-03

- Django check: sin incidencias. makemigrations --check --dry-run: No changes detected.
- Suite workshop: 19 pruebas aprobadas (9 nuevas) en MySQL 8.4 desechable, red aislada, sin puertos ni volumen de la aplicación. Fuente montada en solo lectura; archivos de prueba bajo /tmp.
- Frontend: build Vite y compilación explícita de la plantilla Vue correctos. Revisión del formulario en escritorio y a 390 px de ancho.
- Navegador con sesión ADMIN: VIN, placa en minúsculas e ID de un registro existente devolvieron la misma ficha y los nombres de cliente y taller; ID inexistente mostró Vehículo no encontrado. Cambiar criterio limpió la ficha anterior. No se crearon ni editaron registros para estas consultas.
- Permisos ADMIN/RECEPCION, roles denegados y registros eliminados se verificaron con tests en MySQL aislado; el recorrido de navegador se ejecutó con ADMIN. No se afirma recorrido visual con ambos roles ni todas las dimensiones posibles.
- Imagen backend construida sobre la imagen local ya instalada, copiando el código actualizado; se canceló el build estándar por demora de descarga de la base. Dockerfile y dependencias del repositorio no se modificaron. Backend y frontend reiniciados; base principal preservada.
- Revisión independiente de seguridad: sin hallazgos SEC confirmados en el cambio revisado. No se realizó auditoría global ni check --deploy contra producción.
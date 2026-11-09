# Proceso frontend: edición de vehículos

Fecha: 2026-11-05. TASK-EDIT-FE. Estado: implementado y validado mediante pruebas aisladas, compilación y comprobación visual local.

## Reglas y alcance

Se aplicó orquestador-motora con las guías actuales del repositorio: orquestador 1.3.0, frontend 1.2.0, seguridad 1.1.0 y doc-frontend 1.0.0. Se conservan Options API, JavaScript, estilos actuales y contratos existentes; no se agregan dependencias ni se migra de stack.

REQ/AC01: abrir un formulario flotante desde Consultar vehículo o desde el detalle de Vehículo(s) asociados. REQ/AC02: ID y VIN son de solo lectura. REQ/AC03: mismos permisos operativos ADMIN/RECEPCION, sesión y CSRF. REQ/AC04: guardar sincroniza las fichas, cancelar antes del envío no modifica los objetos originales.

## Proceso anterior y nuevo

Antes se podía consultar la información del vehículo desde la búsqueda global o el perfil del cliente, pero esas fichas no ofrecían edición.

Ahora ambos detalles muestran Editar vehículo. El botón abre un modal con una copia de los campos editables; las modificaciones del formulario no se reflejan en las fichas hasta recibir confirmación 200 del servidor. Cancelar, Escape o cerrar antes del envío descartan esa copia.

El editor permite cambiar placa, marca, modelo, año, versión, color y kilometraje. ID y VIN aparecen identificados como solo lectura; no se envían ni se solicita cambiarlos. Cliente, taller y estatus permanecen fuera del formulario y del payload.

Al guardar, el resultado actualiza el registro coincidente en la consulta global, el detalle asociado, la lista de asociados y la lista de registro presentes en memoria. Se cierra el editor y se muestra Vehículo actualizado correctamente. No se refresca ni altera la relación del cliente o taller.

## Contrato API

PATCH /api/vehicles/{id}/ con credentials: include, Content-Type: application/json y X-CSRFToken de la cookie csrftoken.

El cuerpo incluye exclusivamente plate, brand, model, year, version, color y mileage. Placa se recorta y pasa a mayúsculas; las cadenas se recortan; año y kilometraje son numéricos, con kilometraje vacío convertido a null y cero conservado. La validación autoritativa sigue siendo del backend.

- 200: detail y vehicle actualizado, con campos de vehicle_data, client {id, full_name} y workshop {id, name}.
- 401: invalidar editor y volver al acceso.
- 403: mensaje de permiso insuficiente, incluido rechazo CSRF.
- 404: Vehículo no encontrado y orientación para volver a consultar.
- 409: conflicto de placa; conservar formulario para corregir.
- 422: fields por nombre de campo y mensaje general.
- Respuesta inválida, red o timeout: no afirmar que no se guardó; indicar volver a consultar antes de reintentar.

## Estados, accesibilidad y sesión

Se muestran errores junto a cada campo, error general y carga. Durante Guardando se deshabilitan campos, guardar, cancelar y cierre; el usuario no puede lanzar envíos duplicados. Si hay una pérdida de respuesta, la interfaz no puede garantizar que el servidor no persistió el PATCH, por eso solicita reconsultar.

El modal tiene role dialog, aria-modal, título accesible, captura de foco con Tab/Shift+Tab y cierre Escape antes de guardar. El foco vuelve al acceso que lo abrió. Si procede de asociados, la ventana anterior se oculta mientras se edita; nunca quedan dos overlays interactivos.

La edición usa AbortController con límite de 15 segundos e identificador de generación. Cambiar de usuario/rol, navegar a otra pantalla o desmontar invalida y aborta la solicitud para que respuestas tardías no actualicen una sesión distinta. El ID del registro y el usuario se comprueban antes de aplicar la respuesta. No se persisten datos en almacenamiento local.

## Archivos y evidencia

- frontend/src/main.js: formulario, accesos, estados, invalidación y sincronización; REQ/AC01 a 04.
- frontend/src/style.css: modal adaptable, campos de solo lectura y acciones; REQ/AC01,02.
- frontend/src/services/vehicleEdit.js: PATCH por sesión/CSRF; REQ/AC03.

Ejecutado: node --check sobre main.js y vehicleEdit.js, ambos correctos. Después de iniciar Docker, el coordinador ejecutó docker compose exec -T frontend npm run build: aprobado (Vite 8.3.0). También compiló la plantilla completa de main.js con @vue/compiler-dom: sin errores. La compilación por sí sola no constituye aceptación funcional.

Validación integrada: 29 pruebas Django aprobadas en MySQL 8.4 aislado, incluidas edición con ambos roles, ID/VIN protegidos, CSRF, validaciones e integridad. Cinco pruebas adicionales con Node vm ejecutaron los métodos reales de main.js y transporte simulado: payload cerrado con CSRF, respuesta 200 sincroniza las cuatro referencias/listas conservando cero, cancelación sin mutación/envío, conflicto 409 conserva datos y respuesta tardía tras cierre no se aplica. El script se conservó fuera del repositorio en Documents/Codex/2026-10-14/github-plugin-github-openai-curated-remote/work/test_vehicle_edit_frontend.mjs. No se cambió el esquema.

## Comprobación visual y límites

En localhost:5173, con la sesión ADMIN existente, se verificaron los dos accesos, datos precargados e ID/VIN de solo lectura. Se envió color vacío y la API devolvió validación 422; cancelar conservó el color original y devolvió el foco al botón. Desde asociados, Escape devolvió al detalle con foco en Editar vehículo. Shift+Tab desde el diálogo llevó al último control y Tab regresó al primero. Se revisó el modal a 390x844, con desplazamiento vertical; se restableció el tamaño de pantalla al terminar.

La revisión independiente de seguridad no confirmó hallazgos nuevos en este cambio. No se realizó guardado válido sobre datos existentes: el guardado persistente se validó en MySQL aislado y su sincronización visual mediante métodos reales con transporte simulado. RECEPCION fue validada por API sin privilegio superusuario, no mediante una segunda sesión visual. No se ejecutaron pruebas de carga, auditoría general de dependencias ni producción.

Captura local: Documents/Codex/2026-10-14/github-plugin-github-openai-curated-remote/outputs/edicion_vehiculo.png. No se registran secretos en esta documentación. No hay SEC abierto ni CR implementado en el alcance.

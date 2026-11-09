# Guía de ejecución de Motora

## Carga obligatoria

Antes de trabajar, leer [orquestador](spec/orquestador/orquestador.md) y aplicar la SPEC proporcional en el chat. Leer solo las guías pertinentes, registrar su versión y distinguir hechos, supuestos y pendientes:

- Backend/API/MySQL: [Skills](spec/skills/skills.md) + [Backend Django](spec/backend/backend-django.md). En detalles del framework prevalece Django; skills.md no se modifica.
- Frontend: [Frontend](spec/frontend/frontend.md). Mantener el stack existente en cambios locales; no migrar a TypeScript/Vuetify automáticamente.
- Seguridad y cambios sensibles: [Seguridad](spec/seguridad/seguridad.md).
- Documentación: [Backend](spec/documentacion/doc-backend.md) o [Frontend](spec/documentacion/doc-frontend.md).
- Convenciones del repositorio: [Guía de contribución](spec/AGENTS.md).

## Delegación

Solicitar subagentes según la sección 13 del orquestador: frontend y backend_django para trabajo cruzado con contrato previo; seguridad para revisión independiente de cambios sensibles; skills para contratos y conflictos de reglas. Los perfiles viven en .codex/agents/. Para tareas pequeñas no duplicar trabajo. Si la sesión no ofrece delegación o no carga perfiles, indicarlo y aplicar las responsabilidades directamente. No simular ejecuciones.

Definir TASK, REQ/AC, archivos permitidos y exclusiones en cada encargo. No editar simultáneamente los mismos archivos. El coordinador integra y verifica los resultados. Los especialistas no crean más agentes.

## Conservación y entrega

Preservar trabajo existente, sesiones/CSRF, permisos y contratos. ADMIN y RECEPCION tienen iguales funciones operativas. No mostrar secretos ni editar .env sin necesidad autorizada. No acceder a producción ni ejecutar migraciones destructivas sin autorización. Auditoría y diseño son de solo lectura del proyecto salvo entrega documental pedida.

Entregar evidencia real, límites, SEC/CR, tabla de fases y resumen ejecutivo. No presentar un build como prueba funcional completa.

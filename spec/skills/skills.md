---
name: spring-boot-rest-spec
description: Guía técnica para analizar, diseñar, implementar y validar servicios REST con Spring Boot mediante especificaciones verificables y alcance controlado.
version: 1.0.0
language: es
---

# Skill profesional — Spring Boot y servicios RESTful

## 1. Propósito y contrato de aplicación

Actúa como un ingeniero senior de Java y Spring Boot. Desarrolla software mantenible, seguro, observable y eficiente, aplicando Specification-Driven Development (SDD): especificar el comportamiento, diseñar la solución mínima suficiente, implementar y verificar contra criterios de aceptación.

Este documento contiene instrucciones técnicas reutilizables; `orquestador.md` gobierna su ejecución. Los nombres solicitados se conservan: el entorno de agentes debe cargar ambos archivos explícitamente. Su mera presencia no garantiza descubrimiento automático como skill instalada.

**DEBE** indica obligación; **DEBERÍA** indica recomendación con excepción justificada; **PUEDE** indica opción condicionada al alcance. No todos los patrones son obligatorios. La seguridad y la corrección necesarias para entregar lo solicitado sí lo son. No crear funcionalidades adicionales bajo el argumento de aplicar buenas prácticas.

### Activación

Aplicar al crear o modificar APIs, casos de uso, persistencia, pruebas, seguridad, documentación u optimizaciones de Spring Boot. Para una consulta conceptual, usar la guía sin generar código ni archivos no pedidos.

### Entradas mínimas

- Solicitud y resultado observable esperado.
- Repositorio y convenciones existentes, si están disponibles.
- Versiones reales de Java, Spring Boot, Spring Security y dependencias.
- Motor y versión de base de datos; contratos y consumidores afectados.
- Restricciones de seguridad, compatibilidad, carga y despliegue conocidas.

Si falta un dato, distinguir un supuesto reversible de una decisión bloqueante. Nunca inventar acceso al repositorio, reglas de negocio, resultados de pruebas o capacidad de rendimiento.

## 2. Protocolo SPEC y trazabilidad

SPEC se utiliza aquí como una convención operativa de SDD, no como un estándar oficial de Spring ni como una herramienta específica.

| Elemento | Contenido verificable |
| --- | --- |
| S — Solicitud y alcance | Problema, actores, comportamiento solicitado, exclusiones y restricciones |
| P — Precisión del contrato | Requisitos, entradas/salidas, reglas, errores, permisos y criterios de aceptación |
| E — Ejecución diseñada | Decisiones técnicas, componentes afectados, tareas, dependencias y riesgos |
| C — Comprobación | Pruebas, evidencia, diferencias contra la especificación y estado final |

Toda modificación DEBE tener una justificación rastreable: `REQ → AC → TASK → cambio → TEST/evidencia`. Los identificadores son locales a la funcionalidad, por ejemplo `ORD-REQ-001`. Un hallazgo ajeno al alcance se registra como propuesta; no se implementa automáticamente.

### Plantilla mínima de especificación

```markdown
# SPEC: <identificador y título>
Estado: borrador | lista para ejecutar | en ejecución | validada | bloqueada
Solicitud de origen: <resumen fiel>
Objetivo observable: <resultado>
Incluido: <lista cerrada>
Excluido: <lista explícita>
Restricciones: <compatibilidad, seguridad, datos y entorno>
Supuestos: <ID, fundamento, efecto y modo de validación>
REQ-001: <comportamiento verificable>
BR-001: <regla de negocio confirmada>
AC-001: Dado <contexto>, cuando <acción>, entonces <resultado observable>.
Contrato: <HTTP, DTO, validaciones, errores y permisos>
Datos: <modelo, integridad, transacciones y consultas>
NFR-001: <métrica, objetivo acordado y condiciones de medición>
Diseño: <componentes y decisiones proporcionales>
TASK-001 → REQ-001 / AC-001: <cambio concreto>
TEST-001 → AC-001: <caso y evidencia esperada>
Riesgos y pendientes: <impacto y tratamiento>
Definition of Done: <condiciones aplicables de cierre>
```

Para un cambio pequeño, esta especificación puede estar en la respuesta o descripción del cambio. Para una funcionalidad extensa, usar el directorio de especificaciones del proyecto. No generar documentación duplicada ni imponer nuevos archivos sin necesidad.

## 3. Base tecnológica y dependencias

1. Inspeccionar `pom.xml` o `build.gradle`, wrapper, toolchain, perfiles y CI antes de decidir versiones.
2. Conservar versiones compatibles y soportadas por el proyecto. En proyectos nuevos, verificar la matriz oficial Java/Spring Boot y seleccionar versiones estables soportadas. No usar snapshots ni actualizar una versión mayor sin alcance autorizado.
3. Utilizar el BOM o gestión de dependencias de Spring Boot; justificar cualquier override y comprobar compatibilidad. No mezclar APIs `javax.*` y `jakarta.*` indiscriminadamente.
4. Preferir Maven Wrapper o Gradle Wrapper existente; mantener builds reproducibles y versiones explícitas donde no exista gestión central.
5. Añadir únicamente dependencias necesarias para un requisito. Verificar mantenimiento, licencia y vulnerabilidades conforme a los controles del proyecto.
6. Inyección por constructor; configuración externa con `@ConfigurationProperties` y validación. No incrustar secretos ni usar perfiles como sustituto de controles de acceso.

## 4. Arquitectura proporcional al problema

- Preferir organización por capacidad de negocio, con responsabilidades internas claras. Respetar una arquitectura existente coherente.
- Separar transporte HTTP, coordinación del caso de uso, reglas de negocio y acceso a infraestructura. Los controladores no contienen lógica de negocio ni consultas.
- Aplicar SOLID, cohesión alta, acoplamiento bajo y composición. Evitar abstracciones sin una variación real que resolver.
- En arquitectura hexagonal o Clean Architecture, las dependencias apuntan hacia el dominio; los adaptadores implementan puertos definidos por las necesidades internas.
- Un dominio rico independiente de JPA resulta útil con reglas complejas; un CRUD sencillo puede usar un modelo más directo. Documentar la decisión sin imponer duplicación de modelos.
- No introducir microservicios, CQRS con almacenes separados, event sourcing, service discovery, gateway o mensajería por defecto. Requieren necesidades concretas y alcance autorizado.
- Mantener límites transaccionales en los casos de uso. Evitar llamadas remotas dentro de transacciones prolongadas.
- No introducir repositorios genéricos o capas que únicamente repitan la API de Spring Data sin aportar una responsabilidad.

Organización orientativa, adaptable al repositorio:

```text
com.organizacion.aplicacion.<capacidad>.api
com.organizacion.aplicacion.<capacidad>.application
com.organizacion.aplicacion.<capacidad>.domain
com.organizacion.aplicacion.<capacidad>.infrastructure
```

Registrar decisiones significativas como ADR: contexto, alternativas viables, decisión, consecuencias y condiciones de revisión. No crear un ADR para cada clase.

## 5. Diseño de contratos REST

### Recursos y semántica HTTP

- Usar nombres de recursos consistentes y URI estables. Conservar el idioma y versionado del proyecto.
- GET debe ser seguro; PUT representa sustitución según contrato; PATCH una modificación parcial definida; DELETE y PUT tienen semántica idempotente. POST no lo es automáticamente.
- Para creación síncrona, considerar `201 Created` con `Location`; `202 Accepted` solo para trabajo realmente aceptado y pendiente, con mecanismo de seguimiento especificado. `204` no incluye cuerpo.
- Diferenciar `400` sintaxis/validación según contrato, `401` autenticación ausente o inválida, `403` permiso insuficiente, `404` recurso no visible o inexistente conforme a política, `409` conflicto de estado y `412` precondición incumplida. `422` solo con una convención acordada.
- No responder HTTP 200 a todos los errores ni filtrar detalles internos mediante mensajes.

### DTO, validación y compatibilidad

- Usar DTO de entrada/salida; no exponer entidades persistentes, relaciones lazy ni campos internos.
- Aplicar Jakarta Bean Validation en el borde HTTP y reglas de negocio en el dominio/caso de uso. Los constraints de base de datos son la defensa final de integridad.
- Distinguir campo omitido y `null` en PATCH. Definir formatos de fecha, zona horaria, moneda, escala decimal, longitud y nulabilidad.
- Usar `BigDecimal` para importes y política explícita de redondeo. Elegir tipos temporales según significado: instante UTC, fecha local o fecha con zona.
- Limitar tamaño de cuerpo, rangos de fechas, cantidad de resultados y campos admitidos. Evitar mass assignment mediante DTO y mapeo explícito.
- Documentar cambios incompatibles; no alterar contratos públicos silenciosamente. No añadir una versión de API si el proyecto no la necesita.

### Colecciones e idempotencia

- Paginar listados potencialmente grandes, limitar el tamaño máximo y permitir solo campos de ordenamiento conocidos.
- Usar orden estable con desempate único. Considerar cursor/keyset para páginas profundas; definir semántica ante cambios concurrentes.
- Para POST con riesgo de duplicación y requisito de reintento, especificar clave de idempotencia: alcance por cliente/tenant, huella de solicitud, expiración, persistencia atómica, concurrencia y respuesta repetida. Una clave en memoria no resuelve múltiples instancias.
- Si se requieren actualizaciones condicionales, diseñar ETag/If-Match o control de versión y probar conflictos.

### Errores uniformes

Usar `ProblemDetail` conforme a RFC 9457 cuando la versión lo soporte, o una representación compatible. Centralizar errores MVC con `@RestControllerAdvice`; los errores de la cadena de seguridad necesitan también sus handlers correspondientes. Incluir código de negocio estable, detalle público y correlación; excluir stack traces, SQL y secretos. Las extensiones para errores de campos deben estar documentadas y no devolver valores sensibles rechazados.

## 6. Seguridad desde el diseño

1. Definir activos, actores, fronteras de confianza y amenazas del cambio antes de implementar.
2. Configurar Spring Security con APIs compatibles con la versión del proyecto; en configuraciones modernas, usar beans `SecurityFilterChain`. Evitar ejemplos obsoletos sin verificar.
3. Denegar por defecto y declarar explícitamente recursos públicos. Separar autenticación de autorización.
4. Verificar autorización por operación y por objeto. Un rol o token válido no autoriza por sí solo acceso a cualquier ID. Aplicar aislamiento de tenant en consultas, escrituras y claves de caché.
5. Para OAuth2/OIDC, reutilizar el proveedor de identidad y capacidades de Resource Server cuando corresponda. No desarrollar un emisor JWT propio para una tarea que solo requiere validar tokens.
6. En JWT, verificar firma, algoritmos permitidos, emisor, audiencia y vigencia; considerar rotación de claves y tolerancia temporal limitada. Nunca confiar solo en decodificar el payload.
7. Elegir sesión/cookies o bearer según clientes y amenazas. Si el navegador adjunta credenciales automáticamente, evaluar y mantener protección CSRF. Ser stateless no elimina por sí solo CSRF; desactivarla requiere una justificación sobre el mecanismo real de autenticación.
8. Configurar CORS con orígenes, métodos y encabezados mínimos. CORS no reemplaza autenticación; evitar comodines con credenciales.
9. Si el sistema gestiona contraseñas, usar `PasswordEncoder` con algoritmos adaptativos y coste calibrado; nunca texto plano ni hashes rápidos. No crear gestión de contraseñas si ya la resuelve el IdP.
10. Usar TLS; cookies Secure/HttpOnly/SameSite según flujo; validar redirecciones y destinos salientes para reducir SSRF. No desactivar validación de certificados.
11. Parametrizar consultas; sanitizar únicamente donde corresponda al contexto; no construir SQL o nombres de columnas desde entrada libre.
12. Mantener secretos fuera de Git, logs, ejemplos y respuestas; acceder mediante el mecanismo de secretos del entorno y aplicar privilegio mínimo a la cuenta de BD.
13. Proteger Actuator, documentación y endpoints administrativos según exposición acordada. No publicar `env`, heap dumps u otros datos sensibles.
14. Para endpoints expuestos o costosos, definir límites de consumo y rate limiting proporcional al riesgo. Aclarar si el límite es local o distribuido y cómo responde con `429`.
15. Registrar eventos de seguridad necesarios sin credenciales ni datos personales innecesarios; definir retención conforme al proyecto.

Pruebas mínimas cuando aplique: anónimo, token inválido/expirado, rol insuficiente, acceso a objeto ajeno, acceso cruzado entre tenants y entrada maliciosa. No reducir controles para hacer pasar una prueba.

## 7. Persistencia, transacciones y consultas complejas

### Integridad y modelo

- Definir PK, FK, unicidad, nulabilidad y checks según invariantes confirmadas. Una comprobación previa en Java no evita carreras de inserción: respaldar unicidad en BD y mapear la excepción.
- Diseñar índices según filtros, joins, ordenamiento, selectividad y distribución real. Medir también coste de escritura y almacenamiento; no indexar cada columna.
- Usar migraciones versionadas con Flyway o Liquibase según proyecto. No usar `ddl-auto=update/create` como estrategia de producción.
- Para cambios incompatibles con versiones anteriores, plantear expand/contract, backfill y retirada posterior. No ejecutar migraciones destructivas sobre datos reales sin autorización.

### Transacciones y concurrencia

- Mantener transacciones cortas y explícitas. `readOnly=true` comunica intención/permite optimizaciones; no garantiza universalmente que una escritura sea imposible.
- Considerar proxies de `@Transactional`: una auto-invocación puede evitar la interceptación en modo proxy. Verificar comportamiento real en pruebas.
- La política tradicional revierte excepciones no comprobadas y `Error`; verificar configuración/versión y declarar rollback para excepciones comprobadas cuando el caso lo requiera.
- Usar `@Version` para conflictos optimistas cuando corresponda; bloqueo pesimista solo con justificación de contención y duración. Definir aislamiento por anomalía que se necesita evitar.
- Capturar y traducir conflictos sin ocultarlos. Reintentar deadlocks o conflictos solo con límites y cuando repetir la operación sea seguro.
- Las transacciones locales no garantizan atomicidad con servicios remotos. Si el alcance exige publicación fiable, evaluar outbox y consumidores idempotentes; no prometer exactly-once de extremo a extremo.

### Selección de estrategia de consulta

| Necesidad | Alternativa a evaluar | Evidencia necesaria |
| --- | --- | --- |
| Consulta sencilla | Método derivado o JPQL legible | Resultado y SQL generado |
| Filtros opcionales combinables | Specifications/Criteria o solución ya adoptada | Predicados correctos y parámetros seguros |
| Lectura parcial | Proyección DTO/interfaz apropiada | Columnas y joins realmente ejecutados |
| Relaciones necesarias | Fetch plan, `@EntityGraph` o fetch join | Conteo de consultas y ausencia de N+1 |
| Agregaciones, CTE, ventanas | SQL nativo, JDBC o jOOQ si está autorizado | Plan, portabilidad y mapeo probado |
| Recorrido extenso | Cursor/keyset, lotes o streaming controlado | Memoria, orden, cierre de recursos y tiempo |

Protocolo obligatorio para optimizar una consulta:

1. Especificar resultado, cardinalidad, filtros, permisos, orden y tamaño máximo.
2. Obtener SQL y parámetros representativos sin divulgar datos sensibles.
3. Medir en un entorno seguro con volumen y distribución relevantes.
4. Inspeccionar el plan con herramientas del motor. `EXPLAIN ANALYZE` ejecuta la consulta: usarlo solo en un entorno seguro y controlar efectos/coste.
5. Comprobar índices, estimaciones, scans, joins, sorts, bloqueos y acceso a disco.
6. Corregir el cuello de botella y comparar antes/después conservando resultados.
7. Añadir pruebas de regresión relevantes y documentar límites.

Evitar N+1, cargas completas para filtrar en Java, `SELECT *` innecesario y colecciones sin límite. No paginar ingenuamente un fetch join de colección: puede producir duplicados o paginación en memoria; evaluar consulta de IDs paginados seguida de carga por lote conservando el orden. Evaluar el coste de `COUNT`; usar `Slice` cuando no se requiere total. Desactivar Open Session in View cuando se adopte carga explícita en la capa de aplicación, verificando antes que el cambio no rompa consumidores. Para operaciones bulk, considerar la desincronización del contexto de persistencia y los callbacks omitidos.

## 8. Rendimiento, resiliencia y operación

- No prometer alta concurrencia por usar Spring Boot, WebFlux o virtual threads. Establecer objetivos y demostrar resultados medidos.
- Definir carga, concurrencia, tamaño de datos, mezcla lectura/escritura, throughput, p95/p99, tasa de errores y consumo de CPU/memoria. Si faltan objetivos, registrarlos como pendientes, no inventar cumplimiento.
- Elegir Spring MVC o WebFlux según arquitectura y dependencias. Evitar llamadas JDBC/JPA bloqueantes en event loops. Virtual threads no aumentan la capacidad del motor de BD ni sustituyen límites de concurrencia.
- Dimensionar pools HTTP, ejecutores y conexiones con medición. Considerar conexiones por instancia × réplicas y reservas operativas del motor.
- Establecer timeouts de conexión, respuesta y consulta; usar límites de cola y backpressure cuando corresponda.
- Reintentos con límite, backoff y jitter únicamente para errores transitorios y operaciones seguras. Evitar reintentos multiplicados en varias capas. Circuit breaker y bulkhead se incorporan solo donde el fallo remoto lo justifique.
- Introducir caché después de medir y definir consistencia, TTL, invalidación, aislamiento por usuario/tenant y comportamiento ante fallos. Evitar cachear errores o datos sensibles indiscriminadamente.
- En procesos asíncronos, definir cancelación, estado, idempotencia y recuperación. No usar `@Async` como garantía de entrega durable.
- Aplicar Micrometer/Actuator y trazas según infraestructura existente. Medir latencia, errores, tráfico y saturación. Limitar cardinalidad de etiquetas; no etiquetar métricas con IDs arbitrarios.
- Logs estructurados con correlación; propagar contexto al cruzar hilos cuando corresponda. No registrar cuerpos completos ni tokens por defecto.
- Diferenciar liveness de readiness. No vincular liveness indiscriminadamente a servicios externos y provocar reinicios en cascada. Configurar apagado ordenado si el despliegue lo requiere.
- Contenedores y CI solo si están en alcance: usuario no root, imagen mantenida, recursos limitados, configuración externa y validaciones reproducibles.

## 9. Código y documentación mantenibles

- Nombres del dominio, métodos pequeños con responsabilidad clara, inmutabilidad donde sea útil y errores específicos.
- No usar `Optional` como sustituto indiscriminado de campos/DTO; no devolver `null` ambiguo ni capturar `Exception` para silenciar fallos.
- Evitar `@Data` indiscriminado en entidades JPA por asociaciones, `equals/hashCode` y `toString`. Definir identidad de entidades y exclusión de campos sensibles.
- JavaDoc para contratos públicos relevantes, invariantes, concurrencia, efectos y excepciones; comentarios para explicar decisiones, no repetir cada instrucción.
- Mantener OpenAPI sincronizado con rutas, DTO, validaciones, permisos, paginación, errores y ejemplos ficticios. Verificar compatibilidad de la biblioteca OpenAPI con la versión de Spring Boot.
- README operativo con versiones, arranque, configuración sin secretos, migraciones, pruebas y limitaciones. Actualizar solo secciones afectadas.
- Documentar decisiones, cambios de contrato, NFR y evidencia. No afirmar que documentación generada equivale a contrato validado.

## 10. Estrategia de validación

| Nivel | Qué verificar | Herramientas posibles según proyecto |
| --- | --- | --- |
| Unitario | Reglas y casos de uso con límites y errores | JUnit, Mockito si aporta aislamiento |
| Web | Contrato HTTP, validación y errores | MockMvc / WebTestClient según stack |
| Seguridad | Autenticación, permisos y objetos/tenants | Spring Security Test e integración |
| Persistencia | SQL real, constraints, paginación y concurrencia | Testcontainers con motor compatible |
| Integración | Flujo entre componentes y migraciones | `@SpringBootTest` cuando sea necesario |
| Contrato | Compatibilidad con consumidores | Validación OpenAPI o mecanismo existente |
| Rendimiento | Objetivos bajo carga representativa | Herramienta existente o autorizada |

No sustituir el motor de producción por H2 para validar SQL específico. Evitar mocks que solo reproduzcan la implementación. Elegir pruebas proporcionadas al riesgo; no exigir pruebas de carga para una corrección de texto. Ejecutar comandos reales del repositorio y guardar comando, resultado y limitación. Una prueba no ejecutada se reporta como pendiente, nunca aprobada.

## 11. Definition of Done y entrega

- [ ] Todos los requisitos incluidos tienen criterios de aceptación y evidencia.
- [ ] El diff contiene únicamente cambios solicitados o técnicamente indispensables y justificados.
- [ ] Build y pruebas aplicables pasan; cualquier bloqueo se declara explícitamente.
- [ ] Contratos, errores y autorización están validados para los flujos afectados.
- [ ] Consultas y migraciones se verificaron contra el motor aplicable, si cambiaron.
- [ ] Documentación afectada está actualizada; no hay secretos incorporados.
- [ ] Objetivos de rendimiento reclamados tienen medición reproducible.
- [ ] Se entrega tabla de fases y resumen ejecutivo conforme a `orquestador.md`.

No declarar el conjunto terminado si existen criterios obligatorios fallidos o sin verificar. Marcar controles no aplicables con una justificación.

## 12. Fuentes técnicas oficiales

Referencias consultadas el 11 de octubre de 2026. Los enlaces pueden mostrar una versión distinta a la del proyecto: seleccionar la documentación de su versión antes de copiar APIs o configuración. Estas referencias respaldan capacidades del framework; las reglas SPEC y de alcance son convenciones de estos documentos.

- Spring Security, autenticación: https://docs.spring.io/spring-security/reference/servlet/authentication/architecture.html
- Spring Security, CSRF: https://docs.spring.io/spring-security/reference/servlet/exploits/csrf.html
- Spring Framework, respuestas de error y ProblemDetail: https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-ann-rest-exceptions.html
- Spring Data JPA, proyecciones: https://docs.spring.io/spring-data/jpa/reference/repositories/projections.html
- Spring Data JPA, métodos de consulta y EntityGraph: https://docs.spring.io/spring-data/jpa/reference/jpa/query-methods.html
- Spring Boot, funciones de producción: https://docs.spring.io/spring-boot/reference/actuator/index.html
- Spring Boot, observabilidad: https://docs.spring.io/spring-boot/reference/actuator/observability.html
- Spring Boot, métricas: https://docs.spring.io/spring-boot/reference/actuator/metrics.html

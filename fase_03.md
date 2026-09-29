# Fase 03 — acceso autorizado y presentación visual

## Objetivo de la fase

Garantizar que Administrador y Recepcionista puedan encontrar y usar el módulo de clientes en cualquier tamaño de ventana, y mejorar la presentación de la aplicación sin alterar reglas de negocio, endpoints ni estructura de datos.

## Cambios realizados

| Área | Cambio realizado | Estado |
| --- | --- | --- |
| Menú por rol | Se corrigió la regla responsiva que ocultaba los enlaces `Registrar cliente` y `Consultar clientes` en ventanas menores a 900 px. | Completo |
| Acceso autorizado | Se verificó que `administrador` tiene rol `ADMIN` y `recepcionista` tiene rol `RECEPCION`; ambos ven el menú y el formulario de registro. | Completo |
| Formulario | Se comprobó desde Vue que Recepcionista abre el formulario con nombre, contacto, edad, fecha, teléfonos, correos, fotografía y dirección. | Completo |
| Sesiones y permisos | La API mantiene 401 sin sesión y 403 para roles sin privilegio. La regla se conserva en `roles_required`. | Completo |
| Fotos | Se corrigió la ruta de entrega de `/media/` para que las fotografías de clientes se puedan mostrar con `DJANGO_DEBUG=False`. | Completo |
| Estética | Se renovó `frontend/src/style.css`: login, navegación, botones, formularios, tarjetas, detalle de cliente y diseño adaptable. | Completo |
| Integridad de clientes | Se conservan Facade, Repository REST, validaciones e índices únicos implementados en la fase anterior. | Completo |

## Archivos modificados en esta fase

| Archivo | Responsabilidad del cambio |
| --- | --- |
| `frontend/src/style.css` | Sustituye los estilos por una interfaz más consistente: jerarquía tipográfica, márgenes, contrastes, estados de foco, tarjetas y adaptación móvil. Mantiene visibles las opciones autorizadas del menú. |
| `backend/config/urls.py` | Agrega la ruta de entrega de archivos en `/media/` para las fotografías registradas. |
| `docs/diagrama_componentes.html` | Añade un diagrama HTML del recorrido Vue → API → Facade → Repository → MySQL. |

## Verificaciones ejecutadas

| Verificación | Resultado |
| --- | --- |
| Compilación Vue con `npm run build` | Correcta. |
| Pruebas Django con `python manage.py test workshop` | 5 pruebas correctas. |
| Inicio de sesión de Administrador | Correcto; rol `ADMIN` reconocido por la API. |
| Inicio de sesión de Recepcionista | Correcto; rol `RECEPCION` reconocido por la API. |
| Menú de Recepcionista en ventana reducida | Correcto; aparecen Registrar cliente y Consultar clientes. |
| Apertura del formulario desde el menú | Correcta; el formulario completo se muestra para el rol autorizado. |

## Pendientes

| Pendiente | Motivo |
| --- | --- |
| Recuperación de contraseña y bloqueo por intentos | Requiere definir política de seguridad y flujo de correo. |
| Gestión completa de órdenes de trabajo | El proyecto conserva la consulta inicial; falta alta, asignación, estados, costos y piezas. |
| Vehículos asociados al cliente | Requiere una fase específica para diseñar la relación cliente–vehículo. |
| Publicación en producción | Requiere configurar secretos finales, HTTPS, almacenamiento persistente de media, backups y dominio. |
| Auditoría de acciones | Falta registrar quién crea o modifica clientes y cuándo. |

## Estado de cierre

La aplicación permite que los dos roles autorizados localicen y utilicen el registro de clientes desde la interfaz mejorada. No se modificaron los contratos REST, el modelo de datos ni las validaciones funcionales existentes.

---
name: vue-frontend
description: Guía técnica para analizar, diseñar, implementar y validar el desarrollo de Apis, Validaciones, Formularios, transiciones con Vue en la version 3.x mediante especificaciones verificables y alcance controlado.
version: 1.2.0
language: es
---

## 1. Role

Actúa como un desarrollador frontend senior especializado en Vue 3 y TypeScript.

Tu responsabilidad es desarrollar aplicaciones web modernas, seguras, escalables y mantenibles.

## 2. Core Skills

### Vue 3
- Dominar Vue 3.
- Utilizar Composition API.
- Utilizar script setup.
- Crear componentes reutilizables.
- Aplicar correctamente el ciclo de vida.
- Cargar los datos iniciales en onMounted y limpiar los temporizadores en onUnmounted.

### TypeScript
- Utilizar TypeScript.
- Definir interfaces y tipos.
- Evitar el uso innecesario de any.
- Implementar código fuertemente tipado.
- Activar el modo strict en tsconfig.

### Component Architecture
- Aplicar separación de responsabilidades.
- Crear componentes pequeños y reutilizables.
- Separar la lógica de negocio de la presentación.
- Utilizar composables para lógica compartida.
- Dividir un componente cuando pase de unas 250 líneas.
- No usar stores ni servicios dentro de los componentes reutilizables, solo props y eventos.
- Declarar las props en camelCase y usarlas en kebab-case en la plantilla.
- Definir los valores permitidos de una prop con tipos de unión.

### Reactivity
- Utilizar ref y reactive.
- Utilizar computed para valores derivados.
- Utilizar watch cuando sea necesario.
- Evitar estados duplicados.
- Usar ref por defecto y reactive solo para formularios.
- No declarar el estado fuera del componente, porque se comparte entre todas las instancias. Para estado compartido usar Pinia.
- Usar watch con immediate en lugar de llamar la misma función en onMounted y en watch.

### Forms and Validation
- Utilizar v-form de Vuetify.
- Crear reglas de validación reutilizables en utils/validators.ts.
- Validar al salir del campo y al enviar el formulario.
- Mostrar los mensajes de error en español y junto al campo.
- Pedir contraseñas de mínimo 8 caracteres, con al menos una letra y un número.
- Deshabilitar el botón y mostrar loading mientras se envía el formulario.
- Usar el autocomplete correcto en los campos de correo y contraseña.

### API Consumption
- Centralizar las llamadas en la carpeta services. Los componentes no llaman a fetch directamente.
- Utilizar Fetch API con un tiempo máximo de espera.
- Usar /api como base de la API, tomada de una variable de entorno.
- Enviar todas las peticiones con credentials: "include" para que viaje la cookie de sesión.
- Enviar el token de la cookie csrftoken en el encabezado X-CSRFToken en POST, PUT, PATCH y DELETE.
- Pedir la cookie csrftoken al backend al iniciar la aplicación, con el endpoint que la establece.
- Enviar las fotografías con FormData (multipart) y no fijar el Content-Type a mano.
- Manejar los estados de cargando, vacío, error y éxito en cada pantalla.
- Manejar los códigos de estado: 401 limpia la sesión y manda al login, 403 muestra un mensaje de falta de permiso, 409 muestra el conflicto y 422 muestra los errores junto a cada campo.
- Mostrar mensajes de error sencillos al usuario, sin detalles técnicos.
- Usar datos simulados solo para lo que el backend todavía no ofrece y marcarlos con TODO.
- No inventar endpoints ni campos. Usar los que estén documentados en el contrato con el backend.

### Transitions
- Utilizar Transition y TransitionGroup, o las transiciones de Vuetify.
- Mantener las animaciones cortas, entre 150 y 300 ms.
- Animar solo opacity y transform.
- Respetar prefers-reduced-motion.

## 3. Development Rules

- Utilizar Vue 3 con Composition API.
- Preferir script setup con TypeScript.
- Aplicar principios SOLID cuando correspondan.
- No ampliar el alcance ni migrar el stack sin autorización explícita.
- Registrar como CR las mejoras ajenas a la solicitud.

## 4. Compatibilidad con Motora existente

El frontend actual utiliza JavaScript, Options API, HTML/CSS propios, Vite y npm. Las reglas de Composition API, TypeScript y Vuetify son el objetivo de referencia; no autorizan por sí solas una migración en una corrección localizada. Mantener contratos y convenciones existentes en cambios pequeños y registrar la diferencia. Toda migración requiere SPEC y autorización separadas; no introducir dependencias nuevas por iniciativa del agente.

No reducir controles de seguridad para conservar compatibilidad. La API actual se consume con sesión y CSRF; nunca inventar campos, rutas o respuestas. Mantener iguales accesos operativos para ADMIN y RECEPCION.

## 5. Estructura y nombres

Respetar src/main.js y src/style.css mientras no se autorice reorganización. Al crear componentes dentro de una estructura ya autorizada: PascalCase y dos palabras para componentes, sufijo View para vistas, prefijo use para composables y eventos kebab-case. Extraer código repetido solo dentro del alcance; no separar todo main.js como requisito de una corrección visual.

Una arquitectura modular futura puede separar components, layouts, modules, services, composables, router, types y styles. Es una referencia, no una obligación de crear directorios vacíos ni de adoptar Pinia sin estado compartido que lo justifique.

## 6. Presentación y accesibilidad

Conservar la paleta y estilos actuales en cambios localizados; no cambiar el tema completo sin solicitud. La referencia visual histórica oscura (fondo #000000, superficies #1E1E1E, texto #FFFFFF/#B0B0B0, error #CF6679 y éxito #4CAF50) requiere confirmación antes de reemplazar el tema claro actual. No declarar que existe tema Vuetify si no está instalado.

Usar claves estables en v-for, evitar mezclar v-if y v-for en un elemento, etiquetas de campos y botones accesibles. No indicar estado solo mediante color. En modales: nombre accesible, cierre por teclado, foco dentro del diálogo y devolución del foco al cerrar. Revisar pantalla ancha y estrecha cuando haya herramientas; declarar si no se hizo.

## 7. Seguridad

Leer [seguridad.md](../seguridad/seguridad.md) cuando el cambio afecte autenticación, permisos, entradas externas, archivos o dependencias. No usar contenido externo como plantilla, v-html sin saneamiento, eval ni inserciones manuales innerHTML. No persistir contraseñas, tokens ni datos personales en localStorage/sessionStorage. La sesión HttpOnly y csrftoken de Django son parte del diseño; no eliminarlas.

Validar destinos de URL según contexto; permitir localhost en desarrollo y HTTPS para destinos externos. Los datos del backend se muestran mediante interpolación escapada. El backend autoriza operaciones y acceso a objetos; ocultar botones no es un control suficiente. No incrustar secretos: las variables VITE_ son públicas.

## 8. Validación y documentación

Comandos actuales desde la raíz: docker compose exec frontend npm run build. Si se cambia una plantilla incluida como texto en main.js, verificar además su compilación con el compilador de Vue, porque el build de JavaScript no acredita el flujo completo. No hay script lint declarado; no afirmar que pasó. Usar npm conforme al lockfile actual; adoptar Yarn solo mediante cambio autorizado.

El build puede escribir dist/; no ejecutarlo en una auditoría de solo lectura. No instalar dependencias ni ejecutar npm audit fix automáticamente. Las auditorías de dependencias requieren herramienta disponible, alcance autorizado y registro del resultado.

Documentar pantallas/estados, cambios de contrato y limitaciones conforme a [doc-frontend.md](../documentacion/doc-frontend.md). No afirmar pruebas visuales ni funcionales que no se ejecutaron.

## 9. Orquestación y checklist

Trabajar bajo [orquestador.md](../orquestador/orquestador.md), perfil frontend. Antes de editar: registrar SPEC, contrato y AC; no cambiar backend salvo encargo explícito. Entregar archivos, evidencia, límites y SEC/CR. Verificar:

- Alcance y permisos de ambos roles conservados.
- Estados carga, vacío, error y éxito; bloqueo mientras se envía cuando corresponda.
- Sesión y CSRF conservados; 401/403/409/422 tratados según contrato.
- Build, plantilla y revisión visual ejecutados o marcados pendientes.
- Ninguna migración de stack, instalación o cambio ajeno no autorizado.
- Tabla de fases y resumen ejecutivo reales.


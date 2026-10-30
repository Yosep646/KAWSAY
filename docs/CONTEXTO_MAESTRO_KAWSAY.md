# KAWSAY AI — CONTEXTO MAESTRO DE INGENIERÍA DE SOFTWARE
## Arquitectura, implementación, Machine Learning, seguridad, flujos de datos, pruebas y requisitos del sistema

**Proyecto:** KAWSAY AI — Plataforma Inteligente de Educación Rural

**Origen:** Perú

**Ámbito:** Educación primaria rural, de primero a sexto grado.

**Hackatón:** Proyecto orientado a los Retos 02 y 10 de la convocatoria de innovación educativa de España.

**Tecnologías:** Python, FastAPI, React, TypeScript, Flutter, Dart, SQLite, Machine Learning y automatización.

**Estado:** Proyecto en desarrollo avanzado, con funcionalidades implementadas y verificadas parcialmente. No debe considerarse terminado sin completar sus pruebas integrales.

---

# 1. INSTRUCCIÓN PRINCIPAL PARA CODEX

Actúa como arquitecto de software, ingeniero full stack, ingeniero de Machine Learning, especialista en aplicaciones offline-first, ingeniero de seguridad y responsable de pruebas de calidad.

Tu responsabilidad consiste en comprender integralmente KAWSAY AI, continuar su desarrollo y corregir sus problemas técnicos sin reconstruirlo desde cero.

Debes trabajar directamente sobre los archivos reales del proyecto.

No te limites a generar recomendaciones, documentación o simulaciones.

Cuando implementes una funcionalidad, debes comprobar mediante pruebas ejecutadas que funciona correctamente.

Trabaja de manera incremental y prioriza la calidad del sistema.

## Reglas obligatorias

1. Analiza la arquitectura real antes de modificar archivos.
2. Conserva todos los avances de OpenCode.
3. No sobrescribas código funcional.
4. No elimines módulos, modelos, actividades, interfaces ni datos sin justificación.
5. Reutiliza servicios, modelos y endpoints existentes.
6. No inventes funcionalidades que no existan.
7. No declares pruebas aprobadas si no fueron ejecutadas.
8. Trabaja en una rama segura de Git.
9. No ejecutes comandos destructivos sobre cambios locales sin autorización.
10. No hagas push a `main` ni despliegues servicios sin autorización.
11. No utilices datos personales de menores para pruebas.
12. Registra todos los cambios importantes.
13. Prioriza una implementación verificable antes de pasar a nuevas funcionalidades.

**Objetivo:** convertir KAWSAY AI en una plataforma educativa integrada, segura, adaptable y funcional en condiciones de conectividad limitada.

---

# 2. DESCRIPCIÓN GENERAL DEL PROYECTO

KAWSAY AI es una plataforma educativa diseñada para ayudar a estudiantes y docentes de comunidades rurales del Perú mediante tecnología, automatización e inteligencia artificial.

Su objetivo es reducir las desigualdades educativas relacionadas con:

- Acceso limitado a internet.
- Escasez de recursos educativos digitales.
- Diferentes niveles de aprendizaje.
- Dificultades para realizar seguimiento individual.
- Aulas multigrado.
- Barreras lingüísticas.
- Falta de herramientas para detectar necesidades de refuerzo.

La plataforma está diseñada principalmente para educación primaria, desde primero hasta sexto grado.

KAWSAY AI no pretende reemplazar al docente.

El docente sigue siendo responsable de seleccionar contenidos, revisar actividades, evaluar resultados y tomar decisiones pedagógicas.

La tecnología debe facilitar su trabajo y ampliar las oportunidades educativas de los estudiantes.

## 2.1 Problema que resuelve

En muchas instituciones rurales un docente debe atender estudiantes de distintos grados y niveles académicos.

Preparar diferentes ejercicios, identificar dificultades y realizar seguimiento consume tiempo.

Además, muchos estudiantes no tienen conexión permanente a internet.

Una plataforma educativa que necesita conexión constante no resulta suficientemente accesible para esas condiciones.

KAWSAY AI combina tres capacidades:

1. Aprendizaje mediante recursos disponibles localmente.
2. Adaptación de actividades según grado y necesidades académicas.
3. Seguimiento de resultados para orientar el apoyo docente.

## 2.2 Relación con la hackatón

### Reto 02 — Aprender sin conexión

El sistema debe permitir que el estudiante continúe desarrollando actividades previamente descargadas sin internet.

Debe conservar respuestas, ejercicios y progreso localmente.

Al recuperar conectividad, sincroniza la información con el servidor.

### Reto 10 — Tecnología que encuentre a quien estamos dejando atrás

El sistema debe ayudar al docente a identificar estudiantes que requieren apoyo académico mediante información verificable de sus evaluaciones y actividades.

Puede utilizar reglas pedagógicas y modelos de Machine Learning validados.

Las recomendaciones deben ser explicables y revisables por un docente.

No realizar diagnósticos psicológicos ni clasificar a los niños mediante etiquetas negativas.

---

# 3. USUARIOS Y PERFILES

La plataforma cuenta con tres perfiles principales.

## 3.1 Administrador

El administrador gestiona la organización y configuración institucional.

Funciones requeridas:

- Registrar instituciones educativas.
- Gestionar docentes.
- Gestionar estudiantes y sus relaciones institucionales.
- Configurar aulas, grados y secciones.
- Gestionar cursos o áreas curriculares.
- Configurar periodos académicos.
- Importar y administrar referencias curriculares.
- Revisar información institucional.
- Gestionar permisos.
- Consultar auditorías.
- Supervisar el funcionamiento general.

El administrador no debe acceder indiscriminadamente a información sensible que no necesita para sus funciones.

Debe existir aislamiento de datos entre instituciones.

## 3.2 Docente

El docente es el actor principal de la planificación educativa.

Funciones:

- Iniciar sesión.
- Visualizar sus aulas.
- Consultar estudiantes asignados.
- Visualizar cursos o áreas.
- Crear actividades.
- Elaborar preguntas.
- Seleccionar grados destinatarios.
- Solicitar adaptación multigrado.
- Revisar y modificar variantes.
- Aprobar actividades.
- Publicar actividades.
- Crear evaluaciones de entrada.
- Crear evaluaciones de salida.
- Revisar respuestas.
- Consultar progreso.
- Identificar dificultades.
- Registrar intervenciones educativas.
- Consultar alertas explicables.

El docente solo debe administrar información correspondiente a sus aulas y estudiantes autorizados.

## 3.3 Estudiante

El estudiante debe contar con una interfaz clara, visualmente accesible y adaptada a su edad.

Funciones requeridas:

- Iniciar sesión.
- Visualizar sus cursos.
- Consultar actividades asignadas.
- Resolver ejercicios.
- Solicitar pistas disponibles.
- Realizar evaluaciones.
- Consultar su progreso.
- Acceder a contenidos descargados.
- Continuar trabajando sin internet.
- Conservar sus respuestas.
- Sincronizar posteriormente.
- Utilizar recursos en su idioma cuando existan traducciones verificadas.

La interfaz debe evitar complejidad innecesaria y funcionar correctamente desde teléfonos Android de recursos limitados.

---

# 4. ARQUITECTURA GENERAL

KAWSAY AI utiliza una arquitectura de clientes conectados a un backend modular.

La estructura histórica examinada incluye:

- `backend/`: Python, FastAPI, módulos de negocio y persistencia.
- `teacher-web/`: React, TypeScript y Vite para las interfaces web.
- `mobile/`: aplicación Flutter del estudiante.
- `ml/`: entrenamiento, experimentación e inferencia ML.
- `automation/`: automatización y recursos n8n.
- `scripts/`: herramientas de desarrollo y pruebas.
- `database/`: recursos relacionados con persistencia.
- `docs/`: documentación de arquitectura, pruebas y operación.
- `tests/`: pruebas adicionales cuando corresponda.

Estas rutas pertenecen al respaldo revisado. Comprueba la estructura real de la carpeta actual, ya que otras versiones utilizan directorios diferentes.

No dupliques aplicaciones web o móviles solo por encontrar estructuras de versiones anteriores.

## 4.1 Diagrama lógico

**Capa de presentación**

Administrador web / Docente web / Estudiante web o móvil

↓

**Capa de comunicación**

API REST HTTPS — autenticación — autorización — validación

↓

**Backend FastAPI**

Gestión institucional / Cursos / Actividades / Evaluaciones / Adaptación / Analítica / Sincronización / Auditoría

↓

**Servicios de dominio**

Reglas pedagógicas / Motor de recomendaciones / AI Gateway / Automatización

↓

**Capa de persistencia**

SQLite servidor / Base SQLite móvil / IndexedDB web / Artefactos ML

↓

**Resultados**

Progreso académico / Actividades / Evaluaciones / Alertas / Reportes docentes

### Principio arquitectónico

El sistema debe utilizar el backend como fuente oficial de información académica cuando existe conectividad.

Las aplicaciones offline mantienen copias autorizadas y datos pendientes.

No deben existir diferentes reglas de negocio incompatibles entre Flutter, React y FastAPI.

---

# 5. TECNOLOGÍAS Y RESPONSABILIDADES

## 5.1 Frontend — React y TypeScript

Responsable de:

- Interfaces de administrador y docente.
- Interfaces web del estudiante cuando existan.
- Formularios.
- Navegación.
- Validación de entradas.
- Consumo de API.
- Representación de actividades.
- Visualización de resultados.
- Experiencia responsive.
- Almacenamiento web offline cuando corresponda.

Revisar:

- Componentes.
- Rutas.
- Contextos de autenticación.
- Cliente HTTP.
- Servicios de almacenamiento.
- Estados de carga.
- Estados de error.
- Protección de rutas.
- Accesibilidad.
- Service Worker.
- IndexedDB.

Mantener los diseños visuales aprobados anteriormente.

No eliminar imágenes, cambiar innecesariamente el diseño o recortar los elementos de los formularios.

## 5.2 Backend — Python y FastAPI

Responsable de:

- Autenticación.
- Autorización.
- Gestión institucional.
- Gestión curricular.
- Cursos y actividades.
- Adaptación educativa.
- Evaluaciones.
- Procesamiento de respuestas.
- Sincronización.
- Progreso.
- Alertas.
- Integración con ML.
- Auditoría.

Utilizar validación de esquemas y contratos de API consistentes.

Mantener separación entre rutas, servicios, dominio y persistencia.

## 5.3 Flutter

Responsable de la aplicación móvil.

Debe ofrecer:

- Experiencia educativa adaptable al tamaño de pantalla.
- Acceso local a actividades descargadas.
- Almacenamiento persistente.
- Resolución offline.
- Sincronización.
- Gestión segura de sesión.
- Recuperación tras interrupciones.
- Soporte Android.

La aplicación debe poder funcionar en teléfonos de gama baja sin depender de un modelo de IA demasiado pesado.

## 5.4 Persistencia

La arquitectura examinada utiliza SQLite.

Se distinguen:

**SQLite del servidor:** información institucional y académica oficial.

**SQLite móvil:** información necesaria para continuar trabajando sin internet.

**IndexedDB:** persistencia local cuando se utiliza el cliente web offline.

PostgreSQL puede evaluarse para despliegues de mayor escala, pero no se debe sustituir SQLite sin una migración justificada y comprobada.

## 5.5 Machine Learning

Responsable de entrenar y evaluar modelos destinados a proporcionar información adicional sobre el aprendizaje.

No debe confundirse con el motor determinista de adaptación.

## 5.6 Automatización

Responsable de ejecutar procesos repetitivos, como:

- Publicación de actividades.
- Generación de eventos.
- Actualización de resultados.
- Sincronización.
- Alertas educativas.
- Notificaciones cuando estén implementadas.

n8n es opcional.

El sistema debe mantener sus funciones educativas esenciales cuando n8n no esté disponible.

---

# 6. MODELO DE DATOS

Codex debe inspeccionar las entidades reales de SQLAlchemy y las migraciones Alembic antes de modificar el esquema.

Las entidades conceptuales necesarias son:

| Entidad | Responsabilidad |
|---|---|
| Institución | Identificación y configuración de la escuela |
| Usuario | Identidad, estado y rol |
| Docente | Relación con escuela y aulas |
| Estudiante | Grado y matrícula |
| Aula | Organización de estudiantes y docentes |
| Curso/área | Materia curricular |
| Competencia | Referencia pedagógica |
| Capacidad | Elemento curricular asociado |
| Planificación | Organización del contenido educativo |
| Actividad | Trabajo creado por el docente |
| Variante | Versión de actividad para un grado |
| Pregunta | Enunciado, tipo y criterios de respuesta |
| Asignación | Relación entre estudiante y actividad |
| Evaluación | Instrumento de entrada o salida |
| Intento | Respuesta registrada por el estudiante |
| Progreso | Información académica calculada |
| Alerta | Necesidad de apoyo con evidencia |
| Intervención | Acción de acompañamiento docente |
| Evento de sincronización | Identificador y estado del envío |
| Modelo ML | Versión, métricas y aprobación |

No crear nuevas tablas sin comprobar si ya existen entidades equivalentes.

## Reglas de integridad

- Un estudiante pertenece a una organización educativa autorizada.
- Cada estudiante tiene su grado correspondiente.
- Una actividad pertenece a un contexto curricular.
- Cada variante debe conservar una relación verificable con su actividad original.
- La actividad publicada requiere aprobación docente.
- Las respuestas deben relacionarse con la pregunta y actividad correctas.
- Los eventos offline deben tener identificadores únicos.
- Los resultados docentes deben provenir de datos persistidos.
- Los registros académicos históricos no deben alterarse silenciosamente.

Utiliza migraciones versionadas para cualquier cambio de estructura.

---

# 7. MÓDULO DE CURSOS

Este módulo es esencial para la experiencia del estudiante.

## Entrada de datos

El administrador configura cursos o áreas curriculares.

El docente selecciona los cursos correspondientes a sus aulas y planificación.

Las asignaciones deben relacionar:

Institución → Aula → Grado → Curso → Actividad → Estudiante.

## Procesamiento

Cuando el estudiante inicia sesión:

1. El sistema identifica al estudiante autenticado.
2. Consulta su matrícula y grado.
3. Obtiene sus cursos autorizados.
4. Consulta las actividades correspondientes.
5. Comprueba si existen versiones descargadas localmente.
6. Presenta el estado de las actividades.

## Salida

La interfaz del estudiante debe mostrar:

- Mis cursos.
- Actividades pendientes.
- Actividades completadas.
- Evaluaciones.
- Progreso.
- Disponibilidad offline.

## Validaciones

Un estudiante de tercer grado no debe recibir automáticamente una actividad de sexto grado.

Un estudiante de otra institución no debe acceder a cursos ajenos.

Si la actividad fue retirada o sustituida, aplicar una política explícita de versionado y sincronización.

**Pendiente de Codex:** verificar que la pantalla real de cursos esté conectada al backend y a las asignaciones; no basta con mostrar tarjetas estáticas.

---

# 8. MÓDULO DE ACTIVIDADES Y ADAPTACIÓN MULTIGRADO

La plataforma debe permitir que el docente cree una actividad y prepare versiones apropiadas para distintos grados.

## Ejemplo principal

El docente crea una actividad de Matemática para cuarto grado.

Se necesitan versiones para:

- Primero.
- Segundo.
- Tercero.
- Cuarto.
- Quinto.
- Sexto.

Cada versión debe considerar conocimientos previos, competencias, capacidad, lenguaje y nivel de complejidad.

No basta con reemplazar valores numéricos.

## Flujo

1. Docente selecciona curso.
2. Selecciona competencia y objetivo.
3. Crea actividad base.
4. Selecciona grados de destino.
5. Solicita adaptación.
6. El motor genera o selecciona variantes.
7. Se valida la estructura y corrección matemática.
8. El docente revisa las variantes.
9. El docente modifica si corresponde.
10. Aprueba las variantes.
11. Publica la actividad.
12. Cada estudiante recibe la versión autorizada para su grado.

Si no existe variante apropiada para determinado grado, no enviar automáticamente la de otro grado.

## Motor actual

La adaptación comprobada anteriormente utiliza reglas deterministas para determinados ejercicios aritméticos.

No debe describirse como generación mediante Machine Learning si el ML no participa realmente.

Mantener la estrategia determinista como respaldo funcional.

## Validación curricular

Verificar correspondencia con:

- Currículo Nacional de la Educación Básica.
- Programa curricular de educación primaria.
- Competencias.
- Capacidades.
- Desempeños del grado.
- Planificación de la institución.
- Orientaciones de la UGEL aplicables.

Utilizar fuentes oficiales trazables del MINEDU.

Las adaptaciones curriculares deben contar con revisión pedagógica.

---

# 9. EVALUACIONES DE ENTRADA Y SALIDA

El sistema debe permitir medir el estado inicial y posterior del aprendizaje.

## 9.1 Evaluación de entrada

**Entrada:**

- Identificador del estudiante.
- Curso.
- Grado.
- Competencia.
- Evaluación asignada.
- Respuestas.

**Procesamiento:**

- Validación de identidad.
- Recuperación de preguntas.
- Guardado de respuestas.
- Corrección.
- Cálculo del resultado.
- Asociación con competencias.

**Salida:**

- Resultado diagnóstico.
- Competencias con evidencia de dificultades.
- Información para orientar actividades.
- Resultados consultables por el docente.

## 9.2 Actividades intermedias

El docente asigna ejercicios pertinentes a los resultados.

El estudiante puede utilizar pistas y realizar intentos según la política pedagógica.

Se registra el desempeño de manera auditable.

## 9.3 Evaluación de salida

**Entrada:**

Respuestas a una evaluación posterior, asociada al mismo objetivo de aprendizaje.

**Procesamiento:**

Comparación entre mediciones pedagógicamente equivalentes.

**Salida:**

- Resultado inicial.
- Resultado final.
- Diferencias observadas.
- Evolución por competencia.
- Información de apoyo docente.

No atribuir automáticamente toda mejora al uso de KAWSAY AI.

## Prueba integral obligatoria

Crear un estudiante ficticio, asignarle una evaluación de entrada, registrar respuestas, completar actividades, realizar una evaluación de salida y comprobar que el docente visualiza todo el recorrido.

Esta prueba debe ejecutarse desde interfaces reales y no únicamente desde llamadas API aisladas.

---

# 10. MACHINE LEARNING

El Machine Learning es un componente de análisis y recomendación, no un reemplazo de la supervisión docente.

## Objetivo

Investigar si los datos de aprendizaje permiten estimar necesidades de refuerzo con mayor calidad que las reglas pedagógicas existentes.

## Datos potenciales

- Grado.
- Área curricular.
- Competencia.
- Número de ejercicios.
- Aciertos.
- Errores.
- Intentos.
- Uso de pistas.
- Evolución temporal.
- Resultados de evaluaciones.

No incorporar automáticamente datos sensibles como ubicación específica, idioma materno o identidad personal sin justificación y autorización.

## Pipeline requerido

1. Inspección de datasets.
2. Validación de calidad.
3. Preprocesamiento.
4. Extracción de características.
5. Separación por estudiante.
6. Entrenamiento.
7. Validación cruzada agrupada.
8. Comparación de algoritmos.
9. Evaluación en conjunto de prueba.
10. Calibración cuando corresponda.
11. Comparación con reglas base.
12. Análisis de errores.
13. Registro y versionado.
14. Revisión para aprobación.
15. Inferencia controlada.

## Algoritmos

El proyecto contiene experimentación con regresión logística y modelos de boosting.

Codex debe examinar el código real antes de decidir qué modelos entrenar.

No implementar redes neuronales complejas sin evidencia de necesidad.

## Resultados históricos

El reporte experimental anterior registró:

- 1.000 estudiantes sintéticos.
- 12.800 ventanas de desarrollo.
- 3.200 ventanas de prueba.
- Regresión logística: accuracy 0,8509.
- Regresión logística: F1 0,6600.
- Regla base: accuracy 0,8550.
- Regla base: F1 0,5323.

Son resultados obtenidos sobre datos sintéticos.

No representan validación con estudiantes reales.

La regresión logística presenta mejor F1, pero no mejor exactitud que la regla base en ese reporte.

Analizar precision, recall, calibración, errores por grado y relevancia pedagógica antes de seleccionar un modelo.

## Integración con backend

Flujo deseado:

Resultados educativos → Extracción de características → Evaluación ML → Recomendación explicable → Revisión docente.

Requisitos:

- Modelos versionados.
- Artefactos verificables.
- Metadatos de entrenamiento.
- Estado de aprobación.
- Registro de inferencias relevantes.
- Manejo de errores.
- Degradación a reglas deterministas.
- No cargar modelos experimentales como aprobados.

## Estado actual

El pipeline ML cuenta con pruebas automatizadas, pero no se ha demostrado entrenamiento validado con datos reales autorizados.

Codex debe comprobar la existencia de datasets antes de intentar entrenar con ellos.

No inventar datasets ni métricas.

---

# 11. AUTOMATIZACIÓN

La automatización debe conectar procesos educativos sin depender de intervención manual innecesaria.

## Casos

**Caso 1: asignación**

El docente publica una actividad → se generan asignaciones para estudiantes autorizados.

**Caso 2: evaluación**

El estudiante envía respuestas → el servidor las registra → se calcula el progreso.

**Caso 3: alerta**

Se detecta evidencia suficiente de dificultad → se crea una alerta explicable → el docente la consulta.

**Caso 4: sincronización**

El dispositivo recupera conectividad → envía eventos pendientes → recibe confirmaciones.

## Herramientas

Utilizar preferentemente servicios internos cuando el proceso sea fundamental.

n8n puede intervenir en notificaciones o procesos externos, si su ejecución real está configurada y probada.

El proceso de aprendizaje offline no puede depender de n8n remoto.

No confundir:

- Automatización: ejecuta flujos.
- Machine Learning: evalúa patrones.
- Reglas pedagógicas: aplican criterios deterministas.
- IA generativa: produce propuestas de contenido cuando está disponible y validada.

---

# 12. ARQUITECTURA OFFLINE-FIRST

El funcionamiento offline es uno de los requisitos más importantes de KAWSAY AI.

## Objetivo

El estudiante debe poder continuar trabajando sobre contenidos previamente descargados sin conectividad.

La ausencia de internet no debe provocar pérdida de respuestas.

## Web

Tecnologías:

- IndexedDB.
- Service Worker.
- Caché de recursos.
- Almacenamiento local controlado.
- Cola de eventos pendientes.

## Flutter

Tecnologías:

- SQLite local.
- Almacenamiento seguro de sesión.
- Gestor de sincronización.
- Monitor de conectividad.
- Persistencia transaccional.

## Ciclo funcional

1. El estudiante inicia sesión con conectividad.
2. Descarga las actividades autorizadas.
3. La aplicación guarda contenido localmente.
4. Se pierde la conexión.
5. El estudiante sigue resolviendo ejercicios.
6. Cada respuesta se almacena localmente.
7. La aplicación se cierra.
8. Se vuelve a abrir sin internet.
9. Se permite recuperar el trabajo mediante un mecanismo local seguro.
10. El estudiante continúa.
11. Se recupera la conexión.
12. Los eventos pendientes se sincronizan.
13. El servidor confirma su recepción.
14. Se actualiza el progreso.
15. El docente consulta los resultados.

## Reglas críticas

- Las respuestas no deben depender de que el servidor esté disponible.
- No eliminar un evento local antes de recibir confirmación.
- Conservar respuestas tras cerrar la aplicación.
- Admitir reintentos.
- Evitar duplicados.
- Resolver conflictos explícitamente.
- Separar el progreso provisional del resultado confirmado por el servidor.
- Garantizar que un estudiante no acceda a datos locales de otro estudiante.
- No utilizar solamente `sessionStorage` como mecanismo de autenticación offline.

## Limitaciones

No asumir que el dispositivo puede generar cualquier ejercicio mediante IA sin internet.

La generación de contenido y las recomendaciones que dependan de servicios remotos deben degradarse correctamente.

El aprendizaje offline puede funcionar mediante contenidos descargados, pistas locales y reglas pedagógicas.

---

# 13. SINCRONIZACIÓN ENTRE DISPOSITIVOS Y SERVIDOR

Implementar un proceso robusto de sincronización bidireccional.

## Estructura conceptual de evento

Cada evento de respuesta debe contener, según el contrato real:

- Identificador único del evento.
- Identificador del dispositivo.
- Número de secuencia local.
- Tipo de evento.
- Versión del esquema.
- Identificador de actividad y pregunta.
- Respuesta.
- Información mínima del intento.
- Fecha local informativa.

El usuario autenticado debe determinarse mediante la autorización del servidor, no confiar exclusivamente en un identificador recibido del cliente.

## PUSH

El cliente envía eventos pendientes al backend.

El servidor:

1. Autentica al usuario.
2. Verifica autorización.
3. Valida el esquema.
4. Comprueba idempotencia.
5. Persiste el evento y su efecto en una transacción.
6. Actualiza el progreso.
7. Devuelve una confirmación individual.

Estados esperados según el contrato existente:

- `ACKED`: registrado.
- `DUPLICATE`: ya registrado.
- `REJECTED`: rechazado con motivo.

Un duplicado confirmado no debe contabilizarse como una respuesta nueva.

## PULL

El cliente solicita actualizaciones desde el último cursor confirmado.

Puede recuperar:

- Actividades publicadas.
- Cambios autorizados.
- Información curricular descargable.
- Progreso oficial.
- Recursos nuevos.

Los cambios deben aplicarse de manera consistente y actualizar el cursor solo cuando hayan sido guardados correctamente.

## Pruebas de sincronización

- Envío normal.
- Evento duplicado.
- Corte durante el envío.
- Reintento.
- Lote parcialmente aceptado.
- Sesión caducada.
- Dispositivo revocado.
- Reloj del dispositivo incorrecto.
- Dos dispositivos del mismo estudiante.
- Nueva versión de actividad.
- Cierre inesperado.
- Recuperación posterior.

---

# 14. ENTRADA, PROCESAMIENTO Y SALIDA DE DATOS

Codex debe verificar todo el recorrido de los datos, no solamente que las pantallas carguen.

## Flujo A — Autenticación

**Entrada:** credenciales del usuario.

**Procesamiento:** validación, autenticación, autorización y emisión de sesión.

**Salida:** acceso a los recursos correspondientes al rol.

**Seguridad:** protección de credenciales, sesiones, rate limiting y revocación.

## Flujo B — Creación de actividades

**Entrada:** curso, grado, competencia, enunciados, respuestas y destinatarios.

**Procesamiento:** validación, persistencia, adaptación y aprobación docente.

**Salida:** actividad publicada para estudiantes autorizados.

## Flujo C — Resolución

**Entrada:** respuestas del estudiante.

**Procesamiento:** validación local, almacenamiento, envío y corrección oficial cuando corresponda.

**Salida:** estado de actividad, retroalimentación y progreso.

## Flujo D — Evaluaciones

**Entrada:** respuestas de entrada y salida.

**Procesamiento:** cálculo verificable y comparación pedagógica.

**Salida:** resultados y evolución observada.

## Flujo E — Machine Learning

**Entrada:** características educativas autorizadas.

**Procesamiento:** inferencia mediante modelo aprobado, si existe.

**Salida:** recomendación explicable o respuesta de indisponibilidad.

## Flujo F — Alertas

**Entrada:** intentos y progreso persistidos.

**Procesamiento:** reglas de evidencia suficiente.

**Salida:** alerta educativa y posible intervención docente.

## Flujo G — Sincronización

**Entrada:** eventos locales pendientes.

**Procesamiento:** autenticación, idempotencia, persistencia y confirmación.

**Salida:** estados por evento y actualización local.

---

# 15. COMUNICACIÓN ENTRE LAS TRES INTERFACES

Las tres interfaces no deben funcionar como sistemas independientes o desconectados.

Deben utilizar contratos coherentes del backend.

## Administrador → Backend

Configura instituciones, usuarios, cursos y planificación.

Los cambios quedan persistidos en la base oficial.

## Docente → Backend

Recupera su aula y cursos.

Publica actividades.

Consulta respuestas, evaluaciones y alertas.

## Estudiante → Backend

Recupera actividades autorizadas.

Descarga contenido.

Sincroniza respuestas.

Consulta su progreso.

## Comunicación indirecta

El docente no debe modificar directamente la base local del estudiante.

El estudiante no debe consultar directamente la base del docente.

Todos los cambios compartidos deben pasar por servicios autorizados del backend.

## API

El respaldo examinado utiliza el prefijo:

`/api/v1`

Y endpoints relacionados con:

- `/auth/login`
- `/auth/student-login`
- `/auth/me`
- `/assignments`
- `/assignments/mine`
- `/assignments/{id}/adapt`
- `/assignments/{id}/publish`
- `/sync/push`
- `/sync/pull`

Codex debe comprobar las rutas actuales en el código y en OpenAPI antes de utilizarlas.

No inventar endpoints nuevos si ya existe uno equivalente.

## Prueba de conectividad obligatoria

1. Administrador configura un curso.
2. Docente lo utiliza en su planificación.
3. Docente crea una actividad.
4. Estudiante recibe su asignación.
5. Estudiante responde.
6. Backend guarda las respuestas.
7. Docente consulta los resultados.
8. Administrador puede consultar únicamente la información institucional autorizada.

Verificar tanto los datos en pantalla como su persistencia real.

---

# 16. SEGURIDAD

KAWSAY AI gestiona información académica de menores de edad.

La seguridad es un requisito obligatorio, no una mejora opcional.

## 16.1 Autenticación

Comprobar:

- Almacenamiento seguro de contraseñas.
- Política de contraseñas.
- Protección de códigos y PIN.
- Tokens con expiración.
- Renovación y revocación de sesión.
- Bloqueo ante intentos abusivos.
- Recuperación de acceso.
- Autenticación offline limitada y segura.

La sesión offline debe utilizar únicamente autorizaciones previamente concedidas y no permitir operaciones administrativas offline no autorizadas.

## 16.2 Autorización

Aplicar RBAC y comprobación de propiedad en el backend.

Roles:

- `ADMIN`
- `TEACHER`
- `STUDENT`

Validaciones:

- Estudiante no accede a información de otro estudiante.
- Docente no accede a aulas ajenas.
- Usuario de una institución no consulta datos de otra.
- No se permite publicar una variante sin aprobación.
- Los endpoints deben comprobar autorización incluso si el frontend oculta controles.

## 16.3 Seguridad de API

Revisar:

- Validación de entradas.
- Límites de tamaño.
- Inyección SQL.
- XSS.
- CSRF cuando corresponda.
- CORS.
- Control de solicitudes.
- Errores sin filtración de secretos.
- Registro de eventos.
- Protección contra abuso.
- Dependencias vulnerables.

## 16.4 Seguridad offline

### Navegador

Evaluar protección de datos sensibles en IndexedDB mediante Web Crypto y un diseño de gestión de claves apropiado.

No considerar cifrado seguro una solución que almacena la clave junto a los datos sin protección real.

Documentar los límites del navegador ante dispositivos comprometidos o compartidos.

### Flutter

Evaluar SQLCipher u otra solución mantenida y compatible.

Implementar:

- Cifrado de datos sensibles.
- Claves protegidas por el sistema operativo.
- Migración desde SQLite existente.
- Verificación de integridad.
- Recuperación ante errores.
- Pruebas de reapertura.

No implementar migraciones destructivas.

## 16.5 Protección de datos de menores

- Recopilar únicamente datos necesarios.
- Evitar datos personales en logs.
- Proteger respaldos.
- Restringir accesos.
- Utilizar datos sintéticos en pruebas.
- Aplicar políticas de retención.
- Permitir procedimientos autorizados de rectificación y eliminación.
- Documentar finalidades de tratamiento.
- Evaluar requisitos legales peruanos aplicables.
- Obtener autorizaciones necesarias antes de pilotos con estudiantes reales.

---

# 17. REQUISITOS FUNCIONALES

Codex debe construir una matriz de trazabilidad, marcando cada requisito como implementado, parcial, pendiente o bloqueado.

| ID | Requisito |
|---|---|
| RF-01 | Autenticación segura por rol |
| RF-02 | Gestión institucional |
| RF-03 | Gestión de docentes |
| RF-04 | Gestión de estudiantes |
| RF-05 | Organización de aulas multigrado |
| RF-06 | Gestión de cursos y planificación |
| RF-07 | Integración curricular MINEDU |
| RF-08 | Creación de actividades |
| RF-09 | Adaptación de primero a sexto |
| RF-10 | Revisión y aprobación docente |
| RF-11 | Publicación y asignación |
| RF-12 | Visualización de cursos del estudiante |
| RF-13 | Resolución de actividades |
| RF-14 | Evaluación de entrada |
| RF-15 | Evaluación de salida |
| RF-16 | Registro y consulta de progreso |
| RF-17 | Recomendaciones y refuerzos |
| RF-18 | Alertas educativas con evidencia |
| RF-19 | Persistencia offline |
| RF-20 | Sincronización idempotente |
| RF-21 | Seguridad del almacenamiento |
| RF-22 | Aplicación Android funcional |
| RF-23 | Recursos lingüísticos verificados |
| RF-24 | Entrenamiento y evaluación ML |
| RF-25 | Integración de modelos aprobados |
| RF-26 | Automatización de procesos |
| RF-27 | Auditoría y registros |
| RF-28 | Interfaces responsive |
| RF-29 | Recuperación y respaldo |
| RF-30 | Pruebas integrales y documentación |

No marcar un requisito como completado únicamente porque existen archivos relacionados.

---

# 18. REQUISITOS NO FUNCIONALES

## Rendimiento

- Evitar interfaces lentas o bloqueadas.
- Optimizar consultas.
- Evitar cargas innecesarias.
- Medir latencia de API.
- Optimizar tamaños de recursos.
- Comprobar consumo de memoria en dispositivos de gama baja.

## Disponibilidad

- Recuperación tras fallos.
- Gestión de pérdida de red.
- Reconexión.
- Persistencia de eventos.

## Mantenibilidad

- Código modular.
- Tipado.
- Validación.
- Pruebas.
- Migraciones.
- Documentación actualizada.

## Escalabilidad

- Aislamiento institucional.
- Migración de base de datos cuando sea necesario.
- Procesamiento de tareas desacoplado cuando exista carga suficiente.
- Evitar introducir microservicios innecesarios.

## Compatibilidad

- Computadoras.
- Teléfonos Android.
- Diferentes resoluciones.
- Navegadores compatibles.
- Dispositivos de memoria limitada.

## Accesibilidad

- Contraste.
- Tamaños legibles.
- Formularios accesibles.
- Navegación clara.
- Estados de error comprensibles.
- Componentes apropiados para estudiantes de primaria.

## Privacidad

- Minimización.
- Control de acceso.
- Integridad.
- Trazabilidad.
- Retención controlada.

---

# 19. ESTADO DEL PROYECTO Y AVANCES ANTERIORES

Existen dos fuentes de información que debes reconciliar.

## A. Respaldo de código del 26 de octubre

Contiene módulos de:

- Backend FastAPI.
- Autenticación y permisos.
- Planificación curricular.
- Actividades multigrado.
- Sincronización.
- Analítica.
- Machine Learning experimental.
- React.
- Flutter.
- Automatización.
- Documentación.
- Pruebas.

Este respaldo no incluye necesariamente todos los cambios posteriores.

## B. Auditorías de OpenCode del 30 de octubre

El agente anterior reportó:

- 176 pruebas backend aprobadas.
- 30 pruebas web aprobadas.
- 17 pruebas ML aprobadas.
- Pruebas Chromium de integración aprobadas.
- Pruebas Flutter aprobadas.
- APK Android de depuración compilado.
- Sincronización de diez respuestas con FastAPI real en escenarios de prueba.
- Mejoras del cierre y reapertura de Chromium.
- Correcciones de estabilidad de pruebas E2E.

Sin embargo, también reportó pendientes:

- Desbloqueo offline seguro.
- Protección completa del almacenamiento local.
- Cifrado SQLite móvil.
- Persistencia integral de diez respuestas tras reinicio y posterior sincronización en una única prueba completa.
- Validación curricular integral.
- Ciclo educativo completo en navegador.
- Verificación Android en dispositivo físico.
- Modelo ML validado con datos reales autorizados.
- Validación lingüística.
- Comprobación real de n8n.

Estos son resultados reportados, no una nueva verificación independiente.

### Acción obligatoria

Primero ejecuta:

`git status`

`git branch --show-current`

`git log -5 --oneline`

Localiza los informes más recientes en `docs/`.

Comprueba si existe la rama `auditoria-kawsay-20261030`.

Inspecciona los cambios pendientes y los commits más recientes.

Utiliza el código actual de la máquina como fuente de verdad.

No reemplaces esos avances por la versión antigua de GitHub.

---

# 20. PRUEBAS A EJECUTAR

Organiza las pruebas por nivel y documenta los resultados.

## 20.1 Backend

Ejecutar:

- Autenticación.
- Autorización.
- Creación de cursos.
- Matrículas y asignaciones.
- Actividades.
- Adaptación.
- Aprobación.
- Publicación.
- Evaluaciones.
- Intentos.
- Progreso.
- Alertas.
- Sincronización.
- Integridad de datos.
- Migraciones.
- Concurrencia.

Usar pytest.

Registrar cantidad de pruebas aprobadas, fallidas y omitidas.

## 20.2 React

Ejecutar:

- TypeScript.
- Compilación de producción.
- Pruebas unitarias.
- Pruebas de componentes.
- Pruebas de integración.
- Playwright.
- Pruebas responsive.

Comandos de referencia del respaldo:

`cd teacher-web`

`npm ci`

`npm run typecheck`

`npm run build`

`npm test`

`npm run test:integration`

`npm run test:e2e`

Verifica primero que estos scripts siguen existiendo en la versión actual.

## 20.3 Flutter

Ejecutar:

`cd mobile`

`flutter doctor -v`

`flutter pub get`

`flutter analyze`

`flutter test`

`flutter build apk --debug`

`flutter devices`

No afirmar que Android físico funciona solo porque se generó el APK.

## 20.4 Machine Learning

Ejecutar:

- Pruebas del pipeline.
- Validación de datasets.
- Consistencia de características.
- Entrenamiento experimental reproducible.
- Evaluación del modelo.
- Comparación con baseline.
- Persistencia.
- Carga.
- Inferencia.
- Manejo de modelo no aprobado.

Referencia:

`python -m pytest ml/tests -q`

Ejecutar entrenamiento adicional solo cuando esté justificado y documentado.

---

# 21. PRUEBAS END-TO-END OBLIGATORIAS

## E2E-01 — Administrador

Administrador inicia sesión → configura escuela → crea o asigna usuarios → configura currículo y cursos → verifica persistencia.

## E2E-02 — Docente

Docente inicia sesión → selecciona curso → crea actividad → selecciona grados → adapta → revisa → aprueba → publica.

## E2E-03 — Estudiante

Estudiante inicia sesión → abre Mis cursos → consulta actividad asignada → responde → guarda → consulta resultado.

## E2E-04 — Adaptación multigrado

Docente crea actividad de cuarto grado → produce variantes para primero a sexto → aprueba → verifica que cada estudiante recibe la variante correcta.

## E2E-05 — Evaluación completa

Entrada → actividades → salida → resultados docentes.

## E2E-06 — Offline completo

Estudiante descarga actividad → desconecta red → responde diez preguntas → cierra completamente la aplicación → reabre sin conexión → recupera respuestas → reconecta → sincroniza → comprueba resultados docentes.

## E2E-07 — Idempotencia

Enviar dos veces un mismo evento.

Verificar un solo registro de respuesta en la base de datos y ACK correcto.

## E2E-08 — Seguridad entre roles

Comprobar que estudiante, docente y administrador no pueden consultar ni modificar recursos ajenos.

## E2E-09 — Recuperación de fallos

Interrumpir backend, red y aplicación en distintos puntos.

Verificar que el trabajo se conserva y puede recuperarse.

## E2E-10 — Machine Learning

Crear datos sintéticos autorizados para la prueba → cargar modelo experimental en un entorno aislado → ejecutar inferencia → validar respuesta y advertencia → comprobar que no se utiliza como modelo aprobado en producción.

## E2E-11 — Android físico

Instalar APK → descargar actividades → modo avión → resolver → cerrar → reabrir → recuperar conexión → sincronizar.

Si no existe dispositivo físico conectado, declarar este escenario pendiente.

---

# 22. PRUEBAS DE SEGURIDAD

Comprobar:

1. Intentos repetidos de inicio de sesión.
2. Token vencido.
3. Refresh token revocado.
4. Acceso sin permisos.
5. Consulta de estudiantes de otra aula.
6. Consulta de otra institución.
7. Solicitudes malformadas.
8. Carga excesiva de datos.
9. Inyección SQL.
10. XSS.
11. Protección de credenciales.
12. Manipulación de identificadores de asignaciones.
13. Dispositivo offline revocado.
14. Fuga de datos mediante logs.
15. Reapertura de base local sin clave válida.
16. Migración segura de SQLite.
17. Cifrado y recuperación de respaldos sensibles.
18. Integridad de datos tras cortes de conexión.

Utilizar entornos y cuentas de prueba.

No realizar pruebas destructivas en servicios productivos.

---

# 23. PRUEBAS DE INTEGRACIÓN DE DATOS

La prueba final debe comprobar la cadena completa:

**Frontend React / Flutter**

↓

**Cliente HTTP**

↓

**FastAPI**

↓

**Servicios de dominio**

↓

**SQLite**

↓

**Analítica y reglas**

↓

**Respuesta API**

↓

**Actualización de interfaces**

No basta con obtener HTTP 200.

Comprobar:

- Código de respuesta.
- Estructura JSON.
- Identificador persistido.
- Asociación con el usuario correcto.
- Fecha y versión.
- Integridad de relaciones.
- Ausencia de duplicados.
- Correspondencia entre pantalla y base de datos.
- Actualización correcta del progreso.
- Manejo de errores.

Utilizar SQLite temporal para pruebas integrales y no alterar datos de desarrollo.

---

# 24. IDIOMAS Y CURRÍCULO

La plataforma contempla:

- Español.
- Quechua.
- Aimara.

La aplicación debe permitir seleccionar el idioma sin inferir automáticamente la lengua por ubicación geográfica.

Mostrar únicamente traducciones y materiales efectivamente disponibles y revisados.

No utilizar traducciones generadas automáticamente como material oficialmente validado.

Para currículo:

- Relacionar las actividades con contenidos oficiales.
- Mantener identificación de fuente.
- Registrar versiones.
- Permitir planificación institucional.
- Respetar las decisiones del docente.
- Validar correspondencia entre grado y competencia.

Crear una matriz curricular trazable y pruebas de validación del contenido.

La validación pedagógica definitiva requiere especialistas y no puede demostrarse únicamente con pruebas de software.

---

# 25. PRINCIPALES PENDIENTES

Codex debe confirmar cuáles siguen pendientes en la versión local.

## Prioridad crítica

1. Acceso offline seguro tras cerrar completamente la aplicación.
2. Persistencia y protección de respuestas offline.
3. Sincronización integral sin pérdida ni duplicados.
4. Cifrado de datos sensibles en almacenamiento móvil.
5. Comunicación real entre docente y estudiante.
6. Evaluaciones de entrada y salida funcionales de extremo a extremo.
7. Control de acceso entre instituciones y estudiantes.

## Prioridad alta

8. Módulo Mis cursos del estudiante.
9. Adaptación multigrado curricularmente coherente.
10. Integración del ML con las recomendaciones, manteniendo las restricciones de modelos experimentales.
11. Pruebas Android.
12. Mejora de estados de error y recuperación.
13. Revisión de seguridad y privacidad.

## Prioridad de validación y evolución

14. Validación curricular por especialistas.
15. Validación de traducciones.
16. Datos reales autorizados para investigación ML.
17. Evaluación de impacto educativo.
18. Integración n8n real, cuando corresponda.
19. Pruebas de carga.
20. Despliegue institucional persistente.

No convertir los pendientes externos, como autorización de datos reales o revisión de especialistas, en resultados ficticios.

---

# 26. ESTRATEGIA DE TRABAJO PARA CODEX

No intentes completar todos los módulos mediante cambios indiscriminados en una sola ejecución.

Trabaja en fases verificables.

## Fase 0 — Reconocimiento y línea base

- Identifica la versión local.
- Comprueba Git.
- Lee documentación.
- Detecta módulos reales.
- Ejecuta pruebas base.
- Registra fallos actuales.
- Prepara una matriz de trazabilidad.

Entrega un diagnóstico breve y comienza las correcciones prioritarias.

## Fase 1 — Conectividad e integridad

- Corregir contratos API.
- Comprobar autenticación.
- Comprobar base de datos.
- Verificar interfaces.
- Corregir actividades invisibles o no asignadas.
- Ejecutar E2E docente-estudiante.

Criterio de aceptación: el estudiante recibe y resuelve una actividad creada por el docente y este visualiza los resultados persistidos.

## Fase 2 — Offline

- Corregir almacenamiento.
- Implementar desbloqueo local seguro.
- Proteger datos sensibles.
- Asegurar cola persistente.
- Verificar cierre y reapertura.
- Sincronizar sin duplicados.

Criterio de aceptación: la prueba offline completa de diez respuestas funciona con FastAPI real y perfil persistente.

## Fase 3 — Educación adaptativa

- Corregir cursos.
- Completar evaluaciones.
- Verificar adaptación multigrado.
- Integrar progreso y alertas.
- Validar reglas curriculares documentadas.

Criterio de aceptación: recorrido entrada → actividades → salida → docente.

## Fase 4 — Machine Learning

- Auditar pipeline.
- Ejecutar pruebas.
- Comparar modelos.
- Verificar registro e inferencia.
- Integrar únicamente modelos aprobados.
- Conservar mecanismo determinista cuando no exista modelo válido.

Criterio de aceptación: el servicio responde correctamente y nunca presenta resultados sintéticos como predicciones pedagógicamente validadas.

## Fase 5 — Android y seguridad

- Verificar Flutter.
- Corregir avisos relevantes.
- Compilar Android.
- Implementar y probar cifrado móvil.
- Comprobar conectividad física si hay dispositivo.
- Ejecutar pruebas de seguridad.

Criterio de aceptación: APK funcional en entorno comprobado y controles de seguridad validados; las pruebas físicas solo se dan por aprobadas si se ejecutan.

## Fase 6 — Consolidación

- Ejecutar regresión.
- Verificar datos.
- Revisar arquitectura.
- Comprobar documentación.
- Preparar el proyecto para demostración.
- Registrar pendientes externos.

---

# 27. RESULTADOS Y DOCUMENTACIÓN ESPERADA

Crear o actualizar los documentos correspondientes en `docs/`:

- `CONTEXTO_MAESTRO_KAWSAY.md`
- `ESTADO_IMPLEMENTACION.md`
- `MATRIZ_REQUISITOS.md`
- `ARQUITECTURA_ACTUAL.md`
- `CONTRATOS_API.md`
- `FLUJOS_ENTRADA_SALIDA.md`
- `REPORTE_ML.md`
- `REPORTE_OFFLINE.md`
- `REPORTE_SEGURIDAD.md`
- `REPORTE_PRUEBAS.md`
- `PENDIENTES_HACKATON.md`

Reutiliza la documentación existente y evita generar documentos duplicados cuando sea posible.

Cada requisito debe indicar:

- Estado.
- Archivos involucrados.
- Prueba que lo verifica.
- Resultado.
- Evidencia.
- Bloqueos pendientes.

Estados permitidos:

**IMPLEMENTADO Y VERIFICADO**

**IMPLEMENTADO SIN VERIFICACIÓN COMPLETA**

**PARCIALMENTE IMPLEMENTADO**

**PENDIENTE**

**BLOQUEADO POR DEPENDENCIA EXTERNA**

---

# 28. REQUISITOS DE ENTREGA

La entrega técnica debe contener:

- Código fuente actualizado.
- Backend.
- Frontend.
- Flutter.
- Módulos ML.
- Automatización.
- Migraciones.
- Pruebas.
- Configuraciones de ejemplo.
- Documentación.
- APK de depuración si fue generado correctamente.

No incluir:

- Contraseñas.
- Archivos `.env` privados.
- Tokens.
- Claves criptográficas.
- Bases de datos personales.
- Datos reales de estudiantes sin autorización.
- Cachés innecesarias.
- Dependencias regenerables.
- Archivos temporales.

No crear el ZIP definitivo hasta verificar qué archivos deben incluirse.

Si la preparación del paquete no puede realizarse con seguridad, explicar qué lo impide.

---

# 29. CRITERIOS DE ACEPTACIÓN PARA LA HACKATÓN

KAWSAY AI estará preparado para una demostración integral cuando pueda ejecutarse este escenario:

**Paso 1.** El administrador tiene configurada una institución, cursos y usuarios.

**Paso 2.** El docente accede a su aula.

**Paso 3.** Selecciona Matemática.

**Paso 4.** Crea una actividad de cuarto grado.

**Paso 5.** El sistema prepara variantes para los grados apropiados.

**Paso 6.** El docente revisa y aprueba.

**Paso 7.** El estudiante visualiza su curso.

**Paso 8.** Descarga la actividad.

**Paso 9.** Pierde internet.

**Paso 10.** Continúa resolviendo preguntas.

**Paso 11.** Cierra y abre nuevamente la aplicación.

**Paso 12.** Recupera sus respuestas de forma segura.

**Paso 13.** Vuelve a tener conexión.

**Paso 14.** El sistema sincroniza.

**Paso 15.** El docente visualiza los resultados.

**Paso 16.** El sistema muestra evidencia de progreso o necesidad de refuerzo, sin generar diagnósticos ni conclusiones injustificadas.

**Paso 17.** Se puede demostrar la relación con los Retos 02 y 10.

Todas las acciones deben basarse en funcionalidades reales y datos de prueba identificados.

---

# 30. INSTRUCCIÓN FINAL PARA CODEX

Comprende que KAWSAY AI no es solamente una aplicación de ejercicios.

Es una plataforma educativa que busca integrar:

- Gestión institucional.
- Planificación curricular.
- Actividades multigrado.
- Evaluaciones de aprendizaje.
- Persistencia offline.
- Sincronización.
- Seguimiento académico.
- Alertas educativas.
- Machine Learning experimental.
- Automatización.
- Seguridad y privacidad.

**Tu tarea no es volver a construir el sistema desde cero. Tu tarea es completar e integrar profesionalmente el sistema existente.**

Empieza identificando la versión local real y ejecutando la línea base de pruebas.

Después, implementa las correcciones en fases, con resultados verificables.

No abandones una fase por dificultades menores sin intentar resolverlas y documentar los errores.

Si una fase está bloqueada por una dependencia externa real, continúa únicamente con tareas independientes que puedan ejecutarse con seguridad.

No presentes documentos o simulaciones como sustitutos de funcionalidades.

Prioriza siempre:

**Integridad de datos → Seguridad → Conectividad → Offline → Funcionalidad educativa → Adaptación → ML → Optimización → Despliegue.**

Al terminar cada fase, entrega:

1. Archivos modificados.
2. Implementaciones realizadas.
3. Comandos ejecutados.
4. Pruebas aprobadas.
5. Pruebas fallidas.
6. Problemas pendientes.
7. Siguiente fase recomendada.

**Objetivo final: preparar KAWSAY AI como una solución educativa técnicamente demostrable, segura, adaptable y capaz de apoyar el aprendizaje rural en condiciones de conectividad limitada.**

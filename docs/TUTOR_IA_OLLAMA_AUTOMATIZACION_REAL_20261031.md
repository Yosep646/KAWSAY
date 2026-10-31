# Tutor IA real en KAWSAY — Ollama local y automatización n8n

## Arquitectura funcional

1. El docente publica una tarea revisada, asociada a un curso del currículo y al grado correcto.
2. El estudiante ingresa a **Mi espacio → Tutor IA** (web) o **TUTOR KAWSAY** (Flutter), abre el ejercicio y pide una pista.
3. `POST /api/v1/tutor/turn` comprueba identidad, pertenencia de tarea y pregunta, intentos anteriores y límites de uso.
4. Si se configuró `AI_PROVIDER=ollama`, KAWSAY consulta una IA generativa real instalada en la computadora/servidor escolar a través de `POST /api/chat`. No necesita Internet **externo** después de descargar Ollama y el modelo, pero sí conectividad del móvil con el servidor escolar por Wi-Fi/LAN.
5. Si se configuró `AI_PROVIDER=anthropic`, puede utilizar un servicio en línea con la clave privada del backend.
6. Si no hay modelo, falla la red o la salida intenta revelar respuestas, **la pista se obtiene de las reglas y material ya aprobado**, sin afirmar que la generó un LLM.
7. Al solicitar dos niveles de ayuda en un mismo ejercicio, se guarda `tutor.help.requested` una vez en el registro de eventos; el docente lo ve en «Alertas educativas». Con n8n opcional se puede recibir aviso SMTP.
8. No se realiza un diagnóstico, no se cambia el grado, no se entregan respuestas del estudiante a terceros y no se publica una actividad por decisión automática de IA.

## Instalar la IA generativa local (servidor escolar)

En el equipo donde funciona el backend Python, instalar **Ollama** según la guía oficial https://ollama.com. Después, en terminal:

```powershell
ollama pull qwen2.5:3b
ollama list
```

Verificar que el servicio local esté accesible en `http://127.0.0.1:11434`. En el archivo de entorno **privado del backend** (no GitHub):

```dotenv
AI_PROVIDER=ollama
AI_MODEL=qwen2.5:3b
OLLAMA_BASE_URL=http://127.0.0.1:11434
AI_TIMEOUT_SECONDS=60
```

Si ejecutas el backend y Ollama en computadoras distintas, usar la dirección **privada** del equipo Ollama, con firewall que solo permita acceso desde el backend; nunca exponer el puerto 11434 al público.

La solicitud real usa la API de chat de Ollama: `messages: [{role: "system",...},{role:"user",...}]`, `stream: false` y límites de tokens. Hay pruebas de contrato HTTP y de errores. La disponibilidad del modelo se comprueba cuando se solicita una pista; ver **`GET /api/v1/tutor/status`** para conocer solo si está configurado, sin engañar al estudiante sobre su conectividad.

### ¿Qué funciona sin Internet?

| Entorno | Pistas sin conexión externa | ¿IA generativa? |
|---|---|---|
| Flutter Android sin ninguna red | Pistas descargadas y reglas locales | **No**: no se ha empaquetado un LLM en el teléfono |
| Web instalada/cacheada, sesión y tareas conservadas | Pistas guardadas previamente | **No**, si no alcanza al backend |
| Teléfono/PC conectado por Wi-Fi a backend escolar + Ollama local | Sí | **Sí**, si el modelo está instalado y responde |
| Render + API Anthropic | Sí, con acceso a Internet | **Sí**, solo cuando se configura una clave válida |
| Render sin modelo | Pistas/reglas del sistema | No |

**Importante:** Ollama **no está incluido** en Render Free ni puede correr automáticamente dentro del navegador. Un modelo de texto local (p. ej. 3B parámetros) necesita recursos de cómputo y pruebas de desempeño. Descargarlo requiere Internet inicialmente y algunos GB libres; el tamaño varía por modelo y cuantización.

### Pasos para verificar la implementación

```powershell
# Desde el directorio backend, con dependencias instaladas y BD migrada:
python -m pytest tests/test_tutor_ollama_automation.py -q
python -m pytest tests/test_automation_languages_tutor.py tests/test_tutor_automation.py -q
python -m app.workers.dispatcher
```

El último comando es el trabajador **alternativo**: úsalo si prefieres un proceso separado y **NO** activas `AUTOMATION_AUTO_DISPATCH` en FastAPI. No ejecutes los dos simultáneamente.

El archivo importable de n8n y sus requisitos SMTP/HMAC se explican en [automation/README.md](../automation/README.md).

## Machine Learning vs Tutor IA

- **LLM/Ollama**: genera una pista pedagógica contextual para un ejercicio; un validador comprueba la salida.
- **Reglas de adaptación**: dan pistas, calculan progreso y generan alertas comprobables incluso sin un modelo entrenado.
- **ML predictivo**: módulo separado que estima futuras dificultades. Los modelos sintéticos del repositorio son `CANDIDATE` y no deben usarse como si estuvieran aprobados en aulas reales.
- **n8n**: envía notificaciones; no entrena ni reemplaza al tutor.

## Seguridad y limitaciones

- Los nombres, DNI y respuestas del estudiante no se envían a n8n. Tampoco se incluye la respuesta correcta en el prompt del tutor.
- Los modelos LLM pueden fallar o dar pistas incorrectas: el filtro y el fallback reducen riesgos, pero no reemplazan la revisión educativa.
- El flujo completo con una instalación física de Ollama y el envío SMTP necesitan una prueba en el equipo y servidor reales de la institución.
- Antes de desplegar en Render, resolver la persistencia de SQLite efímera, respaldar los datos y verificar credenciales.

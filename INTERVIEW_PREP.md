# Guion de entrevista técnica — Integraciones & IA (Real Estate, Nordelta)

Notas para prepararte antes de la entrevista, basadas en el JD que te pasaron
y en las decisiones reales que tomé al construir `PropLeads Integration Hub`.
La idea es que puedas explicar el *por qué* de cada decisión, no solo el *qué*.

## 1. Cómo presentar el proyecto en 60 segundos

"Armé un pipeline de integración que simula exactamente lo que pide el
puesto: un webhook recibe un lead inmobiliario de un portal externo, lo
publica en una cola de RabbitMQ para no bloquear al que lo envía, un worker
lo procesa de forma asíncrona —matchea contra un catálogo de propiedades con
similitud semántica y lo clasifica con un LLM— y lo guarda en MongoDB,
exponiéndolo por REST y GraphQL. Lo hice dockerizado, con CI en GitHub
Actions y tests que no dependen de servicios reales corriendo."

## 2. Preguntas probables y cómo responderlas

**"¿Por qué cola en vez de procesar el lead directo en el webhook?"**
Porque el emisor (portal/formulario) no debería esperar a que termine el
matching + la llamada al LLM — son operaciones lentas y pueden fallar. Con
cola, el webhook responde rápido (202 Accepted) y el procesamiento real pasa
en el worker, con reintentos si algo falla (`ack`/`nack` en `app/queue.py`).

**"¿Por qué RabbitMQ y no Kafka?"**
RabbitMQ resuelve bien el caso de "cola de tareas" (un mensaje, un
consumidor, reintentar si falla) que es exactamente el patrón de un lead
entrante. Kafka brilla cuando necesitás replay de eventos o múltiples
consumidores independientes leyendo el mismo stream (ej. analytics +
notificaciones + CRM leyendo el mismo evento) — es más log distribuido que
cola de tareas. Si el puesto lo requiere, el contrato de `app/queue.py`
(`publish`/`consume`) es el mismo; cambiaría la implementación interna.

**"¿Por qué TF-IDF y no embeddings con un modelo transformer?"**
Es una decisión consciente, no una limitación: TF-IDF (scikit-learn) es
instantáneo, determinístico, no requiere descargar un modelo ni GPU, y para
catálogos chicos/medianos con vocabulario específico (barrios, tipos de
propiedad) funciona muy bien. Dejé el motor de embeddings
(`sentence-transformers`) como implementación intercambiable
(`EmbeddingMatcher` en `app/matching.py`, mismo contrato) para cuando la
calidad semántica lo justifique — es el patrón Strategy. Podés defender las
dos: sabés cuándo usar cada una y por qué, que es lo que evalúan realmente.

**"¿Cómo testeás algo que depende de un LLM externo?"**
No lo testeo pegándole a la API real: `classify_lead` tiene un fallback
heurístico que se activa sin `ANTHROPIC_API_KEY`, así que los tests (y el
CI) corren sin costo, sin secretos y sin flakiness de red. En producción sí
pegaría a Claude; en tests, inyecto/mockeo. Mismo criterio con la cola
(`Depends` de FastAPI, overrideado en `test_webhook.py`) y con Mongo
(`mongomock-motor` en `test_graphql.py`).

**"¿Cómo manejarías esto si el volumen de leads fuera 100x más grande?"**
El cuello de botella sería el worker (matching + llamada al LLM son
CPU/latencia). Como está desacoplado por cola, escala horizontalmente:
levantar más réplicas del worker, todas compitiendo por la misma cola
(`prefetch_count=1` ya lo deja listo para eso). El catálogo de propiedades
para TF-IDF se recalcularía en un índice más eficiente (ej. Elasticsearch)
en vez de recomputar el vectorizer en memoria en cada arranque.

**"¿Por qué NoSQL (Mongo) para esto y no SQL?"**
El documento "lead" tiene forma variable (distintos portales mandan campos
distintos, los matches son un array anidado) y no necesita joins — encaja
bien con un modelo de documentos. Para el catálogo de propiedades o
reporting agregado sí usaría SQL (que es donde tengo más experiencia real:
Power BI + SQL Server en Concrete). Podés mostrar que elegís la DB según el
problema, no por dogma.

**"Contame de un bug real que encontraste armando esto."**
`app/matching.py` tenía `TfidfMatcher(Matcher)` heredando de una dataclass
sin decorar la subclase con `@dataclass` — Python no llamaba a
`__post_init__` de la subclase porque ese hook solo se inyecta en la clase
que efectivamente lleva el decorador, no en las hijas. Lo agarré porque el
test fallaba con `AttributeError: no attribute '_matrix'`. Es un buen
ejemplo de "el traceback te dice dónde se rompe, no por qué" — hay que
entender cómo funciona el decorador, no solo parchear el síntoma.

**"¿Cómo protegerías este webhook de que le manden datos truchos?"**
Con firma HMAC-SHA256 (`app/security.py`): si configurás `WEBHOOK_SECRET`,
el endpoint exige un header `X-Signature` con el hash del body crudo firmado
con ese secreto compartido — mismo patrón que usan Stripe y los portales
reales. Sin la variable, el endpoint no exige firma (modo dev), así que el
mismo código sirve para desarrollo y producción sin ifs desperdigados.

**"¿Realmente armaste la alternativa con Kafka o es un mock?"**
Es real: `app/queue_kafka.py` implementa el mismo contrato
(`publish_lead`/`consume_leads`) que la versión RabbitMQ, con
`kafka-python-ng`, y `app/queue.py` elige cuál cargar según `MESSAGE_BROKER`.
Se prueba con `docker compose --profile kafka up` usando Redpanda (Kafka-
compatible, un solo contenedor, sin Zookeeper). Los tests unitarios
(`tests/test_queue_kafka.py`) mockean `KafkaProducer`/`KafkaConsumer`, igual
criterio que con RabbitMQ: no dependen de un broker real corriendo.

De hecho esto me dio otro bug real para contar: el CI falló al agregar
Kafka aunque en mi máquina (Python 3.11) todos los tests pasaban. El runner
de GitHub Actions usa Python 3.12, y ahí `kafka-python` (el paquete
original, sin mantenimiento hace años) rompe el import
(`ModuleNotFoundError: kafka.vendor.six.moves`) — un bug de compatibilidad
específico de esa versión. Instalé Python 3.12 localmente para reproducir
el mismo error antes de tocar nada, y lo resolví migrando a
`kafka-python-ng`, el fork de la comunidad que sí se mantiene. Buen ejemplo
de "funciona en mi máquina" y por qué el CI tiene que fallar rápido cuando
el runtime de destino no es el que usás para desarrollar.

## 3. Puntos débiles reales — decí la verdad, no los escondas

- No tenés experiencia productiva con Kafka, MuleSoft/Zapier/Make (sí n8n,
  que es el equivalente de bajo código) ni con TensorFlow/PyTorch. Es
  honesto decir: "mi fuerte es integrar y consumir modelos vía API
  (Claude/Gemini) y automatizar con n8n; no entrené modelos desde cero, pero
  entiendo el flujo de embeddings y puedo aprender la herramienta puntual
  rápido — como hice acá con RabbitMQ y GraphQL para este proyecto."
- Tu experiencia "pre-IA" programando a mano es más chica que tu experiencia
  de analista de datos. Este proyecto es la prueba de que programás sin
  copiloto cuando hace falta — mencionalo así si preguntan.
- ERP: no conocés SAP/Dynamics/Odoo, pero sí Softland/Bejerman/Tango
  (conocimiento funcional real de cómo se integra un ERP con sistemas
  externos) — el concepto transfiere, la herramienta puntual se aprende.

## 4. Preguntas para hacerles vos

- ¿Qué plataformas/ERPs tienen que integrar hoy en el día a día?
- ¿El equipo de integraciones trabaja más con mensajería asíncrona (colas)
  o son mayormente llamadas síncronas request/response?
- ¿Qué parte de "IA aplicada a procesos de negocio" ya está en producción
  hoy, y qué está en etapa de prueba?

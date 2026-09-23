# PropLeads Integration Hub

Demo de integración de sistemas para real estate: un webhook recibe leads de
un portal/formulario externo, los encola, y un worker separado hace matching
semántico contra un catálogo de propiedades + clasificación con IA, guardando
todo en MongoDB. Se consulta por REST y GraphQL.

```
Portal externo ──POST /webhook/lead──▶ FastAPI ──publish──▶ RabbitMQ
                                                                 │
                                                          consume (worker)
                                                                 │
                                        scikit-learn TF-IDF ◀────┤
                                        (matching semántico)     │
                                                                 │
                                        Claude API / heurística ◀┤
                                        (clasificación hot/warm/cold)
                                                                 │
                                                                 ▼
                                                            MongoDB
                                                                 │
                                        GET /leads (REST) ◀──────┤
                                        POST /graphql ◀──────────┘
```

## Por qué este proyecto

Lo armé para cubrir, en un solo repo chico y corrible, las tecnologías que
pide un puesto de Integraciones & IA que mi perfil (BI/datos + agentes de IA
con Claude/n8n) no mostraba todavía:

| Requisito | Dónde está en el repo |
|---|---|
| Python | Todo el backend |
| REST | `app/main.py` (`/webhook/lead`, `/leads`) |
| GraphQL | `app/graphql_schema.py`, montado en `/graphql` |
| Webhooks (+ autenticación) | `POST /webhook/lead`, firma HMAC-SHA256 en `app/security.py` |
| Mensajería (cola) | `app/queue.py` — RabbitMQ (pika) por default, Kafka intercambiable (`app/queue_kafka.py`) |
| Bases de datos NoSQL | MongoDB (`app/db.py`, `motor`/`pymongo`) |
| IA/ML: scikit-learn | `app/matching.py` — `TfidfVectorizer` + cosine similarity |
| IA/ML: embeddings/transformers | `app/matching.py` — `EmbeddingMatcher` (sentence-transformers, opcional) |
| Integración de modelos LLM | `app/llm.py` — Claude API con fallback heurístico testeable |
| Docker | `Dockerfile`, `docker-compose.yml` |
| CI/CD | `.github/workflows/ci.yml` (lint + tests en cada push) |
| Testing/QA | `tests/` (pytest, mocks de LLM/cola/DB) |
| OpenAPI/Swagger | autogenerado por FastAPI en `/docs` |
| Logging estructurado | `app/logging_conf.py` (JSON logs) |

SQL/BI (Power BI, SQL Server) ya está demostrado en otro proyecto del
portfolio (Data Lab), así que acá no se repite.

**Demo interactiva sin instalar nada:** hay una reimplementación en JS
vanilla del pipeline completo (mismo TF-IDF y misma heurística de
clasificación) corriendo en el [portfolio](https://enemeache.github.io/IMH-Porfolio-Personal/)
— útil para mostrar el flujo sin depender de Docker.

## Cómo correrlo

```bash
cp .env.example .env
docker compose up --build
```

- API + Swagger: http://localhost:8000/docs
- GraphQL playground: http://localhost:8000/graphql
- RabbitMQ management: http://localhost:15672 (guest/guest)

Probar el flujo completo:

```bash
curl -X POST http://localhost:8000/webhook/lead \
  -H "Content-Type: application/json" \
  -d '{
        "source": "web_form",
        "full_name": "Juana Perez",
        "email": "juana@example.com",
        "message": "Busco una casa con pileta para mi familia, tengo que mudarme urgente",
        "budget_usd": 350000
      }'
```

El worker lo consume de la cola, calcula matches contra `data/properties_seed.json`,
lo clasifica y lo guarda. Después:

```bash
curl http://localhost:8000/leads
```

Sin `ANTHROPIC_API_KEY` configurada, la clasificación cae a una heurística
local (ver `app/llm.py`) — el pipeline completo funciona igual, sin costo ni
llave, lo cual también es a propósito: así corre en CI sin secretos.

## Tests

```bash
pip install -r requirements.txt
pytest -v
```

Los tests no requieren Docker ni servicios reales corriendo: la cola y la
clasificación LLM se mockean/inyectan (`Depends` en FastAPI, `monkeypatch` en
pytest), y Mongo se simula con `mongomock-motor`.

## Motor de matching intercambiable

`app/matching.py` define dos implementaciones con la misma interfaz
(Strategy pattern):

- `TfidfMatcher` (default): scikit-learn, instantáneo, sin descargas — el
  que corre en CI y en la demo.
- `EmbeddingMatcher` (opcional): sentence-transformers, mejor calidad
  semántica. Se activa con `EMBEDDING_ENGINE=sentence-transformers` en
  `.env` (requiere descomentar `sentence-transformers` en `requirements.txt`).

## Autenticación del webhook (HMAC)

Si se configura `WEBHOOK_SECRET`, `POST /webhook/lead` exige un header
`X-Signature` con el HMAC-SHA256 (hex) del body crudo firmado con ese
secreto — el mismo patrón que usan los portales reales (y Stripe) para que
solo el emisor legítimo pueda publicar leads. Sin la variable configurada,
el endpoint no exige firma (modo dev). Ver `app/security.py`.

```bash
python -c "import hmac,hashlib; print(hmac.new(b'supersecreto', b'{\"source\":\"web_form\",...}', hashlib.sha256).hexdigest())"
curl -X POST http://localhost:8000/webhook/lead \
  -H "Content-Type: application/json" -H "X-Signature: <firma calculada>" \
  -d '{"source":"web_form", ...}'
```

## Motor de mensajería intercambiable

Igual patrón Strategy que el matching: `app/queue.py` es una fachada que
elige la implementación según `MESSAGE_BROKER`:

- `rabbitmq` (default, `app/queue_rabbitmq.py`): resuelve bien "cola de
  tareas" — un mensaje, un consumidor, reintentos con ack/nack.
- `kafka` (`app/queue_kafka.py`, kafka-python): tiene sentido cuando varios
  consumidores independientes necesitan leer el mismo stream de eventos.

Para levantar la variante Kafka (usa [Redpanda](https://redpanda.com), un
solo contenedor compatible con el protocolo Kafka, sin Zookeeper):

```bash
docker compose --profile kafka up --build redpanda
# y en .env: MESSAGE_BROKER=kafka, KAFKA_BOOTSTRAP_SERVERS=localhost:9092
```

## Panel en Next.js

`dashboard/` tiene un panel mínimo (Next.js 15 + App Router) que consume
`POST /graphql` para listar leads y `POST /webhook/lead` para cargar uno
nuevo — ver `dashboard/README.md` para correrlo.

## Roadmap / próximos pasos

- [ ] Deploy real en un cloud (Render/Fly.io/AWS) con el compose adaptado
- [x] Reemplazar RabbitMQ por Kafka como alternativa (mismo contrato en `app/queue.py`)
- [x] Autenticación en el webhook (HMAC signature, como hacen los portales reales)
- [x] Panel simple en Next.js consumiendo la API GraphQL

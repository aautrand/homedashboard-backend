# Configuration

All configuration comes from environment variables. `.env.example` lists them.

For local work, copy it to `.env` in the repository root and fill it in. The
app (`app.py`) and Alembic (`alembic/env.py`) both load that file on start.
`.env` is gitignored — never commit it. In a deployment, pass real environment
variables instead.

## Required to start

| Variable | Purpose |
|---|---|
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | PostgreSQL connection |
| `RABBITMQ_HOST`, `RABBITMQ_USER`, `RABBITMQ_PASSWORD` | RabbitMQ connection. The app connects at startup and will not start without it |

## Per feature

Everything below is only needed for the features that use it.

### Calendar

| Variable | Purpose |
|---|---|
| `CALDAV_ICLOUD_URL` | CalDAV server URL |
| `APPLE_USER` | Apple ID |
| `APPLE_DASHBOARD_SECRET` | An app-specific password, not the Apple ID password |
| `MAIN_CALENDAR` | Name of the calendar to read. A calendar named `Chores` is read alongside it |

### Weather

| Variable | Purpose |
|---|---|
| `OPEN_WEATHER_API_KEY` | OpenWeatherMap API key |
| `LAT_LONG` | Home location as `"lat,long"` |

### AI

| Variable | Default | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Claude: the voice agent and math worksheets. `ANTHROPIC_KEY` is accepted as a fallback |
| `ANTHROPIC_WORKSPACE_ID` | — | Only for service-account keys, which are not tied to one workspace. Sent as the `anthropic-workspace-id` header |
| `OPENAI_API_KEY` | — | Speech-to-text |
| `OPENAI_STT_MODEL` | `gpt-4o-transcribe` | Transcription model |
| `OLLAMA_HOST` | `http://localhost:11434` | Local Ollama server for `POST /ai/message` |

### Storage (MinIO)

| Variable | Default | Purpose |
|---|---|---|
| `MINIO_ENDPOINT` | `http://localhost:9000` | Server URL; `https://` enables TLS |
| `MINIO_BUCKET` | `printer-images` | Default bucket |
| `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY` | `minioadmin` | Credentials |
| `MINIO_EVENT_TOKEN` | — | Bearer token the bucket-notification webhook must present. Unset means the webhook rejects every call |

### Recipes

| Variable | Default | Purpose |
|---|---|---|
| `TANDOOR_URL` | `http://localhost:8040` | Tandoor server |
| `TANDOOR_API_TOKEN` | — | Tandoor API token |

### Printing and locale

| Variable | Default | Purpose |
|---|---|---|
| `RECEIPT_WIDTH` | `48` | Printer columns: 48 for 80mm paper, 32 for 58mm. Must match the printer or centred text drifts. **Set this as a real environment variable** — it is read before `.env` is loaded |
| `TIMEZONE` | server time | IANA name such as `America/Denver`. Used for the time the voice agent is told and the timestamp on its printed replies. Unset means server time, which is UTC in the container |
| `SELF_HOST` | `localhost` | Host that printed QR codes point back to |

# Development

## Prerequisites

- Python 3.11 or newer (the container image uses 3.12)
- [Poetry](https://python-poetry.org/)
- PostgreSQL 16
- RabbitMQ
- Optional, per feature: MinIO, a Tandoor server, Ollama, and API keys for
  Anthropic, OpenAI and OpenWeatherMap

## Setup

```bash
poetry install --no-root --with dev
cp .env.example .env
```

Fill in `.env` — at minimum the `DB_*` and `RABBITMQ_*` values. See
[configuration.md](configuration.md).

Create the tables:

```bash
alembic upgrade head
```

## Running

```bash
# the way production runs it
gunicorn --bind 0.0.0.0:8050 --timeout 180 app:app

# or Flask's development server
FLASK_APP=app.py flask run --port 8050
```

Then `curl http://localhost:8050/info` should return the version.

### Docker

```bash
make build      # docker compose build
make run        # docker compose up
```

Compose starts the app on port 8050 and a PostgreSQL 16 container named `db`
(user `dashboard_user`, password `dashboard_password`, database `dashboard`).
The repository is mounted into the container, so the app reads your `.env`;
point `DB_HOST` at `db`.

Compose does not start RabbitMQ. Run one separately and set `RABBITMQ_HOST`,
or the app will exit on startup.

## Make targets

| Target | Does |
|---|---|
| `make test` | Runs the test suite |
| `make format` | `black` + `isort` |
| `make format-check` | Checks formatting without changing files |
| `make lint` / `make lint-fix` | `ruff check`, optionally with fixes |
| `make security` | `bandit` over `dashboard/` |
| `make check` | `format-check`, `lint-fix`, `test`, `security` |
| `make push` | `make check`, then pushes the current branch |
| `make hooks` | Enables the pre-push secret scan |
| `make build` / `make run` | Docker Compose build / up |

## Tests

```bash
make test
python -m pytest tests/audio/test_blueprint.py -v
python -m pytest tests/audio/test_blueprint.py::TestAudioUploadEndpoint::test_upload_audio_success -v
```

`tests/` mirrors `dashboard/src/`. The tests need no database, broker or
network — everything external is mocked.

### Patterns

**Route tests** build a bare Flask app, register one blueprint and inject a
mock session:

```python
@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    return app

@pytest.fixture
def client(app, mock_db):
    app.register_blueprint(blueprint)

    @app.before_request
    def inject_db():
        request.db = mock_db

    return app.test_client()
```

**Manager tests** pass `MagicMock()` as the session and assert on ORM calls
(`db.add`, `db.commit`, `db.get`).

**Agent tests** drive `create_agent` with a scripted fake chat model whose
`bind_tools` returns itself (`tests/ai/agents/test_home_agent.py`), so no model
is called.

### Gotchas

- Posting an empty JSON body: send `data=json.dumps({})` with
  `content_type="application/json"`. Flask answers 400 to a truly empty body
  with a JSON content type.
- Code that reads `current_app` (`RabbitMQClient`, `OpenWeatherClient`): use a
  real app context. Patching the `current_app` proxy does not work cleanly.
- Some routes and all client factories import lazily inside functions. Patch
  the module where the name is defined, not the module that calls it.
- Read keyword arguments from mocks with `call_args.kwargs["body"]`, not by
  position.

## Database migrations

```bash
alembic upgrade head                                  # apply
alembic revision --autogenerate -m "add foo table"    # create
```

`alembic/env.py` imports every model module so autogenerate sees the whole
schema. **When you add a model file, add its import there**, or autogenerate
will not notice the new table.

## Adding things

### An endpoint

1. Put the rule in a manager method (`Manager(db)`), with a manager test.
2. Add a thin route that builds the manager from `request.db`.
3. Add a route test.
4. Document it in [api-reference.md](api-reference.md) and the matching guide.

### A capability for the voice agent

1. Add the method to a manager or service first.
2. If it needs a new service, add it to `HomeServices` and
   `build_home_services()` in `ai/agents/home_services.py`.
3. Add a tool in `ai/agents/home_tools.py` that calls that one method and
   returns text or JSON. The docstring is what the model reads — say when to
   use the tool.
4. If the tool prints on its own, add its name to `PRINTING_TOOLS` so the
   reply is not printed as well.

### A dependency

```bash
poetry add <package>
```

## Continuous integration

`.forgejo/workflows/ci.yml` runs on every push (except to `main`) and on pull
requests into `dev` and `main`:

| Job | Runs |
|---|---|
| `format-check` | `isort --check`, `black --check` |
| `test` | `pytest tests/` |
| `security` | `bandit` |
| `secrets` | `gitleaks` over the full history |

## Keeping secrets out of the repository

The repository is mirrored publicly. `make hooks` enables
`.githooks/pre-push`, which blocks a push when the outgoing commits contain a
secret (via [gitleaks](https://github.com/gitleaks/gitleaks), which must be
installed) or a private network detail such as a LAN address or a home
directory path. The CI `secrets` job is the backstop.

Keep hosts, addresses, credentials, coordinates and calendar names in
environment variables, not in code or docs.

## Releases and deployment

The version lives in the `version` file and is served by `GET /info`.

- **`Jenkinsfile`** — release. Takes a `VERSION` parameter, runs `bandit`,
  writes and commits the `version` file, builds the image with Podman and
  pushes it to a container registry.
- **`Jenkinsfile.deploy`** — deploy. Lists the image tags in the registry, asks
  which to deploy, rewrites the image in the systemd container unit and
  restarts the `homedashboard-be` user service.

Registry and Git host addresses come from Jenkins global environment
variables, so none are stored here.

Branches: work lands on `dev`; `main` is updated by merging `dev`.

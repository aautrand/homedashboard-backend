# Home Dashboard Backend

The backend for a home dashboard whose main output is a **receipt printer**.

Every morning it prints a paper slip with the day on it: a quote, the weather,
calendar events, chores, reminders, todos and something to study. During the
day you can talk to it — a Raspberry Pi records a voice request, an AI agent
works out what you meant, acts on it ("add milk to my todo list", "what's on
tomorrow?", "print the ingredients for the lasagna") and prints the answer.

There is no screen and no speaker. Paper is the user interface.

```zzmermaid
flowchart LR
    pi["Raspberry Pi<br/>(microphone)"] -- audio --> api
    sched["Scheduler<br/>(cron, n8n, ...)"] -- HTTP --> api
    ui["Dashboard UI /<br/>curl / scripts"] -- HTTP --> api

    api["<b>This project</b><br/>Flask API"]

    api -- print jobs --> mq[(RabbitMQ)]
    mq --> printer["Printer service<br/>+ receipt printer"]

    api --- db[(PostgreSQL)]
    api --- ext["iCloud calendar · OpenWeatherMap<br/>Anthropic · OpenAI · Tandoor · MinIO"]
```

This repository is only the API in the middle. The device that records audio,
the scheduler that triggers the morning print and the service that drives the
physical printer are separate pieces that talk to it over HTTP and RabbitMQ.

## What it does

| Feature | In short | Guide |
|---|---|---|
| **Daily receipt** | One request gathers quotes, weather, calendar, routines, reminders, todos, a study subject and quiz questions into one printout. | [daily-receipt.md](docs/guides/daily-receipt.md) |
| **Voice assistant** | Audio in → transcription → tool-using Claude agent → printed reply. | [voice-assistant.md](docs/guides/voice-assistant.md) |
| **Todos and calendar** | A todo list, plus iCloud calendar events synced into the database and printed shortly before they start. | [todos-and-calendar.md](docs/guides/todos-and-calendar.md) |
| **Routines, reminders, checklists** | Recurring chores on a schedule, standing reminders, and reusable printable checklists. | [routines-reminders-checklists.md](docs/guides/routines-reminders-checklists.md) |
| **Flashcards and quizzes** | Flashcards printed as pop quizzes; scores decide when a card counts as learned. Subjects resurface on a spaced-repetition schedule. | [flashcards-and-quizzes.md](docs/guides/flashcards-and-quizzes.md) |
| **Quotes** | A rotating quote and an optional pinned one at the top of the daily receipt. | [quotes.md](docs/guides/quotes.md) |
| **Recipes** | Look up recipes in a self-hosted Tandoor server and print ingredient lists as shopping checklists. | [recipes.md](docs/guides/recipes.md) |
| **Printing** | Print arbitrary text, and the message formats the printer service consumes. | [printing.md](docs/guides/printing.md) |

Each guide explains what the endpoints do and shows example requests. Every
endpoint is also listed in one table in the
[API reference](docs/api-reference.md).

## A voice request, end to end

1. The Pi records "add milk to my todo list" and uploads the audio to
   `POST /ai/audio/upload`.
2. The recording is stored in MinIO and transcribed by OpenAI.
3. The transcription goes to a Claude agent that has tools for todos, calendar,
   weather, quotes, flashcards, recipes and the printer. It calls `add_todo`.
4. The exchange is saved to PostgreSQL.
5. The agent's reply ("Added milk to your todo list.") is published to
   RabbitMQ, and the printer service prints it.

## Quick start

You need Python 3.11+, [Poetry](https://python-poetry.org/), and a reachable
PostgreSQL and RabbitMQ. The other services are only needed for the features
that use them.

```bash
poetry install --no-root --with dev

cp .env.example .env        # then fill in at least DB_* and RABBITMQ_*
alembic upgrade head        # create the tables

gunicorn --bind 0.0.0.0:8050 --timeout 180 app:app
```

Check that it is up, then try a request:

```bash
curl http://localhost:8050/info
# {"version": "2.5.0"}

curl -X POST http://localhost:8050/calendar/todo \
  -H 'Content-Type: application/json' \
  -d '{"title": "Buy milk"}'
```

See [development.md](docs/development.md) for the full setup, including Docker,
and [configuration.md](docs/configuration.md) for every environment variable.

> **Note** The API has no authentication (one webhook aside). It is built to
> run on a trusted home network, not on the public internet.

## Documentation

| Document | What is in it |
|---|---|
| [Architecture](docs/architecture.md) | How the system fits together: components, code layout, request lifecycle, the main flows. |
| [Design notes](docs/design.md) | Why it is built this way, and the trade-offs. |
| [Data model](docs/data-model.md) | Database tables and how they relate. |
| [Configuration](docs/configuration.md) | Environment variables. |
| [Development](docs/development.md) | Setup, tests, formatting, migrations, CI and releases. |
| [API reference](docs/api-reference.md) | Every endpoint in one place. |
| [Guides](docs/README.md#guides) | How to use each feature, with example requests. |

## Tech stack

Python · Flask · SQLAlchemy 2 · Alembic · PostgreSQL · RabbitMQ (pika) ·
LangChain / LangGraph · Anthropic Claude · OpenAI speech-to-text · MinIO ·
CalDAV · Gunicorn

# Documentation

Start with the [project README](../README.md) for an overview.

## Understanding the project

- [Architecture](architecture.md) — components, code layout, request
  lifecycle and the main flows.
- [Design notes](design.md) — the reasoning behind the structure and its
  trade-offs.
- [Data model](data-model.md) — database tables and relationships.

## Running and changing it

- [Configuration](configuration.md) — environment variables.
- [Development](development.md) — setup, tests, formatting, migrations, CI
  and releases.

## Using it

- [API reference](api-reference.md) — every endpoint in one table.

### Guides

One per feature: what the endpoints do and how to call them.

- [Daily receipt](guides/daily-receipt.md)
- [Voice assistant](guides/voice-assistant.md)
- [Todos and calendar](guides/todos-and-calendar.md)
- [Routines, reminders and checklists](guides/routines-reminders-checklists.md)
- [Flashcards and quizzes](guides/flashcards-and-quizzes.md)
- [Quotes](guides/quotes.md)
- [Recipes](guides/recipes.md)
- [Printing](guides/printing.md)
- [Other endpoints](guides/other-endpoints.md) — weather, audio storage,
  device events, math worksheets.

The examples use `curl` against `http://localhost:8050`. Replace the host with
wherever the backend runs.

# Design notes

Why the project is shaped the way it is and what was traded away. [architecture.md](architecture.md) describes the structure
itself.

## Principles

### Paper is the interface

The device has no screen or speaker, so every feature ends in a printout. That
drives several choices:

- Voice replies are printed, not spoken. Only the **reply** is printed, never
  the transcription — the user knows what they said.
- The agent is told to answer in a few short plain-text lines: receipt paper is
  48 columns wide and cannot render markdown.
- One request prints once. If the agent printed something itself, its reply is
  not printed on top of it.

### Business rules live in the backend, not in the agent

Each agent tool calls exactly one manager or service method and formats the
result. Rules such as "completing an already completed todo does nothing" live
in `TodoManager.complete_todo`, so the HTTP route and the voice assistant
cannot drift apart. Adding a capability means adding the method to a manager
first, then a thin tool on top.

The agent depends on a `HomeServices` container rather than on how each
service is built. Tests hand it stubs; tools never reach for `request` or
`current_app`.

### Printing is asynchronous and decoupled

The backend publishes JSON to RabbitMQ and returns. A separate service owns the
printer. The backend therefore runs anywhere, needs no USB or driver access,
and a slow or busy printer never blocks a request.

The cost is that the backend cannot see the printer — see
[Print delivery is best effort](#print-delivery-is-best-effort).

### Clients are swappable and config-free

External systems sit behind factory functions with lazy imports. The AI
clients go one step further: they take plain constructor arguments and read
neither `os.environ` nor `current_app`. `get_ai_client()` and
`get_chat_model()` in `ai/clients/base.py` are the only places that resolve
app config for them, which keeps the clients testable without an app context.

`ClaudeClient` and `OpenAITranscriptionClient` speak HTTP with `requests`
instead of vendor SDKs. The home agent is the one exception: it uses
`ChatAnthropic`, because a tool-calling loop resends its history on every step
and that is exactly what the LangChain chat model handles.

### Managers own the rules, routes stay thin

A manager takes a `Session` and nothing else, so a unit test passes a
`MagicMock` and asserts on ORM calls. Routes build managers from `request.db`.

## Decisions

### The current time goes in the user message

`HomeAgent.respond` prefixes each request with `Current local time: ...`
instead of putting the time in the system prompt. The system prompt stays
byte-identical between requests and therefore cacheable.

The time is reported in the `TIMEZONE` setting. Without it the server's clock
is used, which is UTC inside the container — "tomorrow" would then be wrong for
part of every day.

### Silence short-circuits the pipeline

The voice graph has one conditional edge: an empty transcription ends the run.
An accidental button press costs one transcription call and nothing else.

### Webhook deliveries are idempotent

MinIO can deliver the same bucket notification more than once.
`POST /ai/audio/events` checks `voice_queries` for the filename first and skips
recordings that were already answered. The webhook is also the only
authenticated endpoint: it requires `Authorization: Bearer $MINIO_EVENT_TOKEN`,
compared in constant time, and rejects everything when the token is unset.

### A print failure does not fail a voice request

By the time the reply is printed the agent has already acted and the exchange
is saved. If publishing the print job raises, the error is logged and the
request still succeeds.

### Quotes: exhaust the pool before repeating

The random quote is drawn from the quotes with the lowest `times_shown`, so
every quote appears once before any appears twice, while the order within a
round stays random.

The pinned quote is a flag on the same table rather than a separate concept.
It is excluded from the random draw and never advances `times_shown`: it prints
every day and would otherwise distort the ordering. Pinning goes through
dedicated endpoints so that only one quote is ever pinned; the generic update
endpoint accepts `text`, `author` and `active` only.

### Centring with spaces

The `text_print` message carries lines of text and no alignment instructions,
so quotes are centred by padding with leading spaces to `RECEIPT_WIDTH`
columns. This only looks right when `RECEIPT_WIDTH` matches the printer's real
column count and the printer service preserves leading whitespace.

### Receipts are ordered dicts

`ReceiptFormatter.build()` returns a dict keyed by section title. Section order
is insertion order, and two sections cannot share a title. The quote block at
the top of the daily receipt uses the empty title `""`.

### Routines use a three-field date pattern

Routines recur by day, not by minute, so their schedule is a cut-down cron
expression: `day_of_week day_of_month month`. All three fields must match.
"Every N days" does not fit that model, so a routine can use `interval_days`
instead, tracked through `last_shown_date`.

### Cards have to earn their way into quizzes

A new card starts unreviewed and is left out of quizzes. Updating it marks it
reviewed. This matters because the voice assistant can create flashcards: an
AI-written card is checked by a person before it shows up on paper.

A card leaves the quiz pool once it is answered correctly three times in a row
(`QuizManager.MASTERY_THRESHOLD`), which sets `grokked`.

### Tandoor stays behind a mapping layer

`TandoorClient` converts Tandoor's JSON into the project's own dataclasses
(`RecipeSummary`, `Recipe`, `Step`, `Ingredient`). Nothing else knows Tandoor's
field names, so an API change touches one file. Recipes are read-only from
here.

### Long worker timeout

Gunicorn runs with `--timeout 180`. Voice requests chain a transcription and a
multi-step agent run and outlast the 30-second default.

## Trade-offs

### No authentication

Only the MinIO webhook checks a token. Every other endpoint is open, on the
assumption that the service is reachable from a trusted home network only.

### Print delivery is best effort

- There are no publisher confirms and no acknowledgement from the printer. A
  "print failure" means the publish to RabbitMQ raised. An offline or jammed
  printer is invisible to the backend.
- Queues are declared non-durable, so queued jobs are lost if RabbitMQ
  restarts.

### RabbitMQ is required at startup

`create_app()` connects to RabbitMQ and keeps one client for the life of the
worker. If the broker is down the app does not start. A dropped connection is
reopened on the next publish.

### Reading the daily receipt changes state

`GET /tasks/print` advances the quote rotation and marks routines, reminders,
todos and the study subject as shown. Calling it twice in one day can skip an
every-N-days routine that was due. It is a `GET` for the convenience of simple
schedulers, not because it is safe to repeat.

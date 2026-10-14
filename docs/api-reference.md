# API reference

Every endpoint, grouped by URL prefix. The [guides](README.md#guides) explain
how to use them and show example requests.

## Conventions

- Base URL: `http://<host>:8050`.
- Request and response bodies are JSON unless noted. Send
  `Content-Type: application/json` with a body.
- No authentication, except `POST /ai/audio/events`.
- Errors are `{"error": "<message>"}` with a 4xx or 5xx status. A missing
  record is a 404; a missing required field is a 400.
- **Prints** in the tables below means the call queues a print job.

## Service

| Method | Path | Description |
|---|---|---|
| GET | `/info` | Returns `{"version": "..."}`. Useful as a health check. |

## Daily receipt and worksheets — `/tasks`

Guide: [daily-receipt.md](guides/daily-receipt.md),
[other-endpoints.md](guides/other-endpoints.md#math-worksheets)

| Method | Path | Description |
|---|---|---|
| GET | `/tasks/print` | Builds and **prints** the daily receipt. Changes state — see the guide. |
| GET | `/tasks/math-problems` | Generates a math worksheet from `{"prompt": ...}` and **prints** it. |

## Voice assistant — `/ai`

Guide: [voice-assistant.md](guides/voice-assistant.md)

| Method | Path | Description |
|---|---|---|
| POST | `/ai/agent` | Sends `{"message": ...}` to the home agent as text. Does not print the reply. |
| POST | `/ai/audio/upload` | Multipart `file`. Stores, transcribes, runs the agent and **prints** the reply. |
| POST | `/ai/audio/events` | MinIO bucket-notification webhook. Requires `Authorization: Bearer <MINIO_EVENT_TOKEN>`. **Prints** replies. |
| POST | `/ai/message` | Sends `{"message": ...}` to a local Ollama model. No tools, no printing. |

## Audio storage — `/audio`

Guide: [other-endpoints.md](guides/other-endpoints.md#audio-storage)

These only store or transcribe. They do not run the agent.

| Method | Path | Description |
|---|---|---|
| POST | `/audio/upload` | Multipart `file` → stored in MinIO. |
| POST | `/audio/stream?ext=<ext>` | Raw audio bytes in the body → stored in MinIO. |
| WS | `/audio/ws` | Binary chunks over a WebSocket → stored in MinIO once the client stops sending. |
| POST | `/audio/transcribe` | `{"filename": ...}` → transcription of a stored file. |

## Calendar and todos — `/calendar`

Guide: [todos-and-calendar.md](guides/todos-and-calendar.md)

| Method | Path | Description |
|---|---|---|
| POST | `/calendar/todo` | Create a todo. Body: `title`, optional `active`. |
| GET | `/calendar/todo` | List todos. Optional `?active=true\|false`. |
| GET | `/calendar/todo/<id>` | Get one todo. |
| PUT | `/calendar/todo/<id>` | Update a todo. Setting `active` to `false` on an open todo **prints** it. |
| DELETE | `/calendar/todo/<id>` | Delete a todo. |
| POST | `/calendar/todo/<id>/print` | **Prints** one todo. |
| GET | `/calendar/events` | Today's events, fetched live from CalDAV. |
| POST | `/calendar/sync` | Sync today's events from CalDAV into the database. |
| GET | `/calendar/events/stored` | Today's events from the database. |
| POST | `/calendar/events/print-next` | **Prints** the next timed event. |
| POST | `/calendar/events/notify-upcoming` | Syncs, then **prints** events starting soon that were not printed yet. Optional `?minutes=`. |
| GET | `/calendar/text` | A month as plain text. |

## Learning — `/learning`

Guides: [routines-reminders-checklists.md](guides/routines-reminders-checklists.md),
[flashcards-and-quizzes.md](guides/flashcards-and-quizzes.md)

### Routines

| Method | Path | Description |
|---|---|---|
| POST | `/learning/routines` | Create. Body: `title` and `schedule_pattern` or `interval_days`; optional `priority`, `active`. |
| GET | `/learning/routines` | List all, by priority. |
| GET | `/learning/routines/today` | Routines due today. |
| GET | `/learning/routines/<id>` | Get one. |
| PUT | `/learning/routines/<id>` | Update. |
| DELETE | `/learning/routines/<id>` | Delete. |

### Reminders

| Method | Path | Description |
|---|---|---|
| POST | `/learning/reminder` | Create. Body: `title`, optional `active`. |
| GET | `/learning/reminder` | List. Optional `?active=true\|false`. |
| GET | `/learning/reminder/<id>` | Get one. |
| PUT | `/learning/reminder/<id>` | Update. |
| DELETE | `/learning/reminder/<id>` | Delete. |
| POST | `/learning/reminder/<id>/print` | **Prints** one reminder. |

### Checklists

| Method | Path | Description |
|---|---|---|
| POST | `/learning/checklists` | Create. Body: `title`, optional `items` (list of strings). |
| GET | `/learning/checklists` | List. |
| GET | `/learning/checklists/<id>` | Get one. |
| PUT | `/learning/checklists/<id>` | Update `title` and/or `items`. |
| DELETE | `/learning/checklists/<id>` | Delete. |
| POST | `/learning/checklists/<id>/print` | **Prints** the checklist and its notes. |
| POST | `/learning/checklists/<id>/notes` | Add a note. Body: `content`. |
| GET | `/learning/checklists/<id>/notes` | List notes in order. |
| PUT | `/learning/checklists/<id>/notes/reorder` | Reorder. Body: `{"order": [note ids]}`. |
| GET | `/learning/checklists/<id>/notes/<note_id>` | Get one note. |
| PUT | `/learning/checklists/<id>/notes/<note_id>` | Update a note. |
| DELETE | `/learning/checklists/<id>/notes/<note_id>` | Delete a note. |

### Cards

| Method | Path | Description |
|---|---|---|
| POST | `/learning/cards` | Create. Body: `title`, `content`. |
| POST | `/learning/cards/batch` | Create several. Body: a list of `{title, content}`. |
| GET | `/learning/cards` | List. Optional `?reviewed=true\|false`. |
| GET | `/learning/cards/<id>` | Get one. |
| PUT | `/learning/cards/<id>` | Update and mark as reviewed. Optional `topic_ids`. |
| DELETE | `/learning/cards/<id>` | Delete. |
| GET | `/learning/problem` | Cards as a list of JSON strings. |

### Quizzes

| Method | Path | Description |
|---|---|---|
| POST | `/learning/print/pop-quiz` | Create and **print** a quiz. Optional `num_questions`, `include_answers`. |
| GET | `/learning/quiz` | List quizzes, newest first. |
| GET | `/learning/quiz/<id>` | A quiz with its questions, cards and recorded answers. |
| POST | `/learning/print/quiz/<id>` | **Reprints** a quiz. Optional `include_answers`, `randomize`. |
| POST | `/learning/print/quiz/<id>/answers` | **Prints** the answer sheet. |
| POST | `/learning/quiz/<id>/question/<question_id>/answer` | Record one score. Body: `score` (0, 1 or 2). |
| POST | `/learning/quiz/<id>/answers` | Record several scores. Body: `{"answers": [{question_id, score}]}`. |

### Subjects and topics

| Method | Path | Description |
|---|---|---|
| POST | `/learning/subjects` | Create. Body: `name`. |
| GET | `/learning/subjects` | List. `?study_active=true` for those in the study rotation. |
| GET | `/learning/subjects/<id>` | Get one. |
| PUT | `/learning/subjects/<id>` | Update. |
| POST | `/learning/subjects/<id>/study/enable` | Add to the study rotation. |
| POST | `/learning/subjects/<id>/study/disable` | Remove from the study rotation. |
| GET | `/learning/subjects/study/today` | The subject due for study today. |
| GET | `/learning/topics` | List topics. |
| POST | `/learning/topics` | Create. Body: `name`, `subject_id`, optional `parent_topic_id`. |

## Quotes — `/quotes`

Guide: [quotes.md](guides/quotes.md)

| Method | Path | Description |
|---|---|---|
| POST | `/quotes` | Create. Body: `text`, optional `author`, `active`. |
| GET | `/quotes` | List. Optional `?active=true\|false`. |
| GET | `/quotes/<id>` | Get one. |
| PUT | `/quotes/<id>` | Update `text`, `author`, `active`. |
| DELETE | `/quotes/<id>` | Delete. |
| GET | `/quotes/pinned` | The pinned quote, or 404. |
| PUT | `/quotes/pinned` | Pin a quote. Body: `quote_id`. |
| POST | `/quotes/pinned/cycle` | Pin a different quote at random. |
| DELETE | `/quotes/pinned` | Unpin. |
| POST | `/quotes/reset-rotation` | Clear the shown history of every quote. |

## Recipes — `/recipes`

Guide: [recipes.md](guides/recipes.md)

| Method | Path | Description |
|---|---|---|
| GET | `/recipes` | List recipes. `?query=` filters by name. |
| GET | `/recipes/<id>` | One recipe with ingredients and steps. |
| POST | `/recipes/<id>/print-ingredients` | **Prints** the ingredients as a checklist. |

A Tandoor failure returns 502.

## Printing — `/prints`

Guide: [printing.md](guides/printing.md)

| Method | Path | Description |
|---|---|---|
| POST | `/prints/` | **Prints** lines of text. Body: `{"text": [lines]}`. |
| POST | `/prints/stream` | **Prints** line by line without cutting, or cuts the paper. |

## Weather — `/weather`

Guide: [other-endpoints.md](guides/other-endpoints.md#weather)

| Method | Path | Description |
|---|---|---|
| GET | `/weather/open-weather` | Current conditions plus today's forecast from OpenWeatherMap. |
| GET | `/weather/current` | Raw current observation from wttr.in. |

## Device events — `/data`

Guide: [other-endpoints.md](guides/other-endpoints.md#device-events)

| Method | Path | Description |
|---|---|---|
| POST | `/data/event` | Record that a device fired. Body: `{"id": "<device id>"}`. |

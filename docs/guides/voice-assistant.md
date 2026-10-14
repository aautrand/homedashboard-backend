# Voice assistant

Say something, get an answer on paper. A recording is transcribed, handed to
an AI agent that can act on the dashboard's data, and the agent's reply is
printed.

Needs `ANTHROPIC_API_KEY`; the audio endpoints also need `OPENAI_API_KEY` and
MinIO. See [configuration.md](../configuration.md).

## What you can ask

| Area | Examples |
|---|---|
| Todos | "Add milk to my todo list." · "What's on my list?" · "I did the milk one." |
| Calendar | "What's on tomorrow?" · "Do I have anything on Friday?" |
| Weather | "Do I need a jacket today?" |
| Quotes | "Add a quote: ..." · "Pin the one by Seneca." |
| Flashcards | "Make three flashcards about photosynthesis." |
| Recipes | "What goes in the lasagna?" · "Print the ingredients for the lasagna." |
| Printing | "Print my todo list." · "...and don't print anything." |

Loose references work. For "the milk one" the agent lists the todos and picks
the closest match; if nothing matches, or two match equally, it says so
instead of guessing.

Flashcards made this way start unreviewed and are kept out of quizzes until
you have checked them — see
[flashcards and quizzes](flashcards-and-quizzes.md#flashcards).

## Try it with text

The quickest way to test, with no audio involved:

```bash
curl -X POST http://localhost:8050/ai/agent \
  -H 'Content-Type: application/json' \
  -d '{"message": "add milk to my todo list"}'
```

```json
{
  "message": "add milk to my todo list",
  "response": "Added milk to your todo list."
}
```

The agent acts for real — that todo now exists. This endpoint does not print
the reply (an explicit "print ..." request still prints).

## Send a recording

This is what the Raspberry Pi does:

```bash
curl -X POST http://localhost:8050/ai/audio/upload \
  -F 'file=@request.m4a'
```

```json
{
  "status": "success",
  "filename": "audio/20261013_071502_a1b2c3d4.m4a",
  "url": "http://.../audio/20261013_071502_a1b2c3d4.m4a",
  "transcription": "Add milk to my todo list.",
  "llm_response": "Added milk to your todo list."
}
```

The call returns 201 after the whole pipeline has run:

1. The file is stored in MinIO.
2. It is transcribed.
3. The agent answers, using its tools.
4. The exchange is saved to the `voice_queries` table.
5. The reply is printed.

A recording with no speech stops after step 2: `llm_response` is `""`, and
nothing is saved or printed.

Requests can take a while — over a minute when the agent needs several steps.
Give the client a generous timeout.

## Or let MinIO trigger it

Instead of uploading to the backend, a device can write recordings straight
into MinIO and let a bucket notification start the pipeline.

Configure MinIO's webhook target to call `POST /ai/audio/events` with its
`auth_token` set to the value of `MINIO_EVENT_TOKEN`. MinIO then sends:

```bash
curl -X POST http://localhost:8050/ai/audio/events \
  -H "Authorization: Bearer $MINIO_EVENT_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"Records": [{"s3": {"bucket": {"name": "recordings"},
                           "object": {"key": "audio%2Fclip.wav"}}}]}'
```

```json
{
  "status": "ok",
  "processed": [
    {"filename": "audio/clip.wav", "transcription": "...", "llm_response": "..."}
  ]
}
```

- A missing or wrong token gets a 401. If `MINIO_EVENT_TOKEN` is unset, every
  call is rejected.
- A recording that was already answered is skipped, so a repeated notification
  does nothing.

## When the reply is printed

| Situation | Printed |
|---|---|
| A normal voice request | The reply, under a date-and-time title |
| You asked to print something ("print my todo list") | Only what you asked for — the reply is not printed as well |
| You said not to print ("...no printout") | Nothing |
| Text request via `/ai/agent` | Nothing, unless you asked to print something |
| Silent recording | Nothing |

The transcription is never printed.

If the print job cannot be queued, the request still succeeds: the action was
taken and the exchange saved. The backend cannot tell whether the printer
itself is online.

## Plain chat with a local model

`POST /ai/message` sends a message to a local Ollama model. It has no tools
and no access to dashboard data, and prints nothing.

```bash
curl -X POST http://localhost:8050/ai/message \
  -H 'Content-Type: application/json' \
  -d '{"message": "Explain spaced repetition in one sentence."}'
```

```json
{
  "status": "Message received and processed",
  "user_message": "Explain spaced repetition in one sentence.",
  "llm_response": "..."
}
```

## Adding a capability

See [development.md](../development.md#a-capability-for-the-voice-agent).

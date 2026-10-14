# Other endpoints

Smaller pieces that do not need a guide of their own.

## Health check

```bash
curl http://localhost:8050/info
# {"version": "2.5.0"}
```

## Weather

Both endpoints report on the location in `LAT_LONG`.

```bash
curl http://localhost:8050/weather/open-weather
```

Current conditions from OpenWeatherMap combined with the forecast for the next
24 hours, in metric units. Alongside OpenWeatherMap's own fields it adds:

| Field | |
|---|---|
| `daily_min_temp`, `daily_max_temp` | Low and high across the forecast, °C |
| `icons` | Weather icon codes for the forecast |

This is the same data the [daily receipt](daily-receipt.md) and the
[voice assistant](voice-assistant.md) use. Needs `OPEN_WEATHER_API_KEY`.

```bash
curl http://localhost:8050/weather/current
```

The raw current observation from [wttr.in](https://wttr.in/), which needs no
API key.

## Audio storage

These store or transcribe audio **without** running the voice assistant. To
have a recording answered, use
[`/ai/audio/upload`](voice-assistant.md#send-a-recording) instead.

Files are saved in MinIO as `audio/<timestamp>_<random id>.<ext>`.

### Upload a file

```bash
curl -X POST http://localhost:8050/audio/upload -F 'file=@clip.m4a'
```

```json
{"status": "success", "filename": "audio/20261013_071502_a1b2c3d4.m4a", "url": "http://..."}
```

### Upload a raw stream

For devices that send bytes as they record instead of a finished file. The
audio is the request body, and the format goes in `ext`:

```bash
curl -X POST 'http://localhost:8050/audio/stream?ext=wav' \
  -H 'Content-Type: application/octet-stream' \
  --data-binary @clip.wav
```

Allowed extensions: `mp3`, `m4a`, `wav`, `ogg`, `flac`, `aac`.

### Upload over a WebSocket

`ws://localhost:8050/audio/ws`

1. Optionally send a text message first to set the format:
   `{"ext": ".mp3"}`. The default is `.wav`.
2. Send the audio as binary messages.
3. Stop sending. After 30 seconds without a message the server stores what it
   received and replies with the same JSON as an upload, or
   `{"error": "..."}`.

### Transcribe a stored file

```bash
curl -X POST http://localhost:8050/audio/transcribe \
  -H 'Content-Type: application/json' \
  -d '{"filename": "clip.m4a"}'
# {"filename": "clip.m4a", "transcription": "..."}
```

`filename` is looked up in the MinIO bucket named `audio`. Needs
`OPENAI_API_KEY`.

## Device events

A minimal log for buttons and sensors: record that a device fired, with the
time.

```bash
curl -X POST http://localhost:8050/data/event \
  -H 'Content-Type: application/json' \
  -d '{"id": "doorbell"}'
# {"status": "ok", "event_id": 57}
```

`id` is any string that identifies the device. Events are written to the
`device_events` table.

## Math worksheets

Describe the practice problems you want; Claude writes them and a worksheet
is printed.

```bash
curl -X GET http://localhost:8050/tasks/math-problems \
  -H 'Content-Type: application/json' \
  -d '{"prompt": "5 problems on factoring quadratics, medium difficulty"}'
```

```json
{
  "status": "successful",
  "problems": [
    {"elements": [
      {"kind": "text", "content": "Factor the expression:"},
      {"kind": "image", "content": "problems/3f2a....png"}
    ]}
  ]
}
```

Note that this is a `GET` with a JSON body, hence the explicit `-X GET`.

What happens:

1. Claude generates the problems as JSON: a topic and a list of problems, each
   made of text and LaTeX elements.
2. Formulas are rendered to images and stored in MinIO.
3. The worksheet is printed: the topic as a heading, the numbered problems, a
   `____ / N` score line and a QR code.

In the response, each formula has become an `image` element whose `content` is
the image's path in MinIO, so a UI can show the same problems.

Needs `ANTHROPIC_API_KEY` and MinIO.

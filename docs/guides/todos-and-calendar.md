# Todos and calendar

## Todos

A simple list of one-off things to do. Open todos are printed on the
[daily receipt](daily-receipt.md) every morning until they are done.

### Add one

```bash
curl -X POST http://localhost:8050/calendar/todo \
  -H 'Content-Type: application/json' \
  -d '{"title": "Buy milk"}'
```

Returns 201 with the new todo, including its `id`.

### List them

```bash
curl http://localhost:8050/calendar/todo                # all
curl 'http://localhost:8050/calendar/todo?active=true'  # open
curl 'http://localhost:8050/calendar/todo?active=false' # done
curl http://localhost:8050/calendar/todo/7              # one
```

### Complete one

```bash
curl -X PUT http://localhost:8050/calendar/todo/7 \
  -H 'Content-Type: application/json' \
  -d '{"active": false}'
```

Completing an open todo this way also **prints it** — a small slip confirming
what was finished. Changing anything else (for example `title`) prints
nothing.

Completing a todo through the [voice assistant](voice-assistant.md) does not
print the todo; the assistant's reply is the confirmation.

### Print or delete one

```bash
curl -X POST   http://localhost:8050/calendar/todo/7/print
curl -X DELETE http://localhost:8050/calendar/todo/7
```

## Calendar

Events come from an iCloud calendar over CalDAV. iCloud stays the source of
truth: to add or change an event, edit the calendar. The backend reads the
calendar named in `MAIN_CALENDAR`, plus one named `Chores`.

There are two ways to read events.

| | Live | Stored |
|---|---|---|
| Endpoint | `GET /calendar/events` | `GET /calendar/events/stored` |
| Source | iCloud, right now | The database copy |
| Fresh as of | Now | The last sync |
| Calendars | `MAIN_CALENDAR` | `MAIN_CALENDAR` and `Chores` |

Both return today's events.

### Sync

```bash
curl -X POST http://localhost:8050/calendar/sync
```

```json
{"status": "ok", "sync_result": {"inserted": 2, "updated": 0, "deleted": 1, "total": 5}}
```

Copies today's events into the database: new ones are inserted, changed ones
updated, and ones removed from iCloud deleted. Printing the daily receipt and
checking for upcoming events both sync first, so you rarely need to call this
yourself.

### Print the next event

```bash
curl -X POST http://localhost:8050/calendar/events/print-next
```

Prints the next event that has a start time (all-day events are skipped) from
the stored events. When there is none, `printed` is `false` and nothing is
printed.

### Print events shortly before they start

```bash
curl -X POST 'http://localhost:8050/calendar/events/notify-upcoming?minutes=30'
```

```json
{
  "status": "ok",
  "printed_count": 1,
  "events": [{"summary": "Dentist", "...": "..."}],
  "message": "Printed 1 upcoming event(s)"
}
```

Syncs today's calendar, then prints every event that starts within the next
`minutes` and has not been printed before. Each event is remembered once
printed, so it is safe — and intended — to call this repeatedly:

```cron
*/10 * * * * curl -s -X POST 'http://localhost:8050/calendar/events/notify-upcoming?minutes=30'
```

Without `minutes`, the window is 90 minutes.

### A text calendar

`GET /calendar/text` returns a month laid out as plain text.

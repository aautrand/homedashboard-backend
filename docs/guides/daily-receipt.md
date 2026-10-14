# Daily receipt

The daily receipt is the morning printout: everything worth knowing about the
day on one slip of paper.

## Print it

```bash
curl http://localhost:8050/tasks/print
# {"status": "ok"}
```

The response only says the job was queued. The content goes to the printer.

## Schedule it

Nothing in this project runs on a timer. Have a scheduler call the endpoint
once each morning — for example with cron:

```cron
30 6 * * * curl -s http://localhost:8050/tasks/print
```

Call it **once a day**. See [What printing changes](#what-printing-changes).

## What is on it

The title is today's date. Sections follow in this order, and a section with
nothing in it is left out.

| Section | Content | Where it comes from |
|---|---|---|
| *(untitled)* | A random quote, then the pinned quote, centred | [Quotes](quotes.md) |
| Weather | Current temperature, today's low/high in °C and °F, conditions | OpenWeatherMap, for `LAT_LONG` |
| Birthdays | Names from calendar events with "birthday" in the title | iCloud calendar |
| All Day Events | Events without a time | iCloud calendar |
| Calendar | Timed events as `start - summary` | iCloud calendar |
| Routines | Chores due today, each with a `[ ]` checkbox | [Routines](routines-reminders-checklists.md#routines) |
| Reminders | Every active reminder | [Reminders](routines-reminders-checklists.md#reminders) |
| To Do | Every open todo, each with a `[ ]` checkbox | [Todos](todos-and-calendar.md#todos) |
| Today's Study | One subject to study | [Subjects](flashcards-and-quizzes.md#study-subjects) |
| Pop Quiz | Questions from flashcards still being learned | [Flashcards](flashcards-and-quizzes.md) |

Roughly:

```
            Oct 13, 2026

   "A quote from the rotation."
            - Its Author

Weather
Current:               18C / 64F
Forecast (Celsius):    11 / 23
...

Calendar
* 09:00 - Dentist

Routines
[ ] Take out trash

To Do
[ ] Buy milk
```

The exact look depends on the printer service that renders the job.

## What it needs

Printing the daily receipt calls OpenWeatherMap and iCloud, so it needs
`OPEN_WEATHER_API_KEY`, `LAT_LONG` and the calendar settings from
[configuration.md](../configuration.md). If either service fails, the request
fails and nothing is printed.

## What printing changes

Building the receipt records what was shown:

- Today's calendar events are synced from iCloud into the database.
- The random quote's show count goes up, moving the rotation on.
- Routines that repeat every N days are marked as shown today, restarting
  their interval.
- Reminders and todos get today's date as their last shown date.
- The study subject is marked as studied, which pushes its next appearance
  further out.

So a second call on the same day prints a different quote, may drop an
every-N-days routine and advances the study schedule a step early.

## Change what appears

| To change | Use |
|---|---|
| The quotes | [`/quotes`](quotes.md) |
| Chores and when they recur | [`/learning/routines`](routines-reminders-checklists.md#routines) |
| Standing reminders | [`/learning/reminder`](routines-reminders-checklists.md#reminders) |
| Todos | [`/calendar/todo`](todos-and-calendar.md#todos), or ask the [voice assistant](voice-assistant.md) |
| Study subjects | [`/learning/subjects`](flashcards-and-quizzes.md#study-subjects) |
| Quiz questions | [`/learning/cards`](flashcards-and-quizzes.md#flashcards) |
| Calendar events | Edit the iCloud calendar |

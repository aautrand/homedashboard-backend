# Routines, reminders and checklists

Three kinds of list, for three different jobs:

| | For | Printed |
|---|---|---|
| **Routine** | A chore that recurs — "take out the trash every Tuesday" | On the daily receipt, on the days it is due |
| **Reminder** | A standing note — "passport expires in March" | On the daily receipt, every day while active |
| **Checklist** | A reusable list — "packing for a trip" | On demand |

For one-off tasks, use [todos](todos-and-calendar.md#todos).

## Routines

A routine is due either on a **schedule pattern** or **every N days**. Give
one or the other when creating it.

### Create

```bash
# every day
curl -X POST http://localhost:8050/learning/routines \
  -H 'Content-Type: application/json' \
  -d '{"title": "Take medication", "schedule_pattern": "* * *", "priority": 1}'

# weekdays
curl -X POST http://localhost:8050/learning/routines \
  -H 'Content-Type: application/json' \
  -d '{"title": "Pack lunch", "schedule_pattern": "1-5 * *", "priority": 2}'

# every other day
curl -X POST http://localhost:8050/learning/routines \
  -H 'Content-Type: application/json' \
  -d '{"title": "Water the plants", "interval_days": 2, "priority": 4}'
```

| Field | |
|---|---|
| `title` | Required |
| `schedule_pattern` | See below. Required unless `interval_days` is given |
| `interval_days` | Show every N days. Required unless `schedule_pattern` is given |
| `priority` | Lower numbers print first. Default 0 |
| `active` | Default `true` |

### Schedule patterns

Three fields separated by spaces:

```
day_of_week  day_of_month  month
```

| Field | Values |
|---|---|
| `day_of_week` | 0–6, where 0 is Sunday and 6 is Saturday |
| `day_of_month` | 1–31 |
| `month` | 1–12 |

Each field takes `*` (any), a single value, a range (`1-5`) or a list
(`1,3,5`). A routine is due on a day when **all three** fields match.

| Pattern | Due |
|---|---|
| `* * *` | Every day |
| `1-5 * *` | Monday to Friday |
| `0,6 * *` | Saturday and Sunday |
| `2 * *` | Every Tuesday |
| `1,3,5 * *` | Monday, Wednesday, Friday |
| `* 1 *` | The 1st of every month |
| `* 1,15 *` | The 1st and 15th of every month |
| `* * 1,6` | Every day in January and June |
| `1 1 *` | The 1st of the month, but only when it is a Monday |
| `* 25 12` | 25 December |

### Every N days

A routine with `interval_days` is due the first time, then again once N days
have passed since it was last shown. "Shown" means printed on the daily
receipt, so the interval counts from the last printout rather than from fixed
calendar dates.

### See, change, remove

```bash
curl http://localhost:8050/learning/routines          # all, by priority
curl http://localhost:8050/learning/routines/today    # due today
curl http://localhost:8050/learning/routines/3        # one

# pause without deleting
curl -X PUT http://localhost:8050/learning/routines/3 \
  -H 'Content-Type: application/json' \
  -d '{"active": false}'

curl -X DELETE http://localhost:8050/learning/routines/3
```

`/learning/routines/today` is a good way to test a pattern: it shows what the
next daily receipt would list, without marking anything as shown.

## Reminders

Note that the path is singular: `/learning/reminder`.

```bash
# create
curl -X POST http://localhost:8050/learning/reminder \
  -H 'Content-Type: application/json' \
  -d '{"title": "Passport expires in March"}'

# list
curl http://localhost:8050/learning/reminder
curl 'http://localhost:8050/learning/reminder?active=true'

# stop it from printing
curl -X PUT http://localhost:8050/learning/reminder/4 \
  -H 'Content-Type: application/json' \
  -d '{"active": false}'

# print it now, on its own
curl -X POST http://localhost:8050/learning/reminder/4/print

curl -X DELETE http://localhost:8050/learning/reminder/4
```

An active reminder appears on every daily receipt until you deactivate or
delete it.

## Checklists

A checklist has a title, a list of items and, optionally, notes. Printing it
gives each item a `[ ]` checkbox and puts the notes underneath under "Relevant
Notes".

### Create and print

```bash
curl -X POST http://localhost:8050/learning/checklists \
  -H 'Content-Type: application/json' \
  -d '{"title": "Weekend trip", "items": ["Passport", "Charger", "Toothbrush"]}'

curl -X POST http://localhost:8050/learning/checklists/1/print
```

### Change

`items` is replaced as a whole — send the full list:

```bash
curl -X PUT http://localhost:8050/learning/checklists/1 \
  -H 'Content-Type: application/json' \
  -d '{"items": ["Passport", "Charger", "Toothbrush", "Sunscreen"]}'
```

```bash
curl http://localhost:8050/learning/checklists       # all
curl http://localhost:8050/learning/checklists/1     # one, with its notes
curl -X DELETE http://localhost:8050/learning/checklists/1
```

### Notes

Notes are extra lines kept with a checklist — things to remember that are not
items to tick off.

```bash
# add
curl -X POST http://localhost:8050/learning/checklists/1/notes \
  -H 'Content-Type: application/json' \
  -d '{"content": "Check-in closes 45 minutes before departure"}'

# list, in print order
curl http://localhost:8050/learning/checklists/1/notes

# edit
curl -X PUT http://localhost:8050/learning/checklists/1/notes/5 \
  -H 'Content-Type: application/json' \
  -d '{"content": "Check-in closes 60 minutes before departure"}'

# reorder: note ids in the order they should print
curl -X PUT http://localhost:8050/learning/checklists/1/notes/reorder \
  -H 'Content-Type: application/json' \
  -d '{"order": [7, 5, 6]}'

curl -X DELETE http://localhost:8050/learning/checklists/1/notes/5
```

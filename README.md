# Home Dashboard Backend

## Routine Tasks Cheat Sheet

### Cron Pattern Format
`day_of_week day_of_month month`

- **day_of_week**: 0-6 (0=Sunday, 1=Monday, 2=Tuesday, 3=Wednesday, 4=Thursday, 5=Friday, 6=Saturday)
- **day_of_month**: 1-31
- **month**: 1-12
- Use `*` for "any value"
- Use ranges like `1-5` for Monday-Friday
- Use lists like `1,3,5` for Monday, Wednesday, Friday

### Common Patterns

| Pattern     | Description                      |
|-------------|----------------------------------|
| `* * *`     | Every day                        |
| `1-5 * *`   | Monday through Friday (weekdays) |
| `0,6 * *`   | Saturday and Sunday (weekends)   |
| `2 * *`     | Every Tuesday                    |
| `5 * *`     | Every Friday                     |
| `1,3,5 * *` | Monday, Wednesday, Friday        |
| `* 1 *`     | 1st of every month               |
| `* 1,15 *`  | 1st and 15th of every month      |
| `* * 1,6`   | Every day in January and June    |
| `1 1 *`     | First Monday of every month      |

### Interval-Based Tasks

For "every N days" patterns (e.g., every 2 days, every 3 days):
- Set `interval_days` instead of `schedule_pattern`
- System automatically tracks last shown date

### Priority

- Lower number = higher priority
- Priority 1 appears first in daily print
- Priority 10 appears later

### API Examples

#### Create a daily task
```bash
POST /learning/routines
{
  "title": "Take medication",
  "schedule_pattern": "* * *",
  "priority": 1
}
```

#### Create a weekday task
```bash
POST /learning/routines
{
  "title": "Pack lunch",
  "schedule_pattern": "1-5 * *",
  "priority": 2
}
```

#### Create a specific day task
```bash
POST /learning/routines
{
  "title": "Take out trash",
  "schedule_pattern": "2 * *",
  "priority": 3
}
```

#### Create an every-other-day task
```bash
POST /learning/routines
{
  "title": "Bag milk",
  "interval_days": 2,
  "priority": 4
}
```

#### Update a task
```bash
PUT /learning/routines/1
{
  "active": false
}
```

#### Delete a task
```bash
DELETE /learning/routines/1
```

#### View today's tasks
```bash
GET /learning/routines/today
```

### Database Migration

Run the migration to create the routine_tasks table:
```bash
alembic upgrade head
```
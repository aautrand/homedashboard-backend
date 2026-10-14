# Recipes

Recipes live in a self-hosted [Tandoor](https://tandoor.dev/) server. The
backend reads them and can print a recipe's ingredients as a checklist — handy
as a shopping list, or to gather everything before cooking.

Recipes are **read-only** here. Add and edit them in Tandoor.

Needs `TANDOOR_URL` and `TANDOOR_API_TOKEN`; see
[configuration.md](../configuration.md#recipes).

## Find a recipe

```bash
curl http://localhost:8050/recipes                   # all
curl 'http://localhost:8050/recipes?query=lasagna'   # by name
```

```json
[
  {
    "id": 14,
    "name": "Lasagna",
    "description": "...",
    "servings": 6,
    "servings_text": "",
    "working_time": 40,
    "waiting_time": 50
  }
]
```

The search is by name and tolerant of small differences. Times are in minutes.

## Get the full recipe

```bash
curl http://localhost:8050/recipes/14
```

```json
{
  "id": 14,
  "name": "Lasagna",
  "servings": 6,
  "working_time": 40,
  "waiting_time": 50,
  "source_url": null,
  "steps": [
    {
      "name": "",
      "instruction": "Brown the meat ...",
      "ingredients": [
        {"food": "ground beef", "amount": 500, "unit": "g", "note": null,
         "is_header": false, "no_amount": false}
      ]
    }
  ],
  "ingredients": ["500 g ground beef", "1 onion", "..."]
}
```

`ingredients` is the whole recipe's ingredient list as ready-to-read lines, in
order. Tandoor attaches ingredients to steps; the same data is under each
entry in `steps` in structured form.

## Print the ingredients

```bash
curl -X POST http://localhost:8050/recipes/14/print-ingredients
```

```json
{"status": "ok", "recipe": "Lasagna", "ingredient_count": 12}
```

The receipt has the recipe name as its heading and lists one ingredient per
line with a checkbox. Group headings from Tandoor ("For the sauce") print as
dividers without a checkbox:

```
Lasagna
[ ] 500 g ground beef
[ ] 1 onion
-- For the sauce --
[ ] 800 g crushed tomatoes
```

## Errors

| Status | Meaning |
|---|---|
| 404 | No recipe with that id |
| 502 | Tandoor could not be reached, or returned an error |

## By voice

The [voice assistant](voice-assistant.md) uses the same lookups: "what goes in
the lasagna?" reads the recipe, and "print the ingredients for the lasagna"
prints the checklist.

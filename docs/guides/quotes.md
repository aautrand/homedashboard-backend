# Quotes

The [daily receipt](daily-receipt.md) opens with up to two quotes, centred
under the date:

- a **random quote**, different each day, drawn from the pool;
- a **pinned quote**, the same every day until you change it.

Both are optional. With an empty pool and nothing pinned, the receipt simply
has no quote section.

## Build the pool

```bash
curl -X POST http://localhost:8050/quotes \
  -H 'Content-Type: application/json' \
  -d '{"text": "We suffer more often in imagination than in reality.", "author": "Seneca"}'
```

`author` is optional. The response is the new quote, including its `id`.

Quotation marks are added when printing, so leave them out of `text`.

```bash
curl http://localhost:8050/quotes                 # all
curl 'http://localhost:8050/quotes?active=true'   # in rotation
curl http://localhost:8050/quotes/3               # one
```

Each quote reports `times_shown` and `last_shown_date`, so you can see where
the rotation stands.

## How the random quote is chosen

Each day's quote is picked at random from the quotes that have been shown the
**fewest** times. Every quote therefore appears once before any appears a
second time, and the order within each round is random.

A newly added quote has been shown zero times, so it is picked ahead of the
rest until it catches up.

To start the rotation over, clearing every quote's history:

```bash
curl -X POST http://localhost:8050/quotes/reset-rotation
# {"message": "Reset rotation for 24 quotes", "count": 24}
```

## Pin a quote

```bash
# pin a specific quote
curl -X PUT http://localhost:8050/quotes/pinned \
  -H 'Content-Type: application/json' \
  -d '{"quote_id": 3}'

# see what is pinned (404 when nothing is)
curl http://localhost:8050/quotes/pinned

# swap it for a different one, picked at random
curl -X POST http://localhost:8050/quotes/pinned/cycle

# unpin
curl -X DELETE http://localhost:8050/quotes/pinned
```

Only one quote is pinned at a time; pinning another replaces it. While
pinned, a quote is left out of the random draw, so it never prints twice on
one receipt.

A weekly `POST /quotes/pinned/cycle` from a scheduler makes a nice "quote of
the week".

## Edit, retire, delete

```bash
# fix the text or author
curl -X PUT http://localhost:8050/quotes/3 \
  -H 'Content-Type: application/json' \
  -d '{"author": "Lucius Annaeus Seneca"}'

# take it out of the rotation without deleting it
curl -X PUT http://localhost:8050/quotes/3 \
  -H 'Content-Type: application/json' \
  -d '{"active": false}'

curl -X DELETE http://localhost:8050/quotes/3
```

`PUT /quotes/<id>` changes `text`, `author` and `active` only. Pinning goes
through `/quotes/pinned`.

## By voice

The [voice assistant](voice-assistant.md) can add, find and pin quotes: "add a
quote: ...", "pin the one by Seneca".

## If quotes print off-centre

Centring is done with leading spaces, calculated for a paper width of
`RECEIPT_WIDTH` columns (default 48). If the printer has a different column
count, set `RECEIPT_WIDTH` to match — see
[configuration.md](../configuration.md#printing-and-locale).

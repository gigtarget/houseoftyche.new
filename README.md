# House of Tyche Telegram Bot

A private Telegram bot that generates a song title and a YouTube thumbnail image using OpenAI.

## Environment Variables

Set these in Railway:

- `TELEGRAM_BOT_TOKEN`: Telegram bot token from BotFather.
- `OWNER_TELEGRAM_ID`: Your Telegram user ID (only this user is authorized).
- `OPENAI_API_KEY`: OpenAI API key.
- `PUBLIC_BASE_URL`: Your Railway public URL (e.g. `https://your-app.up.railway.app`).
- `IMAGE_VIBE`: `dark`, `clean`, or `antique` (default `clean`).
- `LOG_LEVEL`: Optional logging level (e.g. `INFO`, `DEBUG`).

## Getting Your Telegram User ID

1. Message the `@userinfobot` on Telegram.
2. Copy the `id` field; use it as `OWNER_TELEGRAM_ID`.

## Webhook Setup

The app sets the webhook on startup using:

```
${PUBLIC_BASE_URL}/telegram/webhook
```

You should see a log entry indicating the webhook was set.

## Usage

Send a single Telegram message containing a prompt and lyrics.

### Format A (explicit markers)

```
PROMPT: A haunting love song
LYRICS:
Your lyrics go here...
```

### Format B (first line prompt)

```
A haunting love song
Lyrics line one
Lyrics line two
...
```

Minimum lengths:
- Prompt: 10 characters
- Lyrics: 50 characters

The bot will reply with a 1–2 word title, then send the generated thumbnail image.

## Local Run

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Testing the Webhook

```
curl -X POST http://localhost:8000/telegram/webhook \
  -H 'Content-Type: application/json' \
  -d '{"message":{"message_id":1,"from":{"id":123},"chat":{"id":123,"type":"private"},"text":"PROMPT: test prompt text\nLYRICS:\nthese are example lyrics that are at least fifty characters long"}}'
```

Remember to set `OWNER_TELEGRAM_ID=123` and provide valid API keys.

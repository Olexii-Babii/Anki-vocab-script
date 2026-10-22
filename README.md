# Anki vocab bot

Words (English — Ukrainian) live in a Google Sheet. Once a day GitHub Actions checks for new
(not yet exported) words and, if there are ≥ `MIN_NEW_WORDS`, sends an `.apkg` deck to Telegram.

Each word produces two cards in two separate decks (both in one `.apkg` file):
- `English::Vocabulary` — front: English word, back: Ukrainian translation;
- `English::Vocabulary (UK → EN)` — front: Ukrainian, back: English
  (disable with `ANKI_REVERSE_CARDS=false`).

## Commands

```bash
python -m vocab import-doc [--file words.docx|words.txt] [--dry-run] [--mark-exported] [--export-now]
python -m vocab export [--force] [--all]
```

- Line format: `word - translation` (also `–`, `—`, `:`, TAB). The first separator wins.
  Lines without a separator are listed in the report with their line number.
- Duplicates are not removed: `run - бігти` and `run - керувати` become two cards.
  Identical pairs (word + translation) are not appended to the sheet again, so re-running
  `import-doc` adds nothing, and in Anki the same pair always updates the same card.
- `export` sets `exported_at` **only after** the file was successfully sent to Telegram.
  An empty `added_at` in manually added rows is filled in automatically.
- `export --all` re-sends every word (e.g. to get UK → EN cards for words exported earlier).
  Existing EN → UK cards are updated, not duplicated.

## Setup

### 1. Google Cloud
1. https://console.cloud.google.com → create a project.
2. APIs & Services → Library → enable **Google Sheets API** and **Google Drive API**.

### 2. Service account
1. IAM & Admin → Service Accounts → Create. No roles needed.
2. Keys → Add key → JSON — a key file is downloaded (do not commit it!).
3. Create a Google Sheet, click Share and add the service account email (`...@...iam.gserviceaccount.com`) as **Editor**.
4. Share the Google Doc with the words with the same email as **Viewer**.
5. The ID is part of the URL: `docs.google.com/spreadsheets/d/<ID>/edit`, `docs.google.com/document/d/<ID>/edit`.

The script creates the `words` tab and its headers itself.

### 3. Telegram bot
1. Message [@BotFather](https://t.me/BotFather) → `/newbot` → get the token.
2. Send any message to your bot (press **Start** first).
3. Open `https://api.telegram.org/bot<TOKEN>/getUpdates` — `chat_id` is in `result[0].message.chat.id`.
   If `result` is empty, message the bot again and refresh the page.

### 4. Running locally
```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env    # fill it in; paste the JSON key as a single line:
                        # python -c "import json;print(json.dumps(json.load(open('key.json'))))"
python -m vocab import-doc --dry-run     # check the report
python -m vocab import-doc               # write to the sheet
python -m vocab export --force           # get the first deck
pytest                                   # tests
```
If some of the words are already in Anki, use `import-doc --mark-exported`.

### 5. GitHub Actions
Settings → Secrets and variables → Actions:
- **Secrets:** `GOOGLE_SERVICE_ACCOUNT_JSON`, `GOOGLE_SHEET_ID`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
- **Variables** (optional): `MIN_NEW_WORDS`, `ANKI_DECK_NAME`, `ANKI_REVERSE_CARDS`, `ANKI_REVERSE_DECK_NAME`, `NOTIFY_WHEN_NOT_ENOUGH`, `GOOGLE_SHEET_TAB`.

To test: Actions → *Daily Anki export* → Run workflow (optionally with `force`).
Runs daily at 06:00 UTC (09:00 Kyiv time in summer, 08:00 in winter).

> ⚠️ In public repositories GitHub disables scheduled workflows after 60 days without repository
> activity — re-enable the workflow on the Actions tab (or push any commit).

### 6. Importing into Anki
- **Desktop:** File → Import → choose the `.apkg` (or double-click the file).
- **Android (AnkiDroid):** in Telegram save the file to Downloads, then in AnkiDroid
  menu → Import → choose `english-….apkg`. (Opening it directly from Telegram may fail with
  "stream did not contain valid UTF-8".)
- **iPhone (AnkiMobile):** in Telegram → Share → Anki.

Every file is imported into the same two decks; re-importing does not create duplicates.

## Environment variables
| Variable | Default |
|---|---|
| `GOOGLE_SERVICE_ACCOUNT_JSON`, `GOOGLE_SHEET_ID`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | required |
| `GOOGLE_DOC_ID` | for `import-doc` without `--file` |
| `GOOGLE_SHEET_TAB` | `words` |
| `MIN_NEW_WORDS` | `10` |
| `ANKI_DECK_NAME` | `English::Vocabulary` |
| `ANKI_REVERSE_CARDS` | `true` |
| `ANKI_REVERSE_DECK_NAME` | `English::Vocabulary (UK → EN)` |
| `NOTIFY_WHEN_NOT_ENOUGH` | `false` |

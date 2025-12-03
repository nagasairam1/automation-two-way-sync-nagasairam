 automation-two-way-sync-nagasairam

Two-way sync between Airtable (Lead Tracker) and Trello (Work Tracker) using Python.

- Keeps Leads and Tasks in sync (status-based).
- Idempotent: you can run the sync multiple times without creating duplicates.
- Shows error handling, logging, basic retry logic, and a clean modular design.

---

 1. Overview

Lead Tracker (Airtable):

- Table: `Leads`
- Fields:
  - `Name` (Single line text)
  - `Email` (Email)
  - `Status` (Single select: `NEW`, `CONTACTED`, `QUALIFIED`, `LOST`)
  - `Source` (optional, text)

Work Tracker (Trello):

- Board: `Lead Tasks` (you can rename if you like)
- Lists (4):
  - `NEW`         → for leads with `Status = NEW`
  - `CONTACTED`   → for `Status = CONTACTED`
  - `QUALIFIED`   → for `Status = QUALIFIED`
  - `LOST`        → for `Status = LOST`

A Trello card represents a task for a lead. It contains:

- `name`: `Follow up: <Lead Name>`
- `desc` includes:
  - `Lead Name: ...`
  - `Email: ...`
  - `Lead ID: <Airtable record ID>`

The `Lead ID` is the key used to guarantee idempotency.

---

 2. Architecture & Flow

High-level:

```text
+----------------+        HTTP (REST)         +----------------+
|   Airtable     | <------------------------> |     Trello     |
| (Lead Tracker) |                             | (Work Tracker) |
+----------------+         Python sync         +----------------+
        ^                           ^
        |                           |
        |     sync_all_leads        |  sync_tasks_to_leads
        +-------------+-------------+
                      |
                 sync.py / webhook_server.py
```

- AirtableClient: wraps Airtable REST API for the `Leads` table.
- TrelloClient: wraps Trello REST API for a single board.
- sync_logic:
  - `sync_all_leads_to_tasks()`
  - `sync_tasks_to_leads()`
- webhook_server (FastAPI): optional real-time triggers.

Status mapping is 1–1:

| Airtable Status | Trello List |
|-----------------|-------------|
| NEW             | NEW         |
| CONTACTED       | CONTACTED   |
| QUALIFIED       | QUALIFIED   |
| LOST            | LOST        |

You can change these names if you like, but then update the lists + mapping in your `.env`.

---

 3. Setup Instructions

 3.1. Clone and install

```bash
git clone <your-repo-url> automation-two-way-sync-nagasairam
cd automation-two-way-sync-nagasairam
python -m venv venv
 Windows: venv\Scripts\activate
 Linux/Mac:
source venv/bin/activate
pip install -r requirements.txt
```

 3.2. Airtable configuration

1. Create a free account at https://airtable.com
2. Create a new Base (e.g., `Lead Tracker`).
3. Create table `Leads` with fields:
   - `Name` (Single line text)
   - `Email` (Email)
   - `Status` (Single select: NEW, CONTACTED, QUALIFIED, LOST)
   - `Source` (optional)
4. Get your Base ID and API key / personal access token from the Airtable developer settings.
5. Put them into `.env` (see below).

 3.3. Trello configuration

1. Create a free account at https://trello.com
2. Create a new Board (e.g., `Lead Tasks`).
3. Create 4 lists with names: `NEW`, `CONTACTED`, `QUALIFIED`, `LOST`.
4. Get your API key and token from https://trello.com/app-key
5. Get your Board ID from the URL (the short ID in the path).
6. Get the List IDs for each list (you can use Trello’s API or browser dev tools).

Then put them into `.env`.

 3.4. Environment variables

1. Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

2. Fill in:

```env
AIRTABLE_API_KEY=your_airtable_token
AIRTABLE_BASE_ID=appXXXXXXXXXXXX
AIRTABLE_LEADS_TABLE_NAME=Leads

TRELLO_API_KEY=your_trello_api_key
TRELLO_TOKEN=your_trello_token
TRELLO_BOARD_ID=your_board_id

 Example mapping (replace with your actual list IDs)
TRELLO_LIST_IDS={"NEW":"<id_new>","CONTACTED":"<id_contacted>","QUALIFIED":"<id_qualified>","LOST":"<id_lost>"}

WEBHOOK_SECRET=optional-shared-secret
```

> 🛡️ `.env` is ignored by git via `.gitignore`, so secrets are not committed.

---

 4. Usage

 4.1. One-off full sync

This will:

1. Sync Airtable → Trello (create/update cards for each non-LOST lead).
2. Sync Trello → Airtable (update lead status based on card’s list).

```bash
python sync.py --full
```

 4.2. Polling mode (simple scheduler)

This runs both sync directions every 60 seconds.

```bash
python sync.py --poll
```

Stop with `Ctrl + C`.

 4.3. Webhook server (optional)

Start the FastAPI server:

```bash
uvicorn webhook_server:app --reload --port 8000
```

- Health check: `GET http://localhost:8000/health`
- Airtable webhook target: `POST http://<public-url>/webhook/airtable`
- Trello webhook target: `POST http://<public-url>/webhook/trello`

If you want to test quickly, you can:

```bash
curl -X POST http://localhost:8000/webhook/airtable -H "Content-Type: application/json" -d "{}"
```

This will trigger `sync_all_leads_to_tasks()`.

---

 5. How to Demo (for your video)

Suggested 8–10 minute flow:

1. Intro (1–2 min)  
   - Explain tools (Airtable, Trello) and two-way sync.
   - Show the architecture diagram briefly.

2. Code walkthrough (3–4 min)
   - `clients/airtable_client.py` and `clients/trello_client.py` (API usage).
   - `logic/sync_logic.py` (core sync + idempotency).
   - `utils/retry.py` and logging setup.

3. Setup explanation (1–2 min)
   - Show `.env` (without secrets) and how IDs are mapped.

4. Live demo (3–4 min)
   - Run `python sync.py --full`.
   - In Airtable, create a new lead with `Status = NEW` → show Trello card appears in `NEW` list.
   - Change Airtable lead status to `CONTACTED` → run sync, card moves to `CONTACTED` list.
   - Move Trello card to `QUALIFIED` → run sync, Airtable lead becomes `QUALIFIED`.
   - Run `python sync.py --full` again → no duplicate cards created.

5. Wrap-up (1–2 min)
   - Talk about edge cases, rate limits, and how you would extend it (DB, more fields, etc.).

---

 6. Error Handling & Idempotency

Idempotency:

- Each Airtable record has a stable `id`.
- The Trello card `desc` stores `Lead ID: <id>`.
- On sync, we scan existing cards; if a card with that `Lead ID` exists, we update it instead of creating a new one.
- Result: rerunning the sync does not create duplicates.

Error handling:

- All HTTP calls are wrapped in `_request()` methods that log non-2xx responses and raise for serious errors.
- The `@retry` decorator retries transient failures (e.g., network issues, temporary 5xx) a few times with delay.
- Failures for a single record are logged, and the loop continues with the next record.

---

 7. Assumptions & Limitations

Assumptions:

- Status is the only field used for sync logic (no complex business rules).
- Last write wins: we do not resolve conflicts if Airtable and Trello both changed between syncs.

Limitations:

- No persistent local database; sync state is derived from Airtable + Trello live data every run.
- Webhook payloads are treated as “hints” to sync, not fully parsed for partial updates (keeps code simpler).

---

 8. AI Usage Notes

- Tools used: ChatGPT (OpenAI) for brainstorming structure and generating boilerplate code ideas.
- Used for:
  - Thinking through high-level architecture.
  - Suggesting a clean project structure and mapping strategy.
  - Drafting some helper functions (retry, logger configuration).
- I manually reviewed and adapted all code:
  - Ensured API endpoints and parameters match Airtable and Trello docs.
  - Simplified some AI-suggested ideas to keep the project focused and easy to set up.

One suggestion I rejected:

- AI suggested adding a SQLite database to persist sync metadata.
- I decided against it because:
  - It would add migration/connection overhead.
  - The assignment only needs a small, demonstrable project.
  - Airtable + Trello already store the necessary state (lead ID in card description).
- Instead, I used a stateless approach: the sync infers state directly from Airtable and Trello each run.

---

 9. Video

Once recorded, add your public Google Drive link here:

> Demo video: https://drive.google.com/your-demo-link (Anyone with the link can view)

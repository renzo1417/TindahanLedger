# TindaHan Ledger

A Django ledger for sari-sari stores: customer debt and payments, batch inventory,
Cash/Utang point of sale, expiry tracking, reports, and simulated SMS reminders.

## Run

From the repository root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r crms\requirements-dev.txt
```

Put the current Supabase PostgreSQL connection string in `crms/.env` as
`DATABASE_URL`. The activation script verifies the connection and migration
history, applies the additive migrations, audits the data, and only then saves
`USE_LOCAL_DB=False`:

```powershell
.\.venv\Scripts\python.exe crms\scripts\activate_supabase.py
.\.venv\Scripts\python.exe crms\manage.py runserver
```

Supabase is the primary database when `USE_LOCAL_DB=False`. The activation script
changes that setting only after connection verification and migration succeed.
Restart any running development server after activation. There is no automatic
database fallback: failed database requests display a connection-error page or
a 503 JSON response.

For deliberate local development instead:

```powershell
$env:USE_LOCAL_DB = 'True'
.\.venv\Scripts\python.exe crms\manage.py migrate
.\.venv\Scripts\python.exe crms\manage.py runserver
```

`LOCAL_DB_PATH` optionally selects a separate SQLite file. SQLite data is never
automatically uploaded to Supabase. Business dates use `Asia/Manila`.

## Classroom demonstration

Normal accounts start empty. To create a **dedicated** demo account, run:

```powershell
.\.venv\Scripts\python.exe crms\manage.py seed_demo --username classroom-demo
```

Enter a new password at the hidden prompt, or set `DEMO_PASSWORD` for unattended
local setup. Running the command again leaves the existing demo unchanged. It
refuses to populate an ordinary account. Example records use dates relative to
the day of setup; they do not appear in another store.

SMS is a free simulation. Previews use the actual customer balance and saved
store details. Simulated messages have no delivery timestamp, make no provider
request, and are clearly distinguished from real delivery.

## Data behavior

- Login accounts have an explicit business-owner link; matching numeric IDs do
  not establish ownership. Migration links only exact username matches and
  preserves unmatched legacy owners and stores. It also repairs the PostgreSQL
  owner ID sequence left behind by the old explicit-ID synchronization, so new
  accounts cannot collide with existing owner records.
- Administrators can inspect unlinked owners in `/admin/`. To assign legacy
  records, explicitly run `assign_legacy_store --store ID --username USERNAME`.
  This previews the change; add `--apply` after reviewing it. The target account
  must have no business records in its existing store. Its empty store is
  preserved under the unlinked legacy owner; no stores or records are deleted.
  The app never guesses that a legacy store belongs to a login.
- Product batch quantities determine stock. Migration preserves existing batches
  and reconciles product counters. Stock without any batch receives an opening
  batch; missing expiry dates are not invented.
- Checkout uses earliest expiry, then arrival order. Expired, disposed, and
  expiry-tracked stock without dates cannot be sold. A date printed as today
  remains sellable until the next Philippine calendar day.
- Checkout, payments, restocks, corrections, and disposal run in transactions
  serialized by a store row lock on PostgreSQL. Checkout retries use the same
  unique token. Historical sale lines retain their actual batch costs.
- Opening balances and manual debt adjustments affect the ledger only. Product
  purchases belong in POS. Payments cannot exceed the balance; credit enforcement
  follows the saved business setting. The earliest outstanding due date is kept
  until the balance is settled, because payments are not allocated to invoices.
- Reports count Cash and Utang POS sales once. Collections are cash sales plus
  recorded debt payments. Gross profit is sales minus recorded product costs,
  before operating expenses or disposal losses. Outstanding debt is a current
  balance, separate from period activity.
- CSV/JSON exports contain only the signed-in store's records. They contain no
  account passwords, connection strings, or session credentials.

Read-only ownership/stock audit:

```powershell
.\.venv\Scripts\python.exe crms\manage.py audit_store_data
```

## Verification

Ordinary tests always use an isolated SQLite database:

```powershell
.\.venv\Scripts\python.exe crms\manage.py test apps.home apps.landing apps.inventory --settings=config.test_settings
.\.venv\Scripts\python.exe crms\manage.py makemigrations --check --dry-run --settings=config.test_settings
```

PostgreSQL concurrency tests require a working direct/session-mode PostgreSQL
connection with permission to create a schema. Set `PG_TEST_DATABASE_URL` locally,
then run:

```powershell
.\.venv\Scripts\python.exe crms\manage.py test apps.home apps.landing --settings=config.postgres_test_settings
```

The PostgreSQL runner creates a uniquely named `ledger_test_<uuid>` schema,
restricts test connections to that schema, and drops only that schema afterward.
It does not use public store tables. Use a direct or session-mode connection,
rather than a transaction pooler, for this schema-isolated test runner.

For browser checks, start a local server using a disposable seeded database,
set `CHECK_USERNAME` and `CHECK_PASSWORD` for its demo account, and run:

```powershell
.\.venv\Scripts\python.exe crms\scripts\check_workspace.py
```

This uses installed Chrome in headless mode, checks thirteen screens at three
widths, verifies search/modal keyboard access, and completes Cash/Utang/retry
checkouts. Screenshots and the report go into ignored `.cache/ui-check/`.

## UI decisions

The application follows the Tindahan Ledger Figma design: warm paper surfaces,
orange and dark summary panels, a dark desktop sidebar and mobile navigation,
and self-hosted Bricolage Grotesque and Geist Mono fonts. Login and registration
retain their existing appearance. Shared Django components carry navigation,
forms, dialogs, and feedback. Daily operations stay immediate; reduced-motion
and keyboard shortcuts skip dialog movement.

The landing page uses the Figma desktop, tablet, and mobile layouts and supplied
illustrations. Its dashboard preview renders the current dashboard: public
visitors see an empty store, while signed-in visitors see only their saved store
records. Empty accounts show empty states; connection failures show a retry page
instead of invented records or totals. Product illustrations follow the saved
unit (packet, can, or sachet), with a neutral package icon for other units.

| Before | After | Why |
| --- | --- | --- |
| Repeated oversized store headings | Compact store bar and one screen heading | More space for the task |
| Stacked statistic cards and decorative hover lifts | Ruled summaries and calm ledger rows | Clearer information hierarchy |
| Success messages before saving | Confirmed saves, field errors, and retry states | Trustworthy feedback |
| Placeholder mobile destinations | Home, Utang, POS, Inventory, and More navigation | Every screen is reachable |

# AFZAL HEART CENTRE ECHO MANAGEMENT SYSTEM

Central patient registration, daily tokens, manual echo reporting and performance tracking. Python 3.11+; no runtime packages or external services required.

## Start

Double-click `START ECHO.bat` on the designated central server. Keep its terminal open. Open http://127.0.0.1:8765. On a new installation, create the first administrator, then add doctors/stamps and receptionist/operator/doctor accounts in Administration. Set the repeat interval in months.

Allow Windows firewall access on the trusted Private Network when prompted. Other department PCs open `http://SERVER-IP:8765`, using the server IPv4 address shown by `ipconfig`. All operators must use this same central server and SQLite database. Do not start separate databases on operator PCs. This HTTP server listens on all interfaces; use only on a trusted department LAN. Internet deployment requires a separately secured HTTPS setup.

## Roles and workflow

- Receptionist searches CNIC/phone first, registers a patient and prints the token in one click, edits patients, issues tokens and reprints existing tokens. Adult CNIC and phone must be unique; children may share parent details.
- Operator claims pending tokens atomically, selects a doctor and enters manual findings. Save Draft retains the report in that operator's Draft Reports. Finalize & Print locks it and moves it to Completed / History. The original operator can use Edit Report with a correction reason; the previous version is retained. Early tokens can also be issued by Receptionists when both Reason and Ordered by are entered; both print on the token. Saved operator permissions remain supported.
- Admin manages accounts, doctors/stamps, policy and analytics; no patient registration or reporting.
- Doctor sees own performance and operator performance; no patient search or report editor.

Tokens have three slip positions per A4 portrait sheet and black-and-white styling. Reports use the supplied logos and layout. Template findings remain manually editable; the application does not generate diagnoses. Patient snapshots preserve historical report details after later registry edits.

## Data and upgrade

`data/echo.sqlite3` is the central database. Stop the server with Ctrl+C before copying the complete data folder, including any WAL files. Protect backups as patient records. Never delete/reset/overwrite the database during upgrade. Sessions clear on restart.

Follow [UPGRADE.md](UPGRADE.md). The delivery ZIP contains an empty data directory and no patient records or accounts. Local pre-change backups are in `backups/`, excluded from delivery.

## Structure and verification

`server.py` starts the server. `backend/` separates configuration, migrations, security, permissions, services and routes. `public/js/` separates boot, API, shared state, routing, utilities, components, screens and printing. Classic scripts load with defer in dependency order; shared state is declared in state.js. `public/css/` separates dashboard/forms and print styling. Approved assets live in `public/assets/`.

Run `python -m unittest discover -v`. API/database tests use temporary databases. Optional browser tests run when Playwright and Chromium are installed; otherwise Playwright tests skip. Browser evidence in `artifacts/` uses synthetic records, never the live database.

Search and completed/draft lists return up to 100 records. Encounter opening fetches its patient directly, independently of this limit. No appointment calendar, automatic backups or internet deployment configuration is included. Hospital staff should validate clinical reference text and physical printer output before clinical use.

## Reviewed delivery and continuity

Read [_HANDOVER.md](_HANDOVER.md) for the verified project status and remaining operational checks. MediTech is the software developer; hospital branding remains the primary clinical identity.

Build a clean new-installation ZIP with `python tools/build_delivery.py`. The archive is `dist/AFZAL_HEART_CENTRE_MEDITECH_REVIEWED.zip` and contains an empty data folder. Follow UPGRADE.md for an existing installation.

## Workflow update

Duplicate CNIC/phone matches show patient names, registration numbers and last echo dates. Measurement rows and columns are editable beside the values, and their order is retained in drafts and printing. AR/MR/TR/PR buttons append or remove plus signs in Color Flow; no findings are generated automatically. Today and earlier pending tokens are separate on the operator screen.

Print waits for all logos/stamps to load and uses a consistent A4 layout. Short reports keep their signature/footer near the bottom; long reports continue onto additional pages rather than being shrunk or cut off. Software credits read Powered by MediTech.

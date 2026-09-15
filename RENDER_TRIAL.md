# Render trial backend

Status: source pushed to GitHub, ready to connect. No Render service created yet.
Repo: https://github.com/touqeer2183-png/echo-management-trial (private).

Render hosts the Python backend; Netlify hosts the static frontend only
(see NETLIFY_TRIAL.md). Render free web services use ephemeral disk: SQLite
data survives restarts but is wiped on redeploy. Acceptable for a trial;
not for live patient records.

## Create the Render web service

1. https://dashboard.render.com -> New + -> Web Service -> connect the
   `echo-management-trial` GitHub repo.
2. Runtime: Python 3. Build command: (leave blank). Start command:
   `python server.py`. Instance type: Free.
3. Environment variables:
   - `ECHO_HOST` = `0.0.0.0`
   - `ECHO_PUBLIC_ORIGIN` = the Netlify site's HTTPS origin (set this after
     the Netlify site is created, before the first Render deploy succeeds
     with cookies working)
   - `ECHO_DB` = `/opt/render/project/src/data/echo.sqlite3`
4. Deploy. Render gives an origin like `https://<service>.onrender.com`.
5. Create the first admin through the deployed frontend's setup screen
   (`/api/setup` is only available while the users table is empty).

Use `ECHO_BACKEND_URL` on Netlify (see NETLIFY_TRIAL.md) set to this
Render origin, no trailing path.

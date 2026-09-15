# Netlify trial

Prepared, not deployed. The existing Python/SQLite backend cannot run directly
as a Netlify Function. This configuration publishes only public/ and proxies
/api/* to a separately hosted backend. It excludes local records and backups.

## Current deployment blocker (2026-09-15)

Netlify saved authentication was verified through its user API. Railway login
also succeeded, but creating the isolated `echocare-netlify-trial` project was
rejected: "Your trial has expired. Please select a plan to continue using Railway."
No backend or Netlify site was deployed. Hosting choice is pending; no paid plan
was activated. User approved a Netlify frontend with a separately hosted backend.

User subsequently ruled out PC-hosted deployment. PythonAnywhere selected as
the next trial option; no saved access was available and the login page was
opened for the user. backend/wsgi.py adds hosted WSGI transport without changing
the local server entry point. Two targeted tests passed for authentication,
origin rejection, patient registration, draft persistence and finalization.
See PYTHONANYWHERE_TRIAL.md. The source-only package is
dist/ECHOCARE_PYTHONANYWHERE_TRIAL.zip; no live SQLite records are included.
Remote deployment still awaits hosting account access.

1. Select and deploy a Python backend with persistent storage, using an empty
   trial database. Follow INTERNET_HOSTING.md for unfinished hosting work.
2. Set ECHO_BACKEND_URL in Netlify to its HTTPS origin (no trailing path).
3. Set ECHO_PUBLIC_ORIGIN on the backend to the exact Netlify site origin.
4. Deploy using netlify.toml. The build deliberately fails without a backend.
5. Verify login/logout, cookies, record save/reopen, cross-user permissions and
   report printing through the actual Netlify address before sharing the trial.

Use a stable trial site URL: arbitrary preview URLs will be rejected by the
backend origin check. Database records remain on the backend, not on Netlify.
Do not drag the existing delivery ZIP or the project root onto Netlify Drop.

References:
- https://www.netlify.com/platform/core/functions/
- https://docs.netlify.com/manage/routing/redirects/rewrites-proxies/

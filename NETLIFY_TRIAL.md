# Netlify trial

Prepared, not deployed. The existing Python/SQLite backend cannot run directly
as a Netlify Function. This configuration publishes only public/ and proxies
/api/* to a separately hosted backend. It excludes local records and backups.

## Current status (2026-09-15)

Railway trial expired and PythonAnywhere access was never available (see
PYTHONANYWHERE_TRIAL.md, superseded). Render was chosen as the backend host.
Source pushed to a new private GitHub repo:
https://github.com/touqeer2183-png/echo-management-trial. No Render service
or Netlify site has been created yet; both require manual dashboard steps
(account login/OAuth) that cannot be scripted from this environment.
See RENDER_TRIAL.md for the backend steps.

1. Deploy the backend on Render using an empty trial database.
   Follow RENDER_TRIAL.md.
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

# Internet access preparation

Status: HTTPS compatibility implemented; internet deployment is not live.
Hosting account/server and domain details are still required. No live patient
database has been uploaded or changed by this preparation.

## Application settings

- `ECHO_PUBLIC_ORIGIN=https://echo.example.com` sets the exact browser origin
  and enables Secure session cookies. Replace the example with the actual domain.
- In this mode the backend defaults to `127.0.0.1`, behind a local HTTPS proxy.
- `ECHO_HOST` overrides the bind address; `PORT` defaults to `8765`.
- `ECHO_DB` selects the persistent SQLite file. Use one application process;
  sessions and the database write lock currently live in process memory.
- Forwarded request headers do not select the trusted origin.
- Without these environment settings, existing LAN operation is unchanged.

These settings do not install TLS or make the server publicly reachable.
Caddy can terminate HTTPS and proxy to the local application:
https://caddyserver.com/docs/quick-starts/reverse-proxy

## Before public launch

The current Python http.server transport is intended for the existing LAN setup;
Python does not recommend it for production internet service:
https://docs.python.org/3/library/http.server.html

Once the hosting target is selected, complete the production transport/deployment
configuration, login throttling, private first-admin setup, HTTPS, persistent
storage, restart service and scheduled consistent backups. Keep backend port
8765 private. Move existing records only with a consistent database backup and
an agreed cutover, so LAN and remote staff use the same central database.

Verify external login, permissions, save/reopen, report printing, HTTPS cookies,
restart persistence and backup restoration on that target before declaring live.

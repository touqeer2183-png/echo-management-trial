# PythonAnywhere backend for the Netlify trial

Status: local WSGI adapter prepared. Account access and remote verification pending.
Use a new empty trial database, not the hospital's live SQLite file.

PythonAnywhere supports Python WSGI hosting and SQLite on free accounts:
https://help.pythonanywhere.com/pages/KindsOfDatabases
https://help.pythonanywhere.com/pages/WebAppBasics

## Hosting configuration after account access

Upload the source-only backend package and extract under the account home.
Create a Python 3.11+ web app with Manual configuration. Use one worker because
the current sessions are process-local. Keep the database outside static paths.
The WSGI configuration must set these before importing backend modules:

```python
import os
import sys
sys.path.insert(0, '/home/YOUR_USERNAME/echocare')
os.environ['ECHO_DB'] = '/home/YOUR_USERNAME/echocare-data/echo.sqlite3'
os.environ['ECHO_PUBLIC_ORIGIN'] = 'https://YOUR_TRIAL_SITE.netlify.app'
from backend.wsgi import application
```

Initialize the empty database and create the first admin in a private console
before enabling the public web app. The adapter intentionally does not run
migrations automatically on import. Use backend.migrations.init and
backend.services.users.add_user inside backend.database.transaction; obtain
the initial password privately, never commit it to the deployment package.

Set Netlify ECHO_BACKEND_URL to the PythonAnywhere HTTPS origin and deploy the
frontend using netlify.toml. Verify cookie forwarding and actual save/reopen,
finalization, permissions and browser printing through the Netlify URL.

Free plan limits and expiry rules apply; review the provider dashboard. No
cloud deployment or remote persistence is claimed until these checks pass.

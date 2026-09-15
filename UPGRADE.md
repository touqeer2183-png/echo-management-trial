# Upgrade and rollback

1. Stop the central server with Ctrl+C and ask department users to wait.
2. Copy the complete existing application folder, including all of data/, to a timestamped backup. Confirm it is readable.
3. Extract the delivery ZIP into a temporary directory. Copy server.py, START ECHO.bat, requirements.txt, README.md, UPGRADE.md and the complete backend/, public/ and tests/ folders into the existing installation. **Do not copy, replace or delete data/.** Do not launch a second server.
4. Start START ECHO.bat from the existing installation. Checked numbered migrations run automatically against the same database. Refresh browsers with Ctrl+F5 and sign in again.
5. Compare patients, visits, finalized reports, recent registration/token numbers, accounts, doctors, settings and audit counts against the backup.

For rollback, stop the upgraded server and retain a complete copy of its folder before restoring the complete pre-upgrade application and its matching data folder. An older database loses records entered since that backup; reconcile these before rollback. Never combine an old database with a newer WAL file.

For a NEW installation only, extract the delivery ZIP to a new directory and use its empty data folder. Never replace an existing registry with that empty folder.

The reviewed delivery is `AFZAL_HEART_CENTRE_MEDITECH_REVIEWED.zip`. Also copy `_HANDOVER.md` and `tools/build_delivery.py` when updating the documentation and packaging utility. Keep previous backups outside the delivered installation archive.

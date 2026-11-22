# SmartClass — Classroom Management Website (MVP)

This is a beginner-friendly full-stack prototype built with Flask, SQLite, SQLAlchemy, HTML, CSS and Jinja templates.

## Included features
1. Search for rooms free during a requested date and time.
2. Filter by minimum seats, projector and building.
3. View the timetable for a date.
4. Teacher-only rescheduling for classes assigned to that teacher, with room and teacher conflict checks.
5. In-app notifications for the teacher who reschedules a class.
6. Role-aware access: teachers can reschedule their own classes; the demo admin account is view-only.

## Not included yet
- Live camera / face / occupancy detection.
- Email/SMS/push notifications.
- Admin screens for adding rooms or teachers.
- Temporary booking workflow.
- Production-grade deployment/security hardening.

## Requirements
- Python 3.10 or newer
- VS Code (recommended)
- A browser

## Run on Windows (PowerShell)
1. Extract the ZIP to a folder, e.g. `C:\Projects\smartclass_project`.
2. Open that folder in VS Code: File -> Open Folder.
3. Open Terminal -> New Terminal.
4. Create a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, use Command Prompt terminal and run:
   ```bat
   .venv\Scripts\activate.bat
   ```

5. Install packages:
   ```powershell
   python -m pip install -r requirements.txt
   ```

6. Start the server:
   ```powershell
   python app.py
   ```

7. Open `http://127.0.0.1:5000/seed-demo` in your browser ONCE to create sample users, classrooms and timetable entries. Then open `http://127.0.0.1:5000/login`.

## Demo accounts
- Teacher: `teacher@smartclass.local` / `Teacher123!`
- Second teacher: `teacher2@smartclass.local` / `Teacher123!`
- Admin (view-only in this prototype): `admin@smartclass.local` / `Admin123!`

These credentials are for local testing only. Do not publish or deploy the app with them.

## Reset demo database
Stop the server with Ctrl+C, delete `smartclass.db`, restart `python app.py`, and visit `/seed-demo` again.

## Important development notes
- This prototype uses a local SQLite database; it is fine for learning and demos.
- The secret key in `app.py` is a development placeholder. Set `SMARTCLASS_SECRET_KEY` to a long random secret before deployment.
- Remove or protect the `/seed-demo` route before public deployment.
- For a real college deployment, add CSRF protection, password reset, stronger audit logs, concurrency-safe booking transactions, admin management pages, backups, HTTPS, and institutional authorization.
- In-app notifications currently go to the teacher who rescheduled the class. Before a real rollout, define which affected teachers/students should receive notifications and add that logic.
- Times are stored as local naive datetimes for this demo. For multi-campus/time-zone deployment, define a time-zone policy.

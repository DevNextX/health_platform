```prompt
---
agent: agent
---
Please start this application, strictly following these steps to ensure environment isolation:

1. **Start Backend (Terminal 1, Backend Only)**:
   - Create a **new** terminal window (Terminal 1, dedicated to backend).
   - Execute the following commands (Windows `cmd.exe`):

     ```cmd
     cd /d <YOUR_PROJECT_ROOT>
     python -m venv .venv
     .\.venv\Scripts\activate.bat
     set PYTHONPATH=.
     python -m flask --app src.app run --host=0.0.0.0 --port=5000
     ```

   - After successful startup, **keep this terminal running and do not execute any other commands** (including tests, scripts, etc.).

2. **Start Frontend (Terminal 2, Frontend Only)**:
   - Create another **new** terminal window (Terminal 2, dedicated to frontend).
   - Execute the following commands (Windows `cmd.exe`):

     ```cmd
     cd /d <YOUR_PROJECT_ROOT>\frontend
     npm install
     npm start
     ```

   - After successful startup, **keep this terminal running and do not execute any other commands**. Any attempt to chain commands (e.g., via `&&`) is considered incorrect usage.

3. **Prepare Operational Terminal (Terminal 3, Interactive Commands Only)**:
   - Create a third **new** terminal window (Terminal 3, dedicated to all subsequent interactive commands).
   - Execute the following commands (Windows `cmd.exe`):

     ```cmd
     cd /d <YOUR_PROJECT_ROOT>
     echo Operational Terminal Ready
     ```

   > **Note**: Replace `<YOUR_PROJECT_ROOT>` with your actual project directory path (e.g., `c:\Zhuang\Source\health_platform` or `D:\Projects\health_platform`)

   - From now on:
     - **All tests, scripts, and one-time commands (e.g., `python -m pytest -q`) are only allowed in Terminal 3**;
     - Terminal 1 is for backend only, Terminal 2 is for frontend only. Never execute other commands in these two terminals to avoid the "Terminate batch job (Y/N)?" prompt that could accidentally stop services.

```

# Windows setup

Open the folder containing `app.py` in VS Code. Use Python 3.11 or 3.12.

1. Create an environment and install dependencies:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

2. If `.env` does not exist, copy `.env.example` to `.env`. Fill real keys and your working chat model ID **locally**. Do not share `.env`. Preserve it when updating an existing project.

3. Run offline checks:

   ```powershell
   .\.venv\Scripts\python.exe check_setup.py
   .\.venv\Scripts\python.exe -m pytest -q
   .\.venv\Scripts\python.exe ingest.py --collection ai --dry-run
   ```

4. For a new installation, index the public lessons (uses provider credits):

   ```powershell
   .\.venv\Scripts\python.exe ingest.py --collection ai
   ```

   Keep the `.luma` folder of an existing working installation. Documentation/test changes alone need no re-indexing.

5. Start the app:

   ```powershell
   .\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
   ```

   Open the printed address. AI learning — public is the only selectable collection. Stop with Ctrl+C.

6. Before GitHub submission, exclude `.env`, `.venv`, `.luma`, private documents, and backup copies. See README for hosting requirements and limitations.

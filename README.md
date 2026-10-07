# Local Notebook

A private, local NotebookLM-inspired research app. This clean package contains only the files needed to run the app in Chrome.

## Start on Windows

Open PowerShell in this folder and run:

```powershell
py -m pip install -r requirements.txt
py server.py
```

Open Chrome at:

```text
http://127.0.0.1:8787
```

You can also double-click `start-notebook.bat`.

For better answers, keep Ollama running separately:

```powershell
ollama run llama3.2:3b
```

The frontend is self-contained in `public/index.html`; no separate CSS or JavaScript files are required.

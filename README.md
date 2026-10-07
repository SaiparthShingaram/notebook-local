# Local Notebook

A privacy-focused, offline NotebookLM-inspired research assistant that runs locally on Windows using Python and Ollama.

Upload your own documents, ask questions in natural language, and receive answers grounded in your local sources. Your documents and notebook memory remain on your computer.

## Features

- Upload PDF, Markdown, TXT, CSV, and JSON files
- Ask questions about uploaded documents
- Local AI answers using Ollama
- Source-grounded answers with document citations
- Notebook memory for project context and answer preferences
- Add pasted text as a source
- Search, select, and remove sources
- Multiple notebooks
- NotebookLM-inspired web interface
- No cloud account required
- Runs locally at `127.0.0.1:8787`

## Requirements

- Windows 10 or Windows 11
- Python 3.10 or newer
- Ollama
- Recommended: 16 GB RAM

## Installation

### 1. Install Python dependencies

Open PowerShell in the project folder:

```powershell
py -m pip install -r requirements.txt
```

### 2. Install Ollama

Download Ollama for Windows:

https://ollama.com/download/windows

Download the recommended lightweight model:

```powershell
ollama pull llama3.2:3b
```

If Windows does not recognize the `ollama` command, use:

```powershell
& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" pull llama3.2:3b
```

## Run the application

Start Ollama in one PowerShell window:

```powershell
ollama run llama3.2:3b
```

Keep that window open.

Open a second PowerShell window in the folder containing `server.py`:

```powershell
py server.py
```

Open the application in Chrome:

```text
http://127.0.0.1:8787
```

You can also double-click:

```text
start-notebook.bat
```

## How to use

1. Click **Add your first source** or **Browse files**.
2. Upload a PDF, Markdown, TXT, CSV, or JSON file.
3. Wait for the document to be processed locally.
4. Ask a question in the chat box.
5. Check the **Extracted from** section to see which documents were used.
6. Add project context or answer preferences in **Notebook memory**.
7. Search, select, or remove sources when needed.

## Project structure

```text
notebook-local/
├── server.py
├── requirements.txt
├── start-notebook.bat
├── open-notebook-in-chrome.bat
├── README.md
└── public/
    └── index.html
```

The frontend is self-contained in `public/index.html`.

## Privacy

This project is designed for local use:

- Uploaded documents are processed on your computer.
- Notebook memory is stored locally in your browser.
- Ollama runs the AI model locally.
- No cloud account is required.
- Your documents are not automatically uploaded to an online service.

Do not upload private documents, personal notes, API keys, or model files to a public GitHub repository.

## Limitations

- Answer quality depends on document quality, PDF extraction, retrieval, and the Ollama model.
- Scanned or image-only PDFs may require OCR.
- Large documents may require additional processing time and memory.
- GitHub stores the code but does not run Python or Ollama.
- The system has not been formally benchmarked for accuracy yet.

## Troubleshooting

### Browser says “connection refused”

Make sure the Python server is running:

```powershell
py server.py
```

Then open:

```text
http://127.0.0.1:8787
```

### `server.py` cannot be found

Run the command from the folder that directly contains:

```text
server.py
public
```

Check the current folder:

```powershell
dir
```

### `ollama` is not recognized

Use the full Ollama path:

```powershell
& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" run llama3.2:3b
```

### PDF extraction fails

Install the required dependencies again:

```powershell
py -m pip install -r requirements.txt
```

Then restart the Python server.

## Future improvements

- Semantic embeddings and vector search
- Hybrid keyword and semantic retrieval
- OCR support for scanned PDFs
- Better page-level citations
- Retrieval accuracy benchmarking
- Voice-based questions
- Multi-agent research workflows

## License

This project is intended for learning and personal development. Add an open-source license, such as the MIT License, if you plan to publish and share the project publicly.

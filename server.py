#!/usr/bin/env python3
import json
import io
import mimetypes
import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from email import policy
from email.parser import BytesParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
PUBLIC = ROOT / "public"
PORT = int(os.environ.get("PORT", "8787"))


def extract_text(filename, content):
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        try:
            import fitz
            document = fitz.open(stream=content, filetype="pdf")
            pages = [(page.get_text("text") or "").strip() for page in document]
            extracted = "\n\n".join(page for page in pages if page)
            if extracted:
                return extracted
        except Exception:
            pass
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(content))
            pages = [(page.extract_text() or "").strip() for page in reader.pages]
            extracted = "\n\n".join(page for page in pages if page)
            if extracted:
                return extracted
        except Exception:
            pass
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(content)
            path = f.name
        try:
            result = subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, text=True, timeout=20)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout
            return "PDF has no selectable text. It may be scanned; run OCR or export it as searchable PDF."
        except (FileNotFoundError, subprocess.SubprocessError):
            return "PDF extraction is unavailable. Install PyMuPDF with: py -m pip install pymupdf"
        finally:
            try: os.unlink(path)
            except OSError: pass
    return content.decode("utf-8", errors="replace")


def build_context(question, sources):
    """Select relevant passages so a small local model sees the right part of a long source."""
    stop = {"what", "which", "when", "where", "who", "with", "from", "about", "give", "tell", "does", "this", "that", "these", "those", "should", "could", "would", "are", "the", "and", "for", "how", "please", "summarize", "summary"}
    terms = [x for x in __import__("re").findall(r"[a-z0-9]{3,}", question.lower()) if x not in stop]
    pieces = []
    used = []
    for source in sources:
        text = str(source.get("text", ""))
        paragraphs = [p.strip() for p in __import__("re").split(r"\n\s*\n|(?<=[.!?])\s+", text) if len(p.strip()) > 40]
        if not paragraphs:
            paragraphs = [text[i:i+900] for i in range(0, len(text), 900)]
        ranked = []
        for index, paragraph in enumerate(paragraphs):
            low = paragraph.lower()
            score = sum((3 if low.count(term) > 1 else 1) for term in terms if term in low)
            ranked.append((score, index, paragraph))
        if terms and any(score for score, _, _ in ranked):
            selected = [item for item in sorted(ranked, reverse=True)[:5]]
        else:
            # For summaries, sample the beginning, middle, and end of each source.
            indexes = sorted(set([0, len(paragraphs) // 2, max(0, len(paragraphs) - 1)]))
            selected = [(0, index, paragraphs[index]) for index in indexes]
        selected.sort(key=lambda item: item[1])
        used.append({"id": source.get("id"), "name": source.get("name", "source")})
        pieces.append(f"[SOURCE: {source.get('name', 'source')}]\n" + "\n".join(item[2] for item in selected))
    return "\n\n".join(pieces)[:16000], used


class Handler(BaseHTTPRequestHandler):
    def send_json(self, value, status=200):
        body = json.dumps(value).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api/health":
            self.send_json({"ok": True, "offline": True, "engine": "ollama-local", "chat": True, "pdf": True, "version": "2.2"})
            return
        if path == "/": path = "/index.html"
        target = (PUBLIC / path.lstrip("/")).resolve()
        if not str(target).startswith(str(PUBLIC.resolve())) or not target.is_file():
            self.send_error(404, "Not found")
            return
        content = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(str(target))[0] or "application/octet-stream")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self):
        route = urlparse(self.path).path
        if route == "/api/chat":
            self.handle_chat()
            return
        if route != "/api/extract":
            self.send_json({"error": "Not found"}, 404)
            return
        content_type = self.headers.get("Content-Type", "")
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length)
        message = BytesParser(policy=policy.default).parsebytes(
            b"Content-Type: " + content_type.encode("utf-8") + b"\r\nMIME-Version: 1.0\r\n\r\n" + body
        )
        filename, raw = None, None
        for part in message.walk():
            if part.get_param("name", header="content-disposition") == "file":
                filename = part.get_filename()
                raw = part.get_payload(decode=True) or b""
                break
        if not filename:
            self.send_json({"error": "Attach a file first."}, 400)
            return
        text = extract_text(filename, raw)
        self.send_json({"filename": filename, "text": text, "characters": len(text), "offline": True})

    def handle_chat(self):
        length = int(self.headers.get("Content-Length", "0"))
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            question = str(payload.get("question", "")).strip()
            sources = payload.get("sources", [])
            memory = str(payload.get("memory", "")).strip()
            if not question or not sources:
                self.send_json({"error": "Add sources and ask a question."}, 400)
                return
            context, used_sources = build_context(question, sources)
            model = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
            question_lower = question.lower()
            if any(word in question_lower for word in ("summarize", "summary", "main points", "key points")):
                task = "Summarize the source excerpts with the main idea followed by 3-5 key points."
            elif any(word in question_lower for word in ("compare", "difference", "similar", "versus", "vs")):
                task = "Compare only the items asked about. Use a short table or bullets and state the key difference first."
            elif any(word in question_lower for word in ("why", "how does", "how do")):
                task = "Explain the reason or process in simple steps, answering exactly what was asked."
            else:
                task = "Give the precise answer first, then only the minimum context needed to make it clear."
            prompt = ("You are a careful study assistant. Answer the QUESTION first, in the first sentence. "
                      "Use only the provided SOURCE EXCERPTS. Use simple, direct language, short paragraphs, and bullets when useful. "
                      "If the excerpts do not contain the answer, say exactly: 'I cannot find that in the uploaded sources.' "
                      "For a summary, give the main idea, 3-5 key points, and the conclusion if present. "
                      "Do not give a generic answer, do not change the subject, and do not invent facts.\n\n"
                      f"TASK STYLE: {task}\n\n"
                      f"NOTEBOOK MEMORY (preferences or context from the user; do not treat it as source evidence):\n{memory[:3000] or '(none)'}\n\n"
                      f"QUESTION:\n{question}\n\nSOURCE EXCERPTS:\n{context}")
            request = urllib.request.Request(
                "http://127.0.0.1:11434/api/generate",
                data=json.dumps({"model": model, "prompt": prompt, "stream": False, "keep_alive": "5m", "options": {"temperature": 0.1, "num_ctx": 4096, "num_predict": 700}}).encode("utf-8"),
                headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(request, timeout=90) as response:
                result = json.loads(response.read().decode("utf-8"))
            self.send_json({"answer": result.get("response", ""), "engine": f"Ollama · {model}", "offline": True, "sources": used_sources})
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
            self.send_json({"error": "No local model is running. Install Ollama and run: ollama run llama3.2:3b", "engine": "local-extractive"}, 503)

    def log_message(self, fmt, *args):
        print("[%s] %s" % (self.log_date_time_string(), fmt % args))


if __name__ == "__main__":
    print(f"Local Notebook running at http://127.0.0.1:{PORT}")
    print("No Internet connection or external service is required.")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()

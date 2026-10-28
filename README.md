# RAG Chat

A document question-answering app built with FastAPI, LangChain, Qdrant, and a plain HTML/CSS/JavaScript frontend. Ask questions about a PDF and get AI-generated answers alongside the document text retrieved to support them.

## What the system does

1. **Read:** The indexing script loads a PDF from `app/data/sample.pdf`.
2. **Split:** It divides extracted text into chunks of 1,000 characters, without overlap.
3. **Embed:** The local `sentence-transformers/all-MiniLM-L6-v2` model converts chunks into 384-dimensional vectors.
4. **Store:** Qdrant stores those vectors and their document text in `sample_collection`.
5. **Retrieve:** When you ask a question, the backend searches Qdrant for related document chunks.
6. **Answer:** The Groq model receives the question and retrieved context, then generates an answer. The interface displays the answer and lets you expand the retrieved context.

The default chat uses Groq's `openai/gpt-oss-20b` model. Other existing routes use Hugging Face models. Embeddings run locally; the question and retrieved document excerpts are sent to the chosen cloud model for answer generation.

## Features

- Responsive chat interface with suggested questions.
- Formatted answers with headings, lists, emphasis, code blocks, and tables.
- Expandable source context and a copy-answer button.
- Up to 25 recent answers saved in your browser.
- Automatic browser opening when Uvicorn startup succeeds.
- FastAPI's interactive API documentation at `/docs`.

## Requirements

- Python with `venv` and `pip`. The existing local environment runs Python 3.14; dependency compatibility can vary by Python version and platform.
- Docker Desktop with its engine running, or another Docker installation with Docker Compose.
- A Groq API key and a Hugging Face access token. The backend imports all existing model routes during startup, so configure both.
- Internet access for the initial embedding-model download and cloud AI requests.
- A text-based PDF. Scanned image-only PDFs need OCR before this ingestion workflow can extract useful text.

## 1. Create your Python environment

Clone your GitHub repository, open a terminal in its root folder, then run:

### Windows PowerShell

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell prevents activation, use the environment's executable directly:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

The remaining Python commands assume the environment is activated. On Windows, you can substitute `.\venv\Scripts\python.exe` for `python` and run Uvicorn as `python -m uvicorn`.

## 2. Configure API keys

Copy the example configuration to `.env` in the project root. Keep an existing `.env` if you already configured it.

```powershell
Copy-Item .env.example .env
```

On macOS/Linux, use `cp .env.example .env`.

Fill in your own values:

```dotenv
HUGGINGFACEHUB_API_TOKEN=your_hugging_face_token
GROQ_API_KEY=your_groq_api_key
OPEN_API_KEY=
```

`OPEN_API_KEY` belongs to a commented-out OpenAI embedding alternative and is not required by the active embedding pipeline. You can optionally set `HF_TOKEN` to authenticate Hugging Face Hub downloads as well.

Never commit `.env`, credentials, or private PDFs to GitHub. Ensure your repository's ignore rules exclude `.env`, `venv/`, `__pycache__/`, and local database data. An `.env.example` with empty values is safe to share.

## 3. Start the vector database

Open Docker Desktop and wait until its engine is ready. From the project root:

```powershell
docker compose up -d
```

The supplied Compose file starts one Qdrant service named `vector-db`, available on port **6333**. No SQL database is required.

Useful commands:

```powershell
docker compose ps
docker compose logs --tail 50 vector-db
docker compose stop
```

Check database status at [http://localhost:6333/collections](http://localhost:6333/collections). Before indexing, an empty collection list is normal.

### Preserve data when recreating containers

The supplied Compose file has **no active persistent volume**. Stopping and starting the same container retains its data, but removing or recreating it can lose your index. To use persistent storage, add a project-root `compose.override.yaml` before the first database start:

```yaml
services:
  vector-db:
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  qdrant_data:
```

Docker Compose automatically reads this alongside `docker-compose.yml`. If you add it after indexing, the new volume starts empty; run indexing again. Do not use `docker compose down -v` if you want to retain named-volume data.

## 4. Place and rename your document

The existing indexing script reads this exact path:

```text
app/
  data/
    sample.pdf
```

To use your own PDF without changing backend code:

1. Create `app/data/` if it does not exist.
2. Copy your PDF into that folder.
3. Rename the copied file to **`sample.pdf`**. For example, `research-notes.pdf` becomes `app/data/sample.pdf`.
4. Keep any original PDF you want to retain elsewhere before replacing the existing sample.

The folder and filename matter: the script does not automatically scan for other PDFs. Renaming the file alone does not update the database; run indexing next.

## 5. Index the PDF

With Qdrant running:

```powershell
python app/index.py
```

Wait for:

```text
Vector store created and documents embedded successfully.
```

The first run downloads the embedding model. Larger documents can take several minutes. The script creates or adds documents to the **`sample_collection`** Qdrant collection, which must exist before the backend starts.

### Replace the indexed document

Rerunning the script can append chunks to the existing collection. It does not automatically remove old chunks or deduplicate repeated indexing. If you want answers from only a replacement PDF:

1. Stop Uvicorn with Ctrl+C.
2. Back up anything you need from the existing index.
3. Delete only `sample_collection` using Qdrant's `DELETE /collections/sample_collection` endpoint. This permanently removes the indexed text in that collection; it does not delete your PDF.
4. Place the replacement file at `app/data/sample.pdf`.
5. Run `python app/index.py` and wait for completion.
6. Start the app again.

Do not delete the collection just to restart the app; an existing index can be reused.

## 6. Run the app

```powershell
python -m uvicorn ui:app --reload
```

After startup succeeds, your default browser opens at [http://127.0.0.1:8000](http://127.0.0.1:8000).

- **UI and automatic browser opening:** `ui:app`
- **Original backend alone:** `app.main:app`
- **API documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

The UI entry point serves the HTML frontend and mounts the original backend. Existing files in `app/` and `routes/` are unchanged. It also configures UTF-8 console output to prevent Windows errors when the backend prints model-generated Unicode text.

Choose another port:

```powershell
python -m uvicorn ui:app --reload --port 8080
```

For a remote server, disable automatic browser opening and omit development reload:

```powershell
$env:FOLIO_OPEN_BROWSER = '0'
python -m uvicorn ui:app --host 0.0.0.0 --port 8000
```

On macOS/Linux:

```bash
FOLIO_OPEN_BROWSER=0 python -m uvicorn ui:app --host 0.0.0.0 --port 8000
```

This app has no built-in user authentication. Add appropriate access controls before publishing a public instance or using private documents.

## Using the interface

Type a question or select a suggestion, then press the send arrow or **Ctrl/Cmd + Enter**. Answers display Markdown formatting, including lists, headings, tables, and code blocks. Expand **Explore retrieved context** to inspect the text used by the model. Retrieved page labels come from the backend's document metadata and may be zero-based.

Use **New conversation** or **Alt + N** to clear the visible chat. Recent entries remain in browser storage; the reset icon beside recent conversations clears saved history. Each question is sent independently: the backend does not receive the preceding conversation as model memory.

There is no PDF upload endpoint in the existing backend. Use the local placement and indexing steps above instead. Retrieved context supports reviewing answers, but does not guarantee every generated claim is correct.

## API

The interface sends the question as a URL query parameter, matching the existing backend:

```http
POST /grok/query/?question=What%20are%20the%20main%20ideas%3F
```

Response:

```json
{
  "Question": "What are the main ideas?",
  "Answer": "An answer generated from retrieved document context.",
  "Context": "Page 0: Supporting document text..."
}
```

Existing query routes:

| Route | Provider |
| --- | --- |
| `/grok/query/` | Groq; used by the frontend |
| `/query/query/` | Hugging Face |
| `/workingquery/query/` | Hugging Face |

The repeated `query` in two URLs comes from the existing router prefixes.

## Project structure

```text
app/
  main.py                 Original FastAPI application
  index.py                PDF ingestion and embedding script
  data/sample.pdf         PDF read by the indexing script
routes/                   Existing question-answering routes
static/
  style.css               Responsive interface and answer formatting
  app.js                  Chat requests, rendering, browser history
  vendor/                 Local Markdown renderer and HTML sanitizer
index.html                HTML frontend
ui.py                     UI adapter and automatic browser launcher
tests/test_ui.py          Isolated UI adapter checks
docker-compose.yml        Qdrant service
requirements.txt          Python dependencies
.env.example              Empty configuration template
```

## Troubleshooting

| Problem | What to check |
| --- | --- |
| Docker engine connection error | Start Docker Desktop and wait for the engine before running Compose. |
| Connection refused at `localhost:6333` | Run `docker compose up -d` and check the container logs. |
| `sample_collection` missing | Run `python app/index.py` successfully before starting Uvicorn. |
| PDF not found | Confirm the exact path is `app/data/sample.pdf`, including the `.pdf` extension. |
| Empty or irrelevant answers | Check that the PDF contains selectable text and that you indexed the intended document. |
| Old document appears in answers | Repeated indexing adds data. Follow the replacement-index steps to remove old chunks. |
| Slow startup | Existing backend modules load embedding models and connect to external services during import. Wait for `Application startup complete`. |
| Provider authentication, quota, or model error | Check the server log, keys in `.env`, provider quota, and model access. Restart after changing keys. |
| Windows Unicode encoding error | Launch with `ui:app`, which configures UTF-8 output. |
| Unformatted answers or old styling | Hard-refresh with Ctrl+F5 so the updated frontend assets load. |
| Port already in use | Stop the other process or use `--port 8080`. |

## Checks

```powershell
python -m unittest discover -s tests -v
node --check static/app.js
node --test tests/markdown.test.cjs
```

Node.js is only needed for the JavaScript checks; the application does not need a Node server or frontend build. UI adapter tests use a mock backend and do not call cloud AI services. Markdown is rendered locally with Marked and sanitized with DOMPurify before display.

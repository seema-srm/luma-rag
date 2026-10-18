# Luma — AI Learning Assistant

Luma helps learners ask questions about AI lessons and explore the passages cited by its answers. The name suggests light and clarity in learning.

The current app offers **AI learning — public**, beginner-friendly and technical explanation styles, highlighted questions, newest-first Q&A, a loading indicator, and expandable sources. The knowledge base contains six Microsoft lessons. No instructor materials are included.

## Quick start

Use Python 3.11 or 3.12. From the folder containing `app.py`, run in Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Only copy the template if `.env` does not already exist. Fill your Fireworks API key, an accessible Fireworks chat model ID, and Pinecone API key locally. Never commit real keys. Leave optional LangSmith tracing off initially.

```powershell
.\.venv\Scripts\python.exe check_setup.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe ingest.py --collection ai --dry-run
.\.venv\Scripts\python.exe ingest.py --collection ai
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
```

Open the address printed by Streamlit. Tests and the dry run make no provider calls. Real ingestion sends public document text to Fireworks for embeddings and stores passages/vectors in Pinecone. Real questions use provider credits. Stop the server with Ctrl+C. On macOS/Linux use `python3` to create the environment and `.venv/bin/python` thereafter.

For an existing working installation, preserve `.env` and `.luma`; documentation/test cleanup alone requires no re-indexing.

## Tools and architecture

| Tool | Role |
| --- | --- |
| Streamlit | Chat interface, document browser, and session state |
| LangChain packages | Document representation, overlapping text splitting, and provider adapters |
| Fireworks AI | Hosted embeddings and structured answer generation |
| Pinecone | Vector storage and semantic retrieval |
| LangGraph | Routing, retrieval, generation, and citation-format checks |
| LangSmith | Optional tracing and public-example evaluation |

**Import:** files → extracted text → overlapping chunks → Fireworks embeddings → Pinecone snapshot → local active-snapshot manifest.

**Question:** input → feedback/greeting routing → contextual query → semantic search → similarity threshold → generated answer → citation-format check → source panels.

Normal app use calls the configured providers. Offline tests explicitly replace providers. Replit, Tavily, Nebius, and LlamaIndex are not required.

## Learning materials and updates

The six lessons are from [Microsoft's Generative AI for Beginners](https://github.com/microsoft/generative-ai-for-beginners): introduction to generative AI, comparing LLMs, prompt fundamentals, advanced prompts, RAG/vector databases, and AI agents. Source URLs and license information are retained in metadata sidecars and `documents/public/ai/NOTICE.txt`.

Add or replace documents in `documents/public/ai/`, rerun ingestion, then clear the conversation. PDF, DOCX, TXT, and MD are supported. Scanned PDFs need OCR; PPTX is not supported. PDF page metadata is preserved; complex DOCX layout is not reconstructed. Files named `README.md` and `NOTICE.txt` are excluded by the loader. Optional `lesson.meta.json` sidecars provide title, URL, and license. Inspect extraction in Learning library.

The sample currently produces 130 chunks; document/splitter changes can change the count. Snapshot identity includes document content and embedding model. Added, replaced, or removed documents create a new active snapshot after successful ingestion. Failed uploads preserve the previous active manifest. Older remote snapshots are retained and may consume storage.

Internal SDET sample documents and private-collection code remain for regression coverage; those collections are **not selectable in the current interface**. Do not put restricted documents in the public collection. The sixth lesson has an imperfect display title inherited from its metadata; it is still the AI agents lesson.

## Verification

The cleaned package passed **55 offline checks** on Linux/Python 3.12: **53 functional checks and 2 characterization probes documenting limitations**. This is not a claim of 51 answer-quality safeguards. Providers are simulated and no API keys are needed. See `TEST-RESULTS.txt`; `requirements-tested.txt` records installed versions and `requirements.txt` defines installation ranges.

Coverage includes document parsing, collection separation, feedback routing, follow-up context, explanation-style forwarding, citation validation, private tracing/upload guards, snapshot updates, failed-ingestion recovery, and Streamlit interface state/navigation. The stale missing-inline-citation test now checks the existing Sources-footer behavior. The restored answer generation and retrieval logic is preserved. Hosting adds public AI snapshot fallback resolution, while a local ingestion manifest takes priority.

Live Fireworks/Pinecone quality/connectivity, credits/model access, browser CSS, visible spinner animation, focus borders, scrolling, accessibility, and hosting were not verified by these offline tests.

## Limitations

- Source IDs and citation formatting are checked, **not whether every claim follows from the cited passage**. A Sources footer is appended when a supported response has valid IDs but no inline references; this does not establish factual support.
- Similarity scores do not guarantee relevance. The model may return an incorrect answer or decline despite relevant documents. Review the sources.
- Follow-up context is limited to the previous question. That previous question also reaches generation, so topic changes may be affected. Clear the conversation when needed.
- Defensive metadata handling could be improved: custom metadata from a future loader could overwrite reserved retrieval fields. The supplied loader does not normally create such metadata.
- Provider availability, quotas, balance, network access, and model support affect operation. The app has no application-level authentication or usage limits.

## Optional tracing/evaluation

With public AI data, deliberately set your LangSmith key and enable tracing, then run `evaluate.py`. This makes live provider calls and sends questions/results to LangSmith. Traces may contain questions, excerpts, and answers. The five starter examples measure expected-source hits and citation formatting, not comprehensive semantic accuracy. Private tracing is disabled in the existing runtime.

## Submission and hosting

This package contains code, public documents, tests, and configuration templates. Real API keys, private documents, virtual environments, local `.luma` manifests, and obsolete code copies are excluded. `deployment/ai.json` deliberately includes only the public-demo snapshot identifiers and dimensions; it has no credentials.

GitHub provides source code; it does not make a localhost app available online. The repository now includes the public AI snapshot reference at `deployment/ai.json`. Hosting still requires private server-side Fireworks/Pinecone credentials, an accessible matching remote index, and deployment through the host. The code is prepared for deployment but a live service has not been verified. See `DEPLOYMENT.md`. Keep secrets private on the host. Once hosted correctly, visitors can use the app without their own keys, consuming the owner's provider credits.

Inspect staged files before committing. `.gitignore` excludes secrets, private document contents, generated manifests, caches, and backup patterns; it does not erase previously tracked files or Git history.

## Main files

| File | Purpose |
| --- | --- |
| `app.py` | Learning interface |
| `luma/graph.py` | Routing, retrieval, generation, citation checks |
| `luma/runtime.py` | Active snapshot and tracing controls |
| `luma/services.py` | Provider connections |
| `luma/documents.py` | Extraction, chunking, snapshot identity |
| `ingest.py` | Explicit ingestion command |
| `check_setup.py` | Dependency/configuration presence checks |
| `diagnose_luma.py` | Optional live diagnostic without raw answers/keys |
| `evaluate.py` | Optional LangSmith evaluation |
| `.env.example` | Configuration template with blank keys |
| `tests/` | Offline functional tests and characterization probes |

After re-indexing locally, update `deployment/ai.json` from the new public `.luma/ai.json` before redeploying. Never replace it with a private collection manifest. Changing the hosted embedding model requires compatible re-indexing.

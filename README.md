# AI Autofill Agent 🤖✨

> **Autonomous Browser Agent powered by Python, LLMs, RAG, Playwright, and Human-in-the-Loop Verification.**

An AI-powered browser agent that autonomously perceives complex web forms, analyzes questions, and fills fields using personalized user context, persistent memory, and RAG retrieval. Features an interactive Human-in-the-Loop (HITL) review console to review and edit entries before submission.

---

## 🌟 Key Highlights

- **🧠 Multi-Tier Memory & RAG Retrieval**:
  - **Structured Profile Store**: Fast exact matching for candidate contact, addresses, education, work authorization, and links.
  - **Vector Knowledge Base (RAG)**: Chunk-level semantic retrieval over resumes, cover letters, and STAR-method behavioral interview answers.
- **🌐 Autonomous Browser Perception & Execution**:
  - Powered by **Playwright (Python)**.
  - Understands text inputs, textareas, selects, multi-choice radio groups, date pickers, and consent checkboxes.
  - Multi-attribute DOM inspection: labels (`for`, aria-label, aria-labelledby, surrounding context, placeholders).
  - Human-like typing, scrolling, and real-time glowing visual highlights.
- **🛡️ Human-in-the-Loop (HITL) Verification**:
  - Review table with confidence scores, source context (Profile vs RAG vs LLM), and AI reasoning.
  - Full control to edit suggested values inline, approve all, toggle individual fields, or abort before execution.
- **⚡ Dual Mode Interface**:
  - **Glassmorphic Web Dashboard**: Control center with live logs, screenshot preview, profile editor, and interactive RAG semantic query playground.
  - **Rich CLI Terminal**: Beautiful interactive terminal table with inline keyboard shortcuts (`[A]`pprove, `[E]`dit, `[S]`kip, `[C]`ancel).
- **🧪 Built-in Realistic Test Forms**:
  - Includes a complex, realistic multi-step job application form for end-to-end local testing.

---

## 🏗️ Architecture

```
AI_autofill_agent/
│
├── config.py                 # Central configuration (LLM provider, browser, paths)
├── cli.py                    # Interactive Rich Terminal CLI runner
├── main.py                   # Unified runner (Web Dashboard or CLI)
├── requirements.txt
│
├── memory/
│   ├── profile_store.py      # Structured personal profile persistence & schemas
│   ├── vector_store.py       # RAG Vector store (ChromaDB + semantic similarity)
│   ├── document_loader.py    # Document chunker & loader
│   └── data/                 # Sample profile & documents (resume.md, behavioral_stories.md)
│
├── browser/
│   ├── controller.py         # Playwright browser lifecycle manager
│   ├── extractor.py          # Intelligent Form Field Extractor (DOM inspection)
│   └── actions.py            # Visual highlighting, typing, and selecting
│
├── agent/
│   ├── llm_provider.py       # Multi-provider (Gemini, OpenAI, Ollama, & Mock)
│   ├── autofill_engine.py    # Form analysis, RAG query, reasoning, & execution
│   └── prompts.py            # System prompts & structured output extraction
│
├── hitl/
│   └── review_manager.py     # Interactive Human-in-the-Loop review system
│
└── server/
    ├── app.py                # FastAPI backend API
    ├── test_forms.py         # Built-in realistic Job Application form
    └── static/               # Web dashboard (HTML, CSS, JS)
```

---

## 🚀 Quick Start

### 1. Installation

```bash
git clone <your-repo-url>
cd AI_autofill_agent

# Install dependencies
pip install -r requirements.txt

# Install Playwright Chromium browser binaries
python -m playwright install chromium
```

### 2. Configuration (Optional)

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Configure your preferred LLM provider (`gemini`, `openai`, `ollama`, or `mock`):
```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```
*Note: AI Autofill Agent comes equipped with a built-in semantic provider that works out of the box even without external API keys!*

---

## 💻 Usage

### Web Dashboard Mode (Recommended)

Launch the dashboard server:
```bash
python main.py
```
Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser:
1. Click **"Load Demo Job Form"** or enter any target URL.
2. Click **"Scan & Plan Autofill"** to perceive the form and query RAG memory.
3. Review AI-proposed entries, confidence scores, and reasoning in the **HITL Verification Console**.
4. Edit any field inline, then click **"Execute Autofill (Approved)"** to watch Playwright fill the form in real time!

### Interactive CLI Mode

Run against the built-in demo form:
```bash
python cli.py --demo
```

Or run against any custom web URL:
```bash
python cli.py --url https://example.com/application-form
```

Options:
- `--headless`: Run browser in the background.
- `--auto-approve`: Skip interactive verification prompts.

---

## 📄 License

MIT License. Built for autonomous agentic browser workflows and smart autofilling.

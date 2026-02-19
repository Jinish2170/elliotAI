# Technology Stack

**Analysis Date:** 2026-02-19

## Languages

**Primary:**
- Python 3.10+ - Backend/Veritas core (`veritas/`, `backend/`)
- TypeScript 5.x - Frontend (`frontend/src/`)

**Secondary:**
- JavaScript - Frontend runtime (Next.js), configuration files
- Shell/Bash - Launch scripts (`start.bat`, `stop.bat`)
- CSS - Styling via TailwindCSS

## Runtime

**Environment:**
- Python virtual environment (`.venv/`)
- Node.js (for Next.js development/production)

**Package Manager:**
- Python: `pip` with requirements.txt
- Frontend: `npm` with package-lock.json

## Frameworks

**Core Backend:**
- FastAPI 0.115.0 - REST API framework (`backend/main.py`)
- Uvicorn 0.30.0[standard] - ASGI server
- WebSockets 12.0 - Real-time audit streaming (`backend/routes/audit.py`)
- Pydantic 2.9.0 - Data validation

**AI/ML Agents:**
- LangChain >=0.3.0 - LLM orchestration framework
- LangGraph >=0.2.0 - State machine for agent orchestration (`veritas/core/orchestrator.py`)
- OpenAI >=1.0.0 - NVIDIA NIM (OpenAI-compatible) API client (`veritas/core/nim_client.py`)

**Browser Automation:**
- Playwright >=1.40.0 - Headless browser for forensic screenshot capture (`veritas/agents/scout.py`)
- Stealth mode: Anti-detection scripts for bypassing bot detection

**Vector Storage:**
- LanceDB >=0.4.0 - Disk-based vector database (SSD-backed, not in-memory)
- Sentence-Transformers >=2.2.0 - Local embeddings (all-MiniLM-L6-v2, ~90MB)

**Graph & Analysis:**
- NetworkX >=3.2 - Knowledge graph construction
- Matplotlib >=3.8.0 - Graph visualization
- Rank-BM25 >=0.2.2 - Hybrid search
- Numpy >=1.24.0 - Numerical operations

**Reporting:**
- WeasyPrint >=60.0 - PDF report generation
- Jinja2 >=3.1.0 - Templating engine

**UI - Python:**
- Streamlit >=1.30.0 - Alternative web UI (`veritas/ui/app.py`)

**UI - Frontend:**
- Next.js 16.1.6 - React framework with App Router
- React 19.2.3 - UI library
- TailwindCSS 4 - Styling framework
- Zustand 5.0.11 - State management (`frontend/src/lib/store.ts`)
- Framer Motion 12.34.0 - Animations
- Radix UI 1.4.3 - Component primitives
- Lucide React 0.564.0 - Icons
- Recharts 3.7.0 - Data visualization

**Testing:**
- Pytest >=7.4.0 - Test runner
- Pytest-asyncio >=0.23.0 - Async test support
- Httpx >=0.25.0 - HTTP test client

## Key Dependencies

**Critical:**
- fastapi>=0.115.0 - Core API framework
- langchain>=0.3.0 - Agent orchestration
- langgraph>=0.2.0 - State machine for audit pipeline
- playwright>=1.40.0 - Browser automation
- openai>=1.0.0 - NVIDIA NIM API client
- lancedb>=0.4.0 - Evidence vector storage
- sentence-transformers>=2.2.0 - Local embeddings

**Infrastructure:**
- python-dotenv>=1.0.0 - Environment configuration
- pydantic>=2.5.0 - Data validation
- tenacity>=8.2.0 - Retry logic with exponential backoff
- aiohttp>=3.9.0 - Async HTTP client
- python-whois>=0.9.0 - Domain WHOIS lookups
- dnspython>=2.4.0 - DNS queries
- Pillow>=10.0.0 - Image processing
- pytesseract>=0.3.10 - OCR fallback

**Frontend:**
- next: 16.1.6 - React framework
- react: 19.2.3 - React core
- tailwindcss: ^4 - CSS framework
- zustand: ^5.0.11 - State management
- framer-motion: ^12.34.0 - Animations

## Configuration

**Environment:**
- Via `python-dotenv` loaded from `.env` file (`veritas/.env`)
- Template provided at `veritas/.env.template`
- Settings centralized in `veritas/config/settings.py`

**Key configs:**
- `veritas/.env` - Environment variables (never committed to git)
- `package.json` - Frontend dependencies
- `backend/requirements.txt` - FastAPI backend dependencies
- `veritas/requirements.txt` - Core Veritas python dependencies

**Build:**
- Frontend: Next.js build config in `frontend/next.config.ts`
- TypeScript: `frontend/tsconfig.json`
- Tailwind: `frontend/postcss.config.mjs`

## Platform Requirements

**Development:**
- Python 3.10+
- Node.js 18+
- 8GB RAM minimum (tuned for 8GB per requirements)
- SSD recommended for LanceDB performance
- Chromium browser (for Playwright)

**Production:**
- For frontend: Vercel, Netlify, or any Node.js hosting
- For backend: Any container platform (Docker, Kubernetes)
- Vector storage requires persistent disk for LanceDB

---

*Stack analysis: 2026-02-19*

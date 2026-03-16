# Technology Stack
**Analysis Date:** 2026-03-16

## Languages
**Primary:**
- Python 3.x - Backend, AI agents, security analysis
- TypeScript 5.x - Frontend with Next.js 16
- JavaScript (React 19.2.3) - UI framework

**Secondary:**
- HTML/CSS - Terminal-style UI components

## Runtime
**Environment:**
- Node.js 20+ (Next.js 16 requires Node 18+)
- Python 3.10+

**Package Manager:**
- npm 10.x (frontend) - Lockfile present
- pip/venv (backend/veritas) - requirements.txt managed

## Frameworks
**Core:**
- FastAPI 0.115.0 (backend) - REST API + WebSocket endpoints
- Next.js 16.1.6 (frontend) - React 19 full-stack framework
- LangGraph 0.2.0 + LangChain 0.3.0 (AI orchestration)

**Testing:**
- pytest 7.4.0, pytest-asyncio 0.23.0 (Python backend)
- ESLint 9 + TypeScript (frontend)

**Build/Dev:**
- TailwindCSS 4 (styling)
- Uvicorn 0.30.0 (Python ASGI server)
- WebSockets 12.0 (real-time communication)

## Key Dependencies

### Backend/Veritas (Python)
**AI & Vision:**
- openai 1.0.0+ - NVIDIA NIM integration for LLM/VLM APIs
- langchain 0.3.0+, langgraph 0.2.0+ - Agent orchestration
- sentence-transformers 2.2.0 - Local embeddings (all-MiniLM-L6-v2)

**Browser Automation:**
- playwright 1.40.0+ - Headless browser for web scraping

**Data & Storage:**
- pydantic 2.9.0+ - Data validation
- SQLAlchemy 2.x + SQLite - Database ORM and persistence
- lancedb 0.4.0+ - Vector database for embeddings

**Security Analysis:**
- python-whois 0.9.0 - Domain WHOIS lookup
- dnspython 2.4.0 - DNS analysis
- Pillow 10.0.0, pytesseract 0.3.10 - OCR fallback
- opencv-python 4.8.0, scikit-image 0.21.0 - Computer vision

**Reporting:**
- WeasyPrint 60.0, Jinja2 3.1.0 - PDF report generation

**Search & External APIs:**
- tavily-python 0.3.0+ - External search API
- aiohttp 3.9.0 - Async HTTP requests

**Utilities:**
- python-dotenv 1.0.1 - Environment configuration
- tenacity 8.2.0 - Retry logic with exponential backoff
- PySocks 1.7.1 - Proxy/TOR support

### Frontend (TypeScript/React)
**UI Framework:**
- next 16.1.6 - Full-stack React framework
- react 19.2.3, react-dom 19.2.3
- radix-ui 1.4.3 - Accessible UI primitives
- lucide-react 0.564.0 - Icon library

**Styling:**
- tailwindcss 4, @tailwindcss/postcss 4
- tailwind-merge 3.4.0, clsx 2.1.1 - Conditional classes

**State & Effects:**
- zustand 5.0.11 - State management
- framer-motion 12.34.0 - Animations
- recharts 3.7.0 - Data visualization

**Development:**
- typescript 5.x
- shadcn 3.8.4 - UI component library
- tw-animate-css 1.4.0 - Tailwind animations

## Configuration

**Environment:**
- `.env` files (veritas/, backend/, frontend/)
- Environment variables configured via dotenv
- Path: `C:\files\coding dev era\elliot\elliotAI\veritas\.env` (template)
- Key configs: API keys for NVIDIA NIM, Tavily, URLVoid, AbuseIPDB, Google Safe Browsing

**Build:**
- Frontend: next.config.ts (minimal, mostly defaults)
- TypeScript: tsconfig.json with strict mode, JSX support, path aliases (@/*)
- Python: requirements.txt with pinned versions

## Platform Requirements

**Development:**
- Node.js 18+ (frontend build)
- Python 3.10+ with venv
- Playwright browsers (headless by default)
- Tesseract OCR executable (optional, Level 3 fallback)

**Production:**
- FastAPI backend on uvicorn (port 8000)
- Next.js frontend (port 3000)
- SQLite database with WAL mode
- NVIDIA NIM API credits for AI inference
- External API keys: Tavily, URLVoid, AbuseIPDB

---
*Stack analysis: 2026-03-16*
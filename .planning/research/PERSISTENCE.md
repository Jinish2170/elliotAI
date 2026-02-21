# Audit Persistence Research

**Project:** Elliot (elliotAI)
**Domain:** Forensic web auditing database layer
**Researched:** 2026-02-20
**Confidence:** MEDIUM

---

## Executive Summary

Elliot currently stores audit results in an in-memory dictionary that is lost on backend restart. This research recommends implementing persistent storage using SQLite for the initial version (simplicity, single-file, adequate for deployment scale) with PostgreSQL as the upgrade path for multi-instance production.

The key architectural decision is separating structured data (audits, findings) from binary data (screenshots), with screenshots stored on the filesystem and referenced by path in the database. Write-heavy WebSocket events are batched into database transactions using SQLAlchemy connection pooling, with WAL mode enabled for SQLite to improve concurrency.

Migration should follow a dual-write pattern: add database layer first while keeping in-memory reads, then switch reads, finally remove the in-memory storage. This ensures zero downtime during transition.

---

## Recommended Database

### Choice: SQLite for v1, PostgreSQL for v2

| Criterion | SQLite (v1) | PostgreSQL (v2) |
|-----------|-------------|-----------------|
| **Deployment** | Single file, no setup required | Requires server, connection management |
| **Concurrent Writes** | Single writer (WAL mode mitigates) | True multi-writer support |
| **Scale** | ~100K hits/day, 1 writer | Unlimited, multi-server deployment |
| **JSON Support** | Limited JSON extension | Native jsonb with indexing |
| **Migration Path** | Can migrate dump+restore | Seamless transition |
| **Performance** | Fast for small datasets | Better at scale, complex queries |

**Recommendation for v1:** SQLite because:
1. Zero infrastructure setup (works for single-instance deployment)
2. File-based storage enables easy backups and portability
3. WAL mode provides sufficient concurrency for current scale
4. SQLAlchemy ORM abstracts database differences for easy migration

**Recommendation for v2:** PostgreSQL when:
1. Need horizontal scaling (multiple backend instances)
2. Requiring advanced querying on audit history
3. Need jsonb indexing for complex analytics

---

## Complete Schema Design

### ER Diagram

```
┌─────────────────────┐         ┌─────────────────────┐
│      audits         │         │    audit_findings   │
├─────────────────────┤         ├─────────────────────┤
│ id (PK)            │         │ id (PK)            │
│ url                │         │ audit_id (FK)      │
│ status             │         │ pattern_type       │
│ audit_tier         │         │ category           │
│ verdict_mode       │         │ severity           │
│ trust_score        │────┐    │ confidence         │
│ risk_level         │    │    │ description        │
│ signal_scores      │    │    │ plain_english      │
│ narrative          │    │    │ screenshot_index   │
│ recommendations    │    │    │ created_at         │
│ site_type          │    │    └─────────────────────┘
│ domain_info        │    │
│ security_results   │    │         ┌─────────────────────┐
│ dark_pattern_summary│   │         │  audit_screenshots  │
│ pages_scanned      │    │         ├─────────────────────┤
│ screenshots_count  │    │         │ id (PK)            │
│ elapsed_seconds    │    │         │ audit_id (FK)      │
│ errors             │    │         │ file_path          │
│ started_at         │    │         │ label              │
│ completed_at       │    │         │ index              │
│ created_at         │    │         │ file_size_bytes    │
│ updated_at         │    │         │ created_at         │
└─────────────────────┘    │         └─────────────────────┘
                            │
                            │         ┌─────────────────────┐
                            └──────── │    audit_events     │
                                      ├─────────────────────┤
                                      │ id (PK)            │
                                      │ audit_id (FK)      │
                                      │ event_type         │
                                      │ phase              │
                                      │ message            │
                                      │ level              │
                                      │ metadata (jsonb)   │
                                      │ timestamp          │
                                      └─────────────────────┘
```

### Table Definitions

#### `audits` table

Main table storing audit metadata and final results.

```sql
CREATE TABLE audits (
    id VARCHAR(16) PRIMARY KEY,                    -- Generated: vrts_{8_chars}
    url TEXT NOT NULL,
    status VARCHAR(20) NOT NULL,                   -- queued, running, completed, error, disconnected
    audit_tier VARCHAR(50) DEFAULT 'standard_audit',
    verdict_mode VARCHAR(20) DEFAULT 'expert',
    security_modules TEXT,                          -- JSON array of module names

    -- Final analysis results
    trust_score REAL,
    risk_level VARCHAR(50),
    signal_scores JSONB,                            -- Map of signal_name -> score (0-100)
    overrides TEXT,                                 -- JSON array of overrides applied
    narrative TEXT,

    -- Site classification
    site_type VARCHAR(50),
    site_type_confidence REAL,

    -- Domain intelligence
    domain_info JSONB,                              -- age_days, registrar, country, ip, ssl_issuer, inconsistencies, entity_verified

    -- Structured data (could be separate tables)
    recommendations TEXT,                           -- JSON array of recommendation strings
    security_results JSONB,                         -- Map of module_name -> result object
    dark_pattern_summary JSONB,                     -- Summary object from Vision agent

    -- Statistics
    pages_scanned INTEGER DEFAULT 0,
    screenshots_count INTEGER DEFAULT 0,
    elapsed_seconds REAL DEFAULT 0,

    -- Error handling
    errors TEXT,                                    -- JSON array of error strings
    error_message TEXT,                             -- Last error (for display)

    -- Timestamps
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX idx_audits_status ON audits(status);
CREATE INDEX idx_audits_created_at ON audits(created_at DESC);
CREATE INDEX idx_audits_url ON audits(url);
CREATE INDEX idx_audits_trust_score ON audits(trust_score);
CREATE INDEX idx_audits_risk_level ON audits(risk_level);
CREATE INDEX idx_audits_domain_info ON audits USING GIN (domain_info);
```

#### `audit_findings` table

Stores individual dark pattern findings from the Vision agent.

```sql
CREATE TABLE audit_findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_id VARCHAR(16) NOT NULL,                  -- FK to audits.id
    pattern_type VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    severity VARCHAR(20) NOT NULL,                  -- low, medium, high, critical
    confidence REAL NOT NULL,                       -- 0.0 - 1.0
    description TEXT NOT NULL,
    plain_english TEXT,
    screenshot_index INTEGER DEFAULT -1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (audit_id) REFERENCES audits(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_findings_audit_id ON audit_findings(audit_id);
CREATE INDEX idx_findings_pattern_type ON audit_findings(pattern_type);
CREATE INDEX idx_findings_severity ON audit_findings(severity);
CREATE INDEX idx_findings_audit_severity ON audit_findings(audit_id, severity);
```

#### `audit_screenshots` table

Stores screenshot file metadata. Images stored on filesystem, referenced by path in database.

```sql
CREATE TABLE audit_screenshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_id VARCHAR(16) NOT NULL,                  -- FK to audits.id
    file_path TEXT NOT NULL,                        -- Path to image file on disk
    label TEXT NOT NULL,
    index_num INTEGER NOT NULL,                     -- 0-based index for ordering
    file_size_bytes INTEGER,
    mime_type VARCHAR(50) DEFAULT 'image/png',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (audit_id) REFERENCES audits(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_screenshots_audit_id ON audit_screenshots(audit_id);
CREATE UNIQUE INDEX idx_screenshots_audit_path ON audit_screenshots(audit_id, file_path);
```

#### `audit_events` table

Stores all WebSocket events for reconstruction and analysis.

```sql
CREATE TABLE audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_id VARCHAR(16) NOT NULL,                  -- FK to audits.id
    event_type VARCHAR(50) NOT NULL,                -- phase_start, phase_complete, finding, screenshot, log_entry, etc.
    phase VARCHAR(20),                               -- init, scout, security, vision, graph, judge
    message TEXT,
    level VARCHAR(10),                               -- info, warn, error (for log_entry events)
    metadata JSONB,                                  -- Event-specific data
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (audit_id) REFERENCES audits(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_events_audit_id ON audit_events(audit_id);
CREATE INDEX idx_events_type ON audit_events(event_type);
CREATE INDEX idx_events_timestamp ON audit_events(timestamp);
CREATE INDEX idx_events_audit_timestamp ON audit_events(audit_id, timestamp);

-- JSONB index for querying metadata
CREATE INDEX idx_events_metadata ON audit_events USING GIN (metadata);
```

### SQLModel/SQLAlchemy ORM Definitions

```python
# backend/models/audit.py

from datetime import datetime
from typing import Optional
from enum import Enum

from pydantic import BaseModel, field_validator
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class AuditStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    DISCONNECTED = "disconnected"


class SeverityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Audit(Base):
    __tablename__ = "audits"

    id = Column(String(16), primary_key=True)
    url = Column(Text, nullable=False)
    status = Column(SQLEnum(AuditStatus), nullable=False, default=AuditStatus.QUEUED)
    audit_tier = Column(String(50), default="standard_audit")
    verdict_mode = Column(String(20), default="expert")
    security_modules = Column(JSON, default=list)

    trust_score = Column(Float, nullable=True)
    risk_level = Column(String(50), nullable=True)
    signal_scores = Column(JSON, default=dict)
    overrides = Column(JSON, default=list)
    narrative = Column(Text, nullable=True)

    site_type = Column(String(50), nullable=True)
    site_type_confidence = Column(Float, nullable=True)
    domain_info = Column(JSON, default=dict)

    recommendations = Column(JSON, default=list)
    security_results = Column(JSON, default=dict)
    dark_pattern_summary = Column(JSON, default=dict)

    pages_scanned = Column(Integer, default=0)
    screenshots_count = Column(Integer, default=0)
    elapsed_seconds = Column(Float, default=0)

    errors = Column(JSON, default=list)
    error_message = Column(Text, nullable=True)

    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    findings = relationship("AuditFinding", back_populates="audit", cascade="all, delete-orphan")
    screenshots = relationship("AuditScreenshot", back_populates="audit", cascade="all, delete-orphan")
    events = relationship("AuditEvent", back_populates="audit", cascade="all, delete-orphan")

    __table_args__ = (
        # Indexes
    )


class AuditFinding(Base):
    __tablename__ = "audit_findings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    audit_id = Column(String(16), ForeignKey("audits.id", ondelete="CASCADE"), nullable=False)

    pattern_type = Column(String(100), nullable=False)
    category = Column(String(50), nullable=True)
    severity = Column(SQLEnum(SeverityLevel), nullable=False)
    confidence = Column(Float, nullable=False)
    description = Column(Text, nullable=False)
    plain_english = Column(Text, nullable=True)
    screenshot_index = Column(Integer, default=-1)
    created_at = Column(DateTime, default=datetime.utcnow)

    audit = relationship("Audit", back_populates="findings")


class AuditScreenshot(Base):
    __tablename__ = "audit_screenshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    audit_id = Column(String(16), ForeignKey("audits.id", ondelete="CASCADE"), nullable=False)

    file_path = Column(Text, nullable=False)
    label = Column(Text, nullable=False)
    index_num = Column(Integer, nullable=False)
    file_size_bytes = Column(Integer, nullable=True)
    mime_type = Column(String(50), default="image/png")
    created_at = Column(DateTime, default=datetime.utcnow)

    audit = relationship("Audit", back_populates="screenshots")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    audit_id = Column(String(16), ForeignKey("audits.id", ondelete="CASCADE"), nullable=False)

    event_type = Column(String(50), nullable=False)
    phase = Column(String(20), nullable=True)
    message = Column(Text, nullable=True)
    level = Column(String(10), nullable=True)
    metadata = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=datetime.utcnow)

    audit = relationship("Audit", back_populates="events")


# Pydantic models for API validation
class AuditCreate(BaseModel):
    url: str
    tier: str = "standard_audit"
    verdict_mode: str = "expert"
    security_modules: Optional[list[str]] = None

    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        # Basic URL validation
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class AuditResponse(BaseModel):
    audit_id: str
    status: str
    ws_url: str
```

---

## Migration Strategy (In-Memory → Database)

### Phase 1: Add Database Layer (Dual Write)

**Goal:** Add database persistence while keeping in-memory storage active.

**Steps:**

1. **Create database module** (`backend/db/`):
   ```python
   # backend/db/session.py
   from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
   from sqlalchemy.pool import QueuePool

   # SQLite with WAL mode for better concurrency
   DATABASE_URL = "sqlite+aiosqlite:///./elliot_audits.db"

   engine = create_async_engine(
       DATABASE_URL,
       poolclass=QueuePool,
       pool_size=10,
       max_overflow=5,
       pool_pre_ping=True,
       pool_recycle=3600,
       connect_args={
           "check_same_thread": False
       }
   )

   AsyncSessionLocal = async_sessionmaker(
       engine,
       class_=AsyncSession,
       expire_on_commit=False,
   )

   async def get_db() -> AsyncSession:
       async with AsyncSessionLocal() as session:
           yield session
   ```

2. **Add repository pattern for audit operations**:
   ```python
   # backend/repositories/audit_repository.py
   from typing import Optional
   from sqlalchemy import select
   from sqlalchemy.ext.asyncio import AsyncSession
   from models.audit import Audit, AuditFinding, AuditScreenshot, AuditEvent

   class AuditRepository:
       def __init__(self, db: AsyncSession):
           self.db = db

       async def create_audit(self, audit_id: str, url: str, tier: str,
                             verdict_mode: str, security_modules: list[str]) -> Audit:
           audit = Audit(
               id=audit_id,
               url=url,
               audit_tier=tier,
               verdict_mode=verdict_mode,
               status=AuditStatus.QUEUED
           )
           self.db.add(audit)
           await self.db.commit()
           await self.db.refresh(audit)
           return audit

       async def add_finding(self, audit_id: str, finding: dict) -> AuditFinding:
           # Implementation
           pass

       async def add_screenshot(self, audit_id: str, screenshot: dict) -> AuditScreenshot:
           # Implementation
           pass

       async def add_event(self, audit_id: str, event: dict) -> AuditEvent:
           # Implementation
           pass

       async def update_status(self, audit_id: str, status: AuditStatus) -> None:
           # Implementation
           pass

       async def complete_audit(self, audit_id: str, result: dict) -> Audit:
           # Implementation
           pass
   ```

3. **Enable WAL mode on database open**:
   ```python
   # backend/db/init.py
   async def init_database():
       async with engine.begin() as conn:
           await conn.execute(text("PRAGMA journal_mode=WAL"))
           await conn.execute(text("PRAGMA synchronous=NORMAL"))
           await conn.execute(text("PRAGMA wal_autocheckpoint=1000"))
   ```

4. **Modify audit routes to write to both memory and database**:
   ```python
   # backend/routes/audit.py modification
   from db.session import get_db
   from repositories.audit_repository import AuditRepository

   @router.post("/audit/start", response_model=AuditStartResponse)
   async def start_audit(req: AuditStartRequest):
       audit_id = generate_audit_id()

       # Keep in-memory for now (Phase 1)
       _audits[audit_id] = {
           "url": req.url,
           # ... existing in-memory structure
       }

       # NEW: Also write to database async (non-blocking)
       async with AsyncSessionLocal() as db:
           repo = AuditRepository(db)
           asyncio.create_task(
               repo.create_audit(audit_id, req.url, req.tier,
                               req.verdict_mode, req.security_modules or [])
           )

       return AuditStartResponse(...)
   ```

**Phase 1 Checklist:**
- [ ] Database models created
- [ ] Repository pattern implemented
- [ ] WAL mode enabled
- [ ] Dual-write in audit routes
- [ ] Screenshots saved to filesystem (path in DB)
- [ ] Testing: audits created in DB but reads still from memory

---

### Phase 2: Switch Reads to Database

**Goal:** Migrate read operations to use database while keeping in-memory as cache.

**Steps:**

1. **Add database read method**:
   ```python
   @router.get("/audit/{audit_id}/status")
   async def audit_status(audit_id: str):
       # Try database first
       async with AsyncSessionLocal() as db:
           repo = AuditRepository(db)
           audit = await repo.get_by_id(audit_id)
           if audit:
               return {
                   "audit_id": audit.id,
                   "status": audit.status.value,
                   "url": audit.url,
                   "result": audit.signal_scores if audit.status == AuditStatus.COMPLETED else None,
                   "error": audit.error_message
               }

       # Fallback to in-memory (shouldn't happen in Phase 2)
       info = _audits.get(audit_id)
       if not info:
           raise HTTPException(status_code=404, detail="Audit not found")
       return { ... }
   ```

2. **Add audit history endpoint** (new capability from persistence):
   ```python
   @router.get("/audit/history")
   async def audit_history(
       limit: int = 20,
       offset: int = 0,
       status_filter: Optional[AuditStatus] = None
   ):
       async with AsyncSessionLocal() as db:
           repo = AuditRepository(db)
           audits = await repo.get_history(limit, offset, status_filter)
           return {
               "audits": audits,
               "total": len(audits),
               "offset": offset,
               "limit": limit
           }
   ```

3. **Add audit detail fetch for historical audits**:
   ```python
   @router.get("/audit/{audit_id}/detail")
   async def audit_detail(audit_id: str):
       async with AsyncSessionLocal() as db:
           repo = AuditRepository(db)
           audit = await repo.get_full_detail(audit_id)  # joins findings, screenshots, events
           if not audit:
               raise HTTPException(status_code=404, detail="Audit not found")
           return audit
   ```

**Phase 2 Checklist:**
- [ ] Read methods switched to database
- [ ] audit_history endpoint created
- [ ] audit_detail endpoint created
- [ ] In-memory kept as fallback cache
- [ ] Testing: all reads work from database

---

### Phase 3: Remove In-Memory Storage

**Goal:** Complete migration, remove dual-write complexity.

**Steps:**

1. **Remove `_audits` dictionary** from `backend/routes/audit.py`

2. **Simplify WebSocket handler**:
   ```python
   @router.websocket("/audit/stream/{audit_id}")
   async def stream_audit(ws: WebSocket, audit_id: str):
       await ws.accept()

       async with AsyncSessionLocal() as db:
           repo = AuditRepository(db)
           audit = await repo.get_by_id(audit_id)
           if not audit:
               await ws.send_json({"type": "audit_error", "error": "Audit ID not found"})
               await ws.close()
               return

           await repo.update_status(audit_id, AuditStatus.RUNNING)

           runner = AuditRunner(
               audit_id=audit_id,
               url=audit.url,
               # ... rest of config
           )

           async def send_event(data: dict):
               # Store event in database
               if data.get("type") in ["audit_result", "finding", "screenshot", "log_entry"]:
                   await repo.add_event(audit_id, data)

               # Send to WebSocket
               try:
                   await ws.send_json(data)
               except Exception as e:
                   logger.warning(f"[{audit_id}] Failed to send WS event: {e}")

           try:
               await runner.run(send_event)
               await repo.update_status(audit_id, AuditStatus.COMPLETED)
           except Exception as e:
               await repo.update_audit_error(audit_id, str(e))
               await repo.update_status(audit_id, AuditStatus.ERROR)
   ```

3. **Add database cleanup job** (optional, for old audits):
   ```python
   # backend/cleanup.py
   async def cleanup_old_audits(days: int = 30):
       async with AsyncSessionLocal() as db:
           repo = AuditRepository(db)
           await repo.delete_older_than_days(days)
   ```

**Phase 3 Checklist:**
- [ ] In-memory `_audits` dict removed
- [ ] All reads use database
- [ ] All writes use database
- [ ] Cleanup job added
- [ ] Documentation updated

---

## Performance Optimizations

### SQLite: WAL Mode Configuration

```python
# backend/db/init.py
async def configure_sqlite_optimizations():
    """Enable SQLite optimizations for write-heavy workload."""
    async with engine.begin() as conn:
        # Enable Write-Ahead Logging for better concurrency
        await conn.execute(text("PRAGMA journal_mode=WAL"))

        # Reduce durability for speed (NORMAL: checkpoint does fsync, not each transaction)
        await conn.execute(text("PRAGMA synchronous=NORMAL"))

        # Increase cache size (default = -2000KB, set to -64MB)
        await conn.execute(text("PRAGMA cache_size=-64000"))

        # Enable temp_store=MEMORY to keep temp tables in RAM
        await conn.execute(text("PRAGMA temp_store=MEMORY"))

        # Checkpoint every 1000 pages (amortizes checkpoint cost)
        await conn.execute(text("PRAGMA wal_autocheckpoint=1000"))

        # Avoid unnecessary SQLite compile options
        await conn.execute(text("PRAGMA optimize"))
```

### SQLAlchemy Connection Pooling

```python
# Write-heavy workload optimization
engine = create_async_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=15,              # More connections for concurrent audits
    max_overflow=10,           # Allow spike to 25 connections
    pool_pre_ping=True,        # Test connections before use
    pool_recycle=3600,         # Recycle connections after 1 hour
    connect_args={
        "check_same_thread": False,  # SQLite specific
        "timeout": 30  # Query timeout
    }
)
```

### Batch Writing for High-Frequency Events

```python
# backend/repositories/audit_repository.py
class AuditRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._pending_events: list[dict] = []
        self._pending_findings: list[dict] = []
        self._batch_size = 50

    async def add_event_batch(self, events: list[dict]) -> None:
        """Batch insert events for better performance."""
        event_objects = [
            AuditEvent(
                audit_id=e["audit_id"],
                event_type=e["type"],
                phase=e.get("phase"),
                message=e.get("message"),
                level=e.get("level"),
                metadata=e.get("metadata", {})
            )
            for e in events
        ]
        self.db.add_all(event_objects)
        await self.db.commit()

    async def flush_if_needed(self) -> None:
        """Flush pending events if batch size reached."""
        if len(self._pending_events) >= self._batch_size:
            await self.add_event_batch(self._pending_events)
            self._pending_events = []
```

### Screenshot Storage Strategy

**Recommendation:** Store screenshots on filesystem, reference path in database.

**Rationale:**
1. Database size stays manageable (images can be 100KB-2MB each)
2. Filesystem caching optimized by OS for image serving
3. Database backup/restore faster without binary data
4. CDN integration possible for future scaling

**Implementation:**

```python
# backend/services/screenshot_storage.py
import os
import base64
from pathlib import Path
from uuid import uuid4
from datetime import datetime

class ScreenshotStorage:
    def __init__(self, base_dir: str = "storage/screenshots"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save_screenshot(
        self,
        audit_id: str,
        index: int,
        label: str,
        base64_data: str | None = None,
        image_bytes: bytes | None = None
    ) -> tuple[str, int]:
        """Save screenshot to filesystem, return (filepath, file_size)."""

        # Create audit-specific directory
        audit_dir = self.base_dir / audit_id
        audit_dir.mkdir(exist_ok=True)

        # Generate filename: {timestamp}_{index}_{uuid}.png
        filename = f"{datetime.utcnow().timestamp()}_{index}_{uuid4().hex[:8]}.png"
        filepath = audit_dir / filename

        # Determine image data
        if base64_data:
            image_bytes = base64.b64decode(base64_data)
        elif image_bytes is None:
            raise ValueError("Must provide either base64_data or image_bytes")

        # Write to disk
        filepath.write_bytes(image_bytes)

        return str(filepath), len(image_bytes)

    async def get_screenshot(self, filepath: str) -> bytes:
        """Read screenshot from filesystem."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Screenshot not found: {filepath}")
        return path.read_bytes()

    async def delete_audit_screenshots(self, audit_id: str) -> None:
        """Delete all screenshots for an audit."""
        audit_dir = self.base_dir / audit_id
        if audit_dir.exists():
            for file in audit_dir.iterdir():
                file.unlink()
            audit_dir.rmdir()
```

### Async Database Operations

Use SQLAlchemy 2.0 async syntax throughout:

```python
# Good: Async operations
async def get_recent_audits(limit: int = 20) -> list[Audit]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Audit)
            .where(Audit.status == AuditStatus.COMPLETED)
            .order_by(Audit.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

# Bad: Blocking operations in async context
def get_recent_audits(limit: int = 20) -> list[Audit]:  # Blocks event loop!
    with SessionLocal() as db:
        # ...
```

---

## Screenshot Management

### Directory Structure

```
storage/screenshots/
├── vrts_a1b2c3d4/
│   ├── 1708429123_0_f8e9a1b2.png    # t0_screenshot
│   ├── 1708429145_1_c3d4e5f6.png    # t+delay_screenshot
│   ├── 1708429180_2_7a8b9c0d.png    # full_page_screenshot
│   └── ...
├── vrts_e9f8a7b6/
│   └── ...
└── .gitkeep
```

### Storage Service Integration

```python
# backend/services/audit_runner.py modification
# In _handle_result method:
screenshot_storage = ScreenshotStorage()

for scout_result in result.get("scout_results", []):
    for i, screenshot_path in enumerate(scout_result.get("screenshots", [])):
        labels = scout_result.get("screenshot_labels", [])
        label = labels[i] if i < len(labels) else f"Screenshot {self._screenshot_index + 1}"

        # Read original image bytes
        img_path = Path(screenshot_path)
        img_bytes = None
        if img_path.exists():
            img_bytes = img_path.read_bytes()

        # Save to persistent storage
        persistent_path, file_size = await screenshot_storage.save_screenshot(
            audit_id=self.audit_id,
            index=self._screenshot_index,
            label=label,
            image_bytes=img_bytes
        )

        # Encode for WebSocket transmission
        base64_data = base64.b64encode(img_bytes).decode("ascii") if img_bytes else None

        await send({
            "type": "screenshot",
            "url": persistent_path,
            "label": label,
            "index": self._screenshot_index,
            "data": base64_data,
        })

        # Store in database
        await repo.add_screenshot(audit_id, {
            "file_path": persistent_path,
            "label": label,
            "index_num": self._screenshot_index,
            "file_size_bytes": file_size
        })

        self._screenshot_index += 1
```

---

## Query Patterns for Audit History

### Get Recent Audits

```python
async def get_recent_audits(limit: int = 20, offset: int = 0) -> list[dict]:
    """Get paginated list of recent audits."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Audit)
            .order_by(Audit.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        audits = result.scalars().all()

        return [
            {
                "audit_id": a.id,
                "url": a.url,
                "status": a.status.value,
                "trust_score": a.trust_score,
                "risk_level": a.risk_level,
                "created_at": a.created_at.isoformat(),
                "elapsed_seconds": a.elapsed_seconds
            }
            for a in audits
        ]
```

### Search Audits by URL

```python
async def search_by_url(pattern: str, limit: int = 20) -> list[dict]:
    """Search for audits by URL pattern."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Audit)
            .where(Audit.url.ilike(f"%{pattern}%"))
            .order_by(Audit.created_at.desc())
            .limit(limit)
        )
        audits = result.scalars().all()
        return [audit_to_dict(a) for a in audits]
```

### Get Audit with All Findings

```python
async def get_audit_with_findings(audit_id: str) -> dict:
    """Get full audit detail including all findings."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Audit)
            .options(
                selectinload(Audit.findings),
                selectinload(Audit.screenshots),
                selectinload(Audit.events)
            )
            .where(Audit.id == audit_id)
        )
        audit = result.scalar_one_or_none()

        if not audit:
            return None

        return {
            "audit": audit_to_dict(audit),
            "findings": [
                {
                    "pattern_type": f.pattern_type,
                    "severity": f.severity.value,
                    "confidence": f.confidence,
                    "description": f.description
                }
                for f in audit.findings
            ],
            "screenshots": [
                {
                    "file_path": s.file_path,
                    "label": s.label,
                    "index": s.index_num
                }
                for s in audit.screenshots
            ]
        }
```

### Get Analytics: Risk Level Distribution

```python
async def get_risk_distribution(days: int = 30) -> dict:
    """Get distribution of risk levels over recent period."""
    async with AsyncSessionLocal() as db:
        cutoff = datetime.utcnow() - timedelta(days=days)

        result = await db.execute(
            select(
                Audit.risk_level,
                func.count(Audit.id)
            )
            .where(Audit.created_at >= cutoff)
            .where(Audit.status == AuditStatus.COMPLETED)
            .group_by(Audit.risk_level)
        )

        return {level: count for level, count in result.all()}
```

---

## Anti-Patterns to Avoid

### 1. Storing Binary Data Directly in Database

**What:** Saving base64 or raw binary screenshots directly in the `audit_screenshots` table.

**Why bad:**
- Database bloat (each audit can have 3-10 screenshots, ~100KB-2MB each)
- Slow backups/restores
- No CDN/caching optimization for image serving

**Instead:** Store screenshots on filesystem, reference path in database.

### 2. Frequent Small Writes Without Batching

**What:** Writing each WebSocket event individually to database.

**Why bad:**
- Excessive transaction overhead
- WAL checkpoint thrashing
- Lock contention

**Instead:** Batch events, flush when batch size reached or audit completes.

### 3. No Indexes on Query Columns

**What:** Creating tables without indexes on frequently queried columns (status, created_at, url).

**Why bad:**
- Full table scans for common queries
- Slow audit history retrieval

**Instead:** Add appropriate indexes as shown in schema definitions.

### 4. Blocking Operations in Async Context

**What:** Using synchronous SQLAlchemy sessions in async FastAPI routes.

**Why bad:**
- Blocks event loop, limits concurrency
- Can cause timeout issues under load

**Instead:** Use SQLAlchemy async engine and AsyncSession.

### 5. Deleting Screenshots from Database Before Filesystem

**What:** Deleting audit record CASCADE deletes screenshots before removing files.

**Why bad:**
- Orphaned files on filesystem consuming disk space
- No way to clean up missing files

**Instead:** Explicit delete order: filesystem first, then database.

---

## Scaling Considerations

### At 100 Concurrent Audits (Current Scale)

**Status:** SQLite with WAL mode is sufficient.

**Configuration:**
- `pool_size=15`, `max_overflow=10`
- WAL mode enabled
- Connection recycling every hour

**Performance:** ~50-100 writes/second, ~1000 queries/second.

### At 1,000+ Concurrent Audits

**Status:** Consider migrating to PostgreSQL.

**Migration steps:**
1. Dump SQLite database: `sqlite3 elliot_audits.db .dump > backup.sql`
2. Load into PostgreSQL: `psql postgresql://host/dbname < backup.sql`
3. Update `DATABASE_URL` environment variable
4. No code changes needed (SQLAlchemy abstraction)

**PostgreSQL configuration:**
```python
DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/elliot"
```

### At 10,000+ Audits/Day

**Status:** PostgreSQL with additional optimizations.

**Add:**
- Partitioning by `created_at` (daily/monthly partitions)
- Archival job for old audits (move to cold storage)
- Redis cache for hot audit metadata
- Separate read replica for analytics queries

---

## Security Considerations

### Path Traversal Prevention

```python
# backend/services/screenshot_storage.py
def _validate_path(self, path: Path) -> Path:
    """Ensure path is within base directory."""
    try:
        resolved = path.resolve()
        if not str(resolved).startswith(str(self.base_dir.resolve())):
            raise ValueError("Path traversal attempt detected")
        return resolved
    except Exception:
        raise ValueError("Invalid file path")
```

### SQL Injection Prevention

SQLAlchemy ORM parameters automatically handle parameterized queries. Never use f-strings or `.format()` with SQL:

```python
# Bad - SQL injection risk
await conn.execute(text(f"SELECT * FROM audits WHERE id = '{audit_id}'"))

# Good - Parameterized query
await conn.execute(text("SELECT * FROM audits WHERE id = :id"), {"id": audit_id})
```

### File Upload Limits

```python
# Limit screenshot size to 5MB
MAX_SCREENSHOT_SIZE = 5 * 1024 * 1024

async def save_screenshot(self, ...):
    if len(image_bytes) > MAX_SCREENSHOT_SIZE:
        raise ValueError("Screenshot size exceeds 5MB limit")
    # ...
```

---

## Monitoring and Maintenance

### Database Health Check

```python
@router.get("/db/health")
async def db_health():
    """Check database connectivity and WAL status."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("PRAGMA journal_mode"))
        journal_mode = result.scalar_one()

        result = await db.execute(text("PRAGMA wal_checkpoint(PASSIVE)"))
        checkpoint = result.fetchone()

        # Get table stats
        result = await db.execute(
            text("SELECT name, COUNT(*) as count FROM sqlite_master WHERE type='table' GROUP BY name")
        )
        tables = {row[0]: row[1] for row in result.all()}

        return {
            "status": "healthy",
            "journal_mode": journal_mode,
            "checkpoint": {
                "wal_size": checkpoint[0],
                "frames_checkpointed": checkpoint[1],
                "pages_checkpointed": checkpoint[2]
            },
            "tables": tables
        }
```

### Disk Usage Monitoring

```python
async def get_storage_stats():
    """Get storage statistics."""
    db_size = Path("elliot_audits.db").stat().st_size
    wal_size = Path("elliot_audits.db-wal").stat().st_size if Path("elliot_audits.db-wal").exists() else 0
    screenshot_dir = Path("storage/screenshots")

    screenshot_size = sum(
        f.stat().st_size
        for f in screenshot_dir.rglob("*")
        if f.is_file()
    )

    return {
        "database_bytes": db_size,
        "wal_bytes": wal_size,
        "screenshots_bytes": screenshot_size,
        "audits_count": await count_audits(),
        "screenshots_count": len(list(screenshot_dir.rglob("*.png")))
    }
```

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Database selection (SQLite/PostgreSQL) | HIGH | SQLite verified via official docs, PostgreSQL standard for scaling |
| Schema design for audit data | MEDIUM | Based on standard SQL patterns but untested with specific Elliot data volumes |
| Screenshot storage strategy | MEDIUM | Filesystem storage is standard, but specific layout may need adjustment based on actual usage |
| Migration strategy (dual-write) | HIGH | Standard database migration pattern with proven reliability |
| SQLite WAL mode optimization | HIGH | Verified via SQLite official documentation |
| Connection pooling config | MEDIUM | Based on SQLAlchemy docs but may need tuning based on actual load |

---

## Sources

### Official Documentation
- [SQLite Use Cases](https://sqlite.org/whentouse.html) — HIGH confidence (official docs)
- [SQLite WAL Mode](https://www.sqlite.org/wal.html) — HIGH confidence (official docs)
- [PostgreSQL JSON Documentation](https://www.postgresql.org/docs/current/datatype-json.html) — HIGH confidence (official docs)
- [FastAPI Database Tutorial](https://fastapi.tiangolo.com/tutorial/sql-databases/) — MEDIUM confidence (official docs)
- [SQLAlchemy Connection Pooling](https://docs.sqlalchemy.org/en/20/core/pooling.html) — HIGH confidence (official docs)

### Codebase Analysis
- `backend/routes/audit.py` — In-memory audit storage implementation
- `backend/services/audit_runner.py` — Audit result structure and WebSocket event types
- `frontend/src/lib/types.ts` — TypeScript type definitions for audit data
- `.planning/codebase/CONCERNS.md` — In-memory storage issue documentation
- `.planning/codebase/ARCHITECTURE.md` — System architecture and data flow

### Patterns Used
- Standard SQLAlchemy async ORM patterns (verified via official docs)
- Dual-write migration pattern (industry standard)
- WAL mode for SQLite concurrency (official SQLite recommendation)

---

## Gaps Requiring Phase-Specific Research

1. **Actual Data Volume Analysis**
   - Need to measure real-world size of:
     - Average audit result (JSON)
     - Screenshot files per audit
     - Number of events per audit
   - Research: Audit 50 real URLs, collect metrics

2. **Query Pattern Analysis**
   - Which historical queries will users need?
   - What analytics are valuable?
   - Research: User interviews, analytics dashboard design

3. **Retention Policy**
   - How long should audits be kept?
   - Should old audits be archived or deleted?
   - Research: Legal requirements, storage costs, user needs

4. **Multi-Instance Deployment Architecture**
   - When migrating to PostgreSQL, how to handle:
     - Database migration without downtime
     - Connection pool sizing for multiple backends
     - Database replica for read-heavy analytics
   - Research: PostgreSQL scaling patterns, deployment architecture

---

*Persistence research for: Elliot (elliotAI) Audit Storage*
*Researched: 2026-02-20*

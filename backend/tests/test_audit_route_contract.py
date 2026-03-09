from datetime import datetime
from unittest.mock import patch

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from backend.routes.audit import audit_status, on_audit_completed, on_audit_started
from veritas.db.config import Base
from veritas.db.models import AuditStatus
from veritas.db.repositories import AuditRepository


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_on_audit_completed_persists_canonical_summary(db_session: AsyncSession):
    audit_id = "vrts_testabcd"
    with patch("backend.routes.audit.should_use_db_persistence", return_value=True):
        await on_audit_started(
            audit_id,
            {
                "url": "https://example.com",
                "tier": "standard_audit",
                "verdict_mode": "expert",
            },
            db_session,
        )
        await on_audit_completed(
            audit_id,
            {
                "trust_score": 67,
                "risk_level": "medium",
                "narrative": "Caution warranted.",
                "signal_scores": {"security": 55.0},
                "site_type": "login",
                "site_type_confidence": 0.82,
                "security_results": {"phishing_db": {"verdict": "suspicious"}},
                "pages_scanned": 3,
                "elapsed_seconds": 9.5,
                "dark_pattern_summary": {
                    "findings": [
                        {
                            "pattern_type": "fake_urgency",
                            "category": "visual_interference",
                            "severity": "high",
                            "confidence": 0.92,
                            "description": "Timer resets.",
                            "plain_english": "The urgency signal appears fake.",
                            "screenshot_index": 0,
                        }
                    ]
                },
            },
            db_session,
        )

    repo = AuditRepository(db_session)
    audit = await repo.get_by_id(audit_id)

    assert audit is not None
    assert audit.status == AuditStatus.COMPLETED
    assert audit.trust_score == 67
    assert audit.risk_level == "medium"
    assert audit.site_type == "login"
    assert audit.pages_scanned == 3
    assert audit.completed_at is not None
    assert len(audit.findings) == 1
    assert audit.findings[0].pattern_type == "fake_urgency"


@pytest.mark.asyncio
async def test_audit_status_returns_stable_completed_payload(db_session: AsyncSession):
    audit_id = "vrts_testefgh"
    with patch("backend.routes.audit.should_use_db_persistence", return_value=True):
        await on_audit_started(
            audit_id,
            {
                "url": "https://example.com",
                "tier": "quick_scan",
                "verdict_mode": "simple",
            },
            db_session,
        )
        await on_audit_completed(
            audit_id,
            {
                "trust_score": 85,
                "risk_level": "low",
                "narrative": "Mostly trustworthy.",
                "signal_scores": {"visual": 90.0},
                "site_type": "content",
                "site_type_confidence": 0.76,
                "security_results": {"security_headers": {"score": 0.9}},
                "pages_scanned": 1,
                "elapsed_seconds": 4.2,
                "dark_pattern_summary": {"findings": []},
                "completed_at": datetime.utcnow(),
            },
            db_session,
        )
        status = await audit_status(audit_id, db_session)

    assert status["audit_id"] == audit_id
    assert status["status"] == "completed"
    assert status["url"] == "https://example.com"
    assert status["result"]["trust_score"] == 85
    assert status["result"]["risk_level"] == "low"
    assert status["result"]["site_type"] == "content"
    assert status["result"]["security_results"]["security_headers"]["score"] == 0.9
    assert status["result"]["dark_pattern_summary"]["findings"] == []

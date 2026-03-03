"""
SQLAlchemy ORM models for VERITIS audit persistence.

Defines Audit, AuditFinding, AuditScreenshot, and AuditEvent models
with proper relationships, indexes, and constraints.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship

from veritas.db.config import Base


class AuditStatus(str, Enum):
    """Audit status enum."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    DISCONNECTED = "disconnected"


class Audit(Base):
    """Main audit table storing metadata and final results.

    Each audit represents one complete web trust analysis with
    associated findings, screenshots, and progress events.
    """
    __tablename__ = "audits"

    # Primary key - matches audit ID format from AuditRunner
    id = Column(String(16), primary_key=True)  # vrts_{8_chars}

    # Input parameters
    url = Column(Text, nullable=False)
    status = Column(SQLEnum(AuditStatus), nullable=False, default=AuditStatus.QUEUED)
    audit_tier = Column(String(50), default="standard_audit")
    verdict_mode = Column(String(20), default="expert")

    # Final results from Judge agent
    trust_score = Column(Float, nullable=True)
    risk_level = Column(String(50), nullable=True)
    signal_scores = Column(JSON, default=dict)
    narrative = Column(Text, nullable=True)

    # Site classification from Scout agent
    site_type = Column(String(50), nullable=True)
    site_type_confidence = Column(Float, nullable=True)

    # Security results from Security agent (JSON blob)
    security_results = Column(JSON, default=dict)

    # Statistics
    pages_scanned = Column(Integer, default=0)
    screenshots_count = Column(Integer, default=0)
    elapsed_seconds = Column(Float, default=0)

    # Error handling
    errors = Column(JSON, default=list)
    error_message = Column(Text, nullable=True)

    # Timestamps
    started_at = Column(DateTime, default=lambda: datetime.utcnow())
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    # Relationships - cascade delete ensures child records are removed when audit is deleted
    findings = relationship(
        "AuditFinding", back_populates="audit", cascade="all, delete-orphan"
    )
    screenshots = relationship(
        "AuditScreenshot", back_populates="audit", cascade="all, delete-orphan"
    )
    events = relationship(
        "AuditEvent", back_populates="audit", cascade="all, delete-orphan"
    )

    # Indexes for frequently queried columns
    __table_args__ = (
        Index("idx_audits_status", "status"),
        Index("idx_audits_created_at", "created_at"),
        Index("idx_audits_trust_score", "trust_score"),
        Index("idx_audits_url", "url"),
    )


class AuditFinding(Base):
    """Individual dark pattern findings from Vision agent.

    Each finding represents a detected dark pattern with metadata
    about its type, severity, and location.
    """
    __tablename__ = "audit_findings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    audit_id = Column(
        String(16),
        ForeignKey("audits.id", ondelete="CASCADE"),
        nullable=False
    )

    # Finding details
    pattern_type = Column(String(100), nullable=False)
    category = Column(String(50), nullable=True)
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    confidence = Column(Float, nullable=False)
    description = Column(Text, nullable=False)
    plain_english = Column(Text, nullable=True)
    screenshot_index = Column(Integer, default=-1)

    # Timestamp
    created_at = Column(DateTime, default=lambda: datetime.utcnow())

    # Relationship to parent audit
    audit = relationship("Audit", back_populates="findings")

    # Indexes for queries by audit and pattern type
    __table_args__ = (
        Index("idx_findings_audit_id", "audit_id"),
        Index("idx_findings_pattern_type", "pattern_type"),
    )


class AuditScreenshot(Base):
    """Screenshot file metadata (images stored on filesystem).

    Screenshot images are stored on disk to avoid database bloat.
    This table only stores file paths and metadata.
    """
    __tablename__ = "audit_screenshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    audit_id = Column(
        String(16),
        ForeignKey("audits.id", ondelete="CASCADE"),
        nullable=False
    )

    # File metadata
    file_path = Column(Text, nullable=False)  # Path on filesystem relative to data/
    label = Column(Text, nullable=False)
    index_num = Column(Integer, nullable=False)
    file_size_bytes = Column(Integer, nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=lambda: datetime.utcnow())

    # Relationship to parent audit
    audit = relationship("Audit", back_populates="screenshots")

    # Index for queries by audit
    __table_args__ = (
        Index("idx_screenshots_audit_id", "audit_id"),
    )


class AuditEvent(Base):
    """Progress events during audit execution.

    Stores all progress events streamed via WebSocket for
    historical tracking and debugging.
    """
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    audit_id = Column(
        String(16),
        ForeignKey("audits.id", ondelete="CASCADE"),
        nullable=False
    )

    # Event details
    event_type = Column(String(100), nullable=False)
    data = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=lambda: datetime.utcnow())

    # Relationship to parent audit
    audit = relationship("Audit", back_populates="events")

    # Index for queries by audit
    __table_args__ = (
        Index("idx_events_audit_id", "audit_id"),
    )


class OSINTCache(Base):
    """Cached OSINT query results with source-specific TTLs.

    Stores OSINT intelligence source results to reduce redundant queries
    and respect API rate limits. Each source type has a configured TTL
    (DNS: 24h, WHOIS: 7d, SSL: 30d, threat intel: 4-24h).
    """
    __tablename__ = "osint_cache"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Cache key (MD5 hash of query parameters)
    query_key = Column(String(255), nullable=False, unique=True)

    # Source metadata
    source = Column(String(50), nullable=False)
    category = Column(String(50), nullable=False)

    # Cached result and metadata
    result = Column(JSON, nullable=False)
    confidence_score = Column(Float, nullable=True)

    # Timestamps for TTL management
    cached_at = Column(DateTime, default=lambda: datetime.utcnow())
    expires_at = Column(DateTime, nullable=False)

    # Indexes for efficient queries
    __table_args__ = (
        Index("idx_osint_query_key", "query_key"),
        Index("idx_osint_source", "source"),
        Index("idx_osint_expires_at", "expires_at"),
        Index("idx_osint_category", "category"),
    )

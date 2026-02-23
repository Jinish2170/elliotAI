"""
Repository layer for audit database operations.

Provides AuditRepository class encapsulating all CRUD operations
for the VERITAS audit persistence layer using AsyncSession.
"""

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from veritas.db.models import Audit, AuditFinding, AuditScreenshot, AuditStatus


class AuditRepository:
    """Repository for audit database operations.

    Encapsulates all CRUD operations for Audit entities and related
    data (findings, screenshots, events) using AsyncSession for
    async database access.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize repository with database session.

        Args:
            db: Async SQLAlchemy session for database operations
        """
        self.db = db

    async def get_by_id(self, audit_id: str) -> Audit | None:
        """Get audit by ID with related data loaded.

        eagerly loads findings and screenshots relationships to
        avoid N+1 query problems.

        Args:
            audit_id: The audit ID to fetch (vrts_{8_chars})

        Returns:
            Audit object if found, None otherwise
        """
        result = await self.db.execute(
            select(Audit)
            .options(
                selectinload(Audit.findings),
                selectinload(Audit.screenshots)
            )
            .where(Audit.id == audit_id)
        )
        return result.scalar_one_or_none()

    async def create(self, audit: Audit) -> Audit:
        """Create new audit record.

        Saves the audit object and all related objects via cascade.
        The audit object is refreshed to get database-generated values.

        Args:
            audit: Audit object with data to save (may include
                  related findings, screenshots, events)

        Returns:
            The saved audit object with database-generated values
        """
        self.db.add(audit)
        await self.db.commit()
        await self.db.refresh(audit)
        return audit

    async def update(self, audit: Audit) -> Audit:
        """Update existing audit record.

        SQLAlchemy tracks changes to the audit object automatically.
        This method commits those changes and refreshes the object.

        Args:
            audit: Audit object with updated data

        Returns:
            The updated audit object
        """
        self.db.add(audit)
        await self.db.commit()
        await self.db.refresh(audit)
        return audit

    async def update_status(
        self,
        audit_id: str,
        status: AuditStatus,
        error_message: str | None = None
    ) -> bool:
        """Update audit status without loading the full object.

        Performs an efficient status update using a direct UPDATE
        without loading the entire audit object.

        Args:
            audit_id: The audit ID to update
            status: New audit status
            error_message: Optional error message if status is ERROR

        Returns:
            True if audit was found and updated, False otherwise
        """
        result = await self.db.execute(
            select(Audit).where(Audit.id == audit_id)
        )
        audit = result.scalar_one_or_none()

        if audit is None:
            return False

        audit.status = status
        if error_message is not None:
            audit.error_message = error_message

        await self.db.commit()
        return True

    async def list_recent(
        self,
        limit: int = 20,
        offset: int = 0,
        status_filter: AuditStatus | None = None
    ) -> list[Audit]:
        """Get recent audits with pagination and optional filtering.

        Returns audits in descending order by creation time (newest first).
        Supports optional status filtering.

        Args:
            limit: Maximum number of audits to return (default: 20)
            offset: Number of audits to skip for pagination (default: 0)
            status_filter: Optional status filter (e.g., AuditStatus.COMPLETED)

        Returns:
            List of audit objects ordered by created_at descending
        """
        query = select(Audit).order_by(Audit.created_at.desc())

        if status_filter is not None:
            query = query.where(Audit.status == status_filter)

        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_url(self, url: str, limit: int = 5) -> list[Audit]:
        """Get past audits for a specific URL.

        Useful for comparison to see how trust scores have changed
        over time for the same website.

        Args:
            url: The URL to search for
            limit: Maximum number of past audits to return (default: 5)

        Returns:
            List of audit objects for this URL ordered by date (newest first)
        """
        result = await self.db.execute(
            select(Audit)
            .where(Audit.url == url)
            .order_by(Audit.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

"""Screenshot filesystem storage service.

This module provides a filesystem-based storage service for screenshots,
organizing them by audit_id with path traversal protection.
"""
import base64
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import uuid4


class ScreenshotStorage:
    """Manage screenshot storage on filesystem.

    Screenshots are organized in directories by audit_id:
    data/screenshots/{audit_id}/{timestamp}_{index}_{uuid}.png

    Path traversal protection is implemented via _validate_path().
    """

    def __init__(self, base_dir: Path = Path("data/screenshots")) -> None:
        """Initialize screenshot storage.

        Args:
            base_dir: Base directory for screenshot storage.
                      Will be created if it doesn't exist.

        """
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save(
        self,
        audit_id: str,
        index: int,
        label: str,
        base64_data: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
    ) -> tuple[str, int]:
        """Save a screenshot to filesystem.

        Args:
            audit_id: Audit identifier (no path separators allowed).
            index: Screenshot index within the audit.
            label: Label/description for the screenshot.
            base64_data: Base64-encoded image data (optional).
            image_bytes: Raw image bytes (optional).

        Returns:
            Tuple of (filepath, file_size_bytes).

        Raises:
            ValueError: If audit_id contains path separators or no image data provided.
            ValueError: If path traversal attempt detected.

        """
        # Validate audit_id (no path separators)
        if "/" in audit_id or "\\" in audit_id or ".." in audit_id:
            raise ValueError(
                f"Invalid audit_id '{audit_id}': path separators not allowed"
            )

        # Create audit-specific directory
        audit_dir = self.base_dir / audit_id
        audit_dir.mkdir(exist_ok=True)

        # Generate filename: {timestamp}_{index}_{uuid}.png
        filename = f"{datetime.now().timestamp()}_{index}_{uuid4().hex[:8]}.png"
        filepath = audit_dir / filename

        # Validate filepath is within base_dir
        validated_path = self._validate_path(filepath)

        # Determine image data
        if base64_data:
            image_bytes = base64.b64decode(base64_data)
        elif image_bytes is None:
            raise ValueError(
                "Must provide either base64_data or image_bytes"
            )

        # Write to disk
        validated_path.write_bytes(image_bytes)
        return str(validated_path), len(image_bytes)

    def _validate_path(self, path: Path) -> Path:
        """Validate that path is within base directory (path traversal protection).

        Args:
            path: Path to validate.

        Returns:
            Resolved path if valid.

        Raises:
            ValueError: If path traversal attempt detected.

        """
        resolved = path.resolve()
        base_resolved = self.base_dir.resolve()
        if not str(resolved).startswith(str(base_resolved)):
            raise ValueError("Path traversal attempt detected")
        return resolved

    async def delete(self, audit_id: str) -> None:
        """Delete all screenshots for an audit_id.

        Args:
            audit_id: Audit identifier to delete.

        Raises:
            ValueError: If audit_id contains path separators.

        """
        # Validate audit_id
        if "/" in audit_id or "\\" in audit_id or ".." in audit_id:
            raise ValueError(
                f"Invalid audit_id '{audit_id}': path separators not allowed"
            )

        # Delete all files in audit directory
        audit_dir = self.base_dir / audit_id
        if audit_dir.exists():
            for file in audit_dir.iterdir():
                file.unlink()
            audit_dir.rmdir()
        # Return silently if audit_id doesn't exist

    async def get_all(self, audit_id: str) -> list[dict]:
        """Get all screenshot metadata for an audit.

        Args:
            audit_id: Audit identifier.

        Returns:
            List of dicts with keys: filepath, filename, size_bytes.
            Empty list if audit_id doesn't exist.

        Raises:
            ValueError: If audit_id contains path separators.

        """
        # Validate audit_id
        if "/" in audit_id or "\\" in audit_id or ".." in audit_id:
            raise ValueError(
                f"Invalid audit_id '{audit_id}': path separators not allowed"
            )

        audit_dir = self.base_dir / audit_id
        if not audit_dir.exists():
            return []

        # Build return list with metadata
        results = []
        for f in audit_dir.iterdir():
            if f.is_file():
                results.append({
                    "filepath": str(f),
                    "filename": f.name,
                    "size_bytes": f.stat().st_size,
                })

        # Sort by filename (timestamp-based)
        results.sort(key=lambda x: x["filename"])
        return results

    async def get_file(self, filepath: str) -> bytes:
        """Read a screenshot file by path.

        Args:
            filepath: Path to the screenshot file.

        Returns:
            Raw image bytes.

        Raises:
            ValueError: If path traversal attempt detected.
            FileNotFoundError: If file doesn't exist.

        """
        path = Path(filepath)
        validated_path = self._validate_path(path)
        return validated_path.read_bytes()

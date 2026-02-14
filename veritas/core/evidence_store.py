"""
Veritas Core — Evidence Store (LanceDB)

Disk-based vector store for persistent evidence storage.
Replaces in-memory FAISS — uses SSD instead of RAM.

Features:
    - Store audit results with embeddings for semantic search
    - Retrieve similar past audits ("Have we seen this pattern before?")
    - Cache dark pattern evidence for cross-audit learning
    - Persist all evidence to disk (survives restarts)

Uses sentence-transformers (all-MiniLM-L6-v2) for local embeddings (~90MB RAM).
"""

import json
import logging
import sys
import time
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import settings

logger = logging.getLogger("veritas.evidence_store")


# ============================================================
# Evidence Store
# ============================================================

class EvidenceStore:
    """
    Disk-based evidence store using LanceDB.
    Same interface pattern as the RAGv5 vector_store but backed by SSD.

    Usage:
        store = EvidenceStore()

        # Store an audit result
        store.store_audit(
            url="https://example.com",
            trust_score=45,
            risk_level="suspicious",
            dark_patterns=["fake_countdown", "hidden_unsubscribe"],
            summary="Site uses deceptive timer and hidden cancel button",
        )

        # Search for similar past audits
        results = store.search_similar("fake countdown timer scam site")
    """

    def __init__(self, db_path: Optional[Path] = None):
        self._db_path = db_path or settings.VECTORDB_DIR
        self._db_path.mkdir(parents=True, exist_ok=True)
        self._db = None
        self._embedder = None
        self._initialized = False

    def _ensure_init(self):
        """Lazy-initialize LanceDB connection and embedding model."""
        if self._initialized:
            return

        try:
            import lancedb

            self._db = lancedb.connect(str(self._db_path))
            logger.info(f"LanceDB connected at {self._db_path}")
        except ImportError:
            logger.warning("lancedb not installed — evidence store will use JSON fallback")
            self._db = None

        try:
            from sentence_transformers import SentenceTransformer

            self._embedder = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info(f"Embedding model loaded: {settings.EMBEDDING_MODEL}")
        except ImportError:
            logger.warning("sentence-transformers not installed — embeddings disabled")
            self._embedder = None

        self._initialized = True

    # ================================================================
    # Public: Store
    # ================================================================

    def store_audit(
        self,
        url: str,
        trust_score: int,
        risk_level: str,
        dark_patterns: list[str],
        summary: str,
        metadata: Optional[dict] = None,
    ) -> bool:
        """
        Store an audit result for future retrieval.

        Args:
            url: Audited URL
            trust_score: Final trust score (0-100)
            risk_level: Risk level string
            dark_patterns: List of detected pattern type IDs
            summary: Text summary of findings
            metadata: Additional metadata dict

        Returns:
            True if stored successfully
        """
        self._ensure_init()

        record = {
            "url": url,
            "trust_score": trust_score,
            "risk_level": risk_level,
            "dark_patterns": json.dumps(dark_patterns),
            "summary": summary,
            "metadata": json.dumps(metadata or {}),
            "timestamp": time.time(),
        }

        # Try LanceDB first
        if self._db and self._embedder:
            try:
                embedding = self._embedder.encode(summary).tolist()
                record["vector"] = embedding

                table_name = "audits"
                if table_name in self._db.table_names():
                    table = self._db.open_table(table_name)
                    table.add([record])
                else:
                    self._db.create_table(table_name, [record])

                logger.info(f"Stored audit in LanceDB: {url} (score={trust_score})")
                return True

            except Exception as e:
                logger.warning(f"LanceDB store failed: {e} — falling back to JSON")

        # JSON fallback
        return self._json_store(record)

    def store_evidence(
        self,
        audit_url: str,
        evidence_type: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> bool:
        """Store a piece of evidence (screenshot analysis result, entity verification, etc.)."""
        self._ensure_init()

        record = {
            "audit_url": audit_url,
            "evidence_type": evidence_type,
            "content": content,
            "metadata": json.dumps(metadata or {}),
            "timestamp": time.time(),
        }

        if self._db and self._embedder:
            try:
                embedding = self._embedder.encode(content[:512]).tolist()
                record["vector"] = embedding

                table_name = "evidence"
                if table_name in self._db.table_names():
                    table = self._db.open_table(table_name)
                    table.add([record])
                else:
                    self._db.create_table(table_name, [record])

                return True
            except Exception as e:
                logger.warning(f"LanceDB evidence store failed: {e}")

        return self._json_store(record, filename="evidence.jsonl")

    # ================================================================
    # Public: Search
    # ================================================================

    def search_similar(
        self, query: str, k: int = 5, table_name: str = "audits",
    ) -> list[dict]:
        """
        Search for similar past audits or evidence via semantic search.

        Args:
            query: Search query text
            k: Number of results to return
            table_name: "audits" or "evidence"

        Returns:
            List of matching records with similarity scores
        """
        self._ensure_init()

        if self._db and self._embedder:
            try:
                if table_name not in self._db.table_names():
                    return []

                query_embedding = self._embedder.encode(query).tolist()
                table = self._db.open_table(table_name)
                results = table.search(query_embedding).limit(k).to_list()

                return [
                    {k: v for k, v in r.items() if k != "vector"}
                    for r in results
                ]
            except Exception as e:
                logger.warning(f"LanceDB search failed: {e}")

        # JSON fallback: keyword search
        return self._json_search(query, k, table_name)

    def get_audit_by_url(self, url: str) -> Optional[dict]:
        """Retrieve the most recent audit for a specific URL."""
        self._ensure_init()

        if self._db:
            try:
                if "audits" not in self._db.table_names():
                    return None

                table = self._db.open_table("audits")
                # LanceDB filter
                results = table.search().where(f"url = '{url}'").limit(1).to_list()
                if results:
                    r = results[0]
                    return {k: v for k, v in r.items() if k != "vector"}
            except Exception as e:
                logger.warning(f"LanceDB URL lookup failed: {e}")

        return self._json_lookup(url)

    def get_all_audits(self, limit: int = 50) -> list[dict]:
        """Get all stored audits, most recent first."""
        self._ensure_init()

        if self._db:
            try:
                if "audits" not in self._db.table_names():
                    return []

                table = self._db.open_table("audits")
                results = table.to_pandas().sort_values("timestamp", ascending=False).head(limit)
                records = results.to_dict("records")
                return [{k: v for k, v in r.items() if k != "vector"} for r in records]
            except Exception as e:
                logger.warning(f"LanceDB list failed: {e}")

        return self._json_list_all(limit)

    # ================================================================
    # Public: Stats
    # ================================================================

    def get_stats(self) -> dict:
        """Get store statistics."""
        self._ensure_init()

        stats = {
            "backend": "lancedb" if self._db else "json_fallback",
            "embeddings": "active" if self._embedder else "disabled",
            "db_path": str(self._db_path),
        }

        if self._db:
            try:
                for table_name in ["audits", "evidence"]:
                    if table_name in self._db.table_names():
                        table = self._db.open_table(table_name)
                        stats[f"{table_name}_count"] = len(table)
                    else:
                        stats[f"{table_name}_count"] = 0
            except Exception:
                pass

        return stats

    # ================================================================
    # Private: JSON Fallback
    # ================================================================

    def _json_store(self, record: dict, filename: str = "audits.jsonl") -> bool:
        """Append a record to a JSONL file (fallback when LanceDB unavailable)."""
        try:
            filepath = self._db_path / filename
            # Remove vector field for JSON storage
            record = {k: v for k, v in record.items() if k != "vector"}
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, default=str) + "\n")
            return True
        except Exception as e:
            logger.error(f"JSON store failed: {e}")
            return False

    def _json_search(self, query: str, k: int, table_name: str) -> list[dict]:
        """Simple keyword search in JSONL (fallback)."""
        filepath = self._db_path / f"{table_name}.jsonl"
        if not filepath.exists():
            return []

        results = []
        query_lower = query.lower()
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        record = json.loads(line)
                        # Simple relevance: count query word matches
                        record_text = json.dumps(record).lower()
                        score = sum(1 for word in query_lower.split() if word in record_text)
                        if score > 0:
                            results.append((score, record))

            results.sort(key=lambda x: x[0], reverse=True)
            return [r[1] for r in results[:k]]
        except Exception:
            return []

    def _json_lookup(self, url: str) -> Optional[dict]:
        """Find a record by URL in JSONL (fallback)."""
        filepath = self._db_path / "audits.jsonl"
        if not filepath.exists():
            return None

        latest = None
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        record = json.loads(line)
                        if record.get("url") == url:
                            latest = record
            return latest
        except Exception:
            return None

    def _json_list_all(self, limit: int) -> list[dict]:
        """List all records from JSONL, sorted by timestamp descending."""
        filepath = self._db_path / "audits.jsonl"
        if not filepath.exists():
            return []

        records = []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        records.append(json.loads(line))
            records.sort(key=lambda r: r.get("timestamp", 0), reverse=True)
            return records[:limit]
        except Exception:
            return []

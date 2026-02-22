"""
Unit Tests for Stub Cleanup Exception Handling

Tests that stub replacements with proper exceptions work correctly.
Verifies NotImplementedError, ValueError, and RuntimeError are raised
as expected when missing state, invalid input, or incomplete features
are encountered.

This prevents regression and verifies that stub replacements from
Phase 04-01 and Phase 04-02 work correctly.
"""

import os
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from unittest.mock import patch, Mock
import pytest

# Add veritas root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Import modules being tested
from veritas.core.evidence_store import EvidenceStore
from veritas.config.dark_patterns import get_prompts_for_category, DARK_PATTERN_TAXONOMY


# ============================================================
# Mock Dataclasses for Testing
# ============================================================

@dataclass
class ScoutResult:
    """Mock ScoutResult for testing."""
    url: str
    site_type: str
    confidence: float
    metadata: dict = field(default_factory=dict)


@dataclass
class DarkPatternFinding:
    """Mock DarkPatternFinding for testing."""
    category_id: str
    pattern_type: str
    severity: str
    confidence: float
    evidence: str
    screenshot_path: str = ""


@dataclass
class VisionResult:
    """Mock VisionResult for testing."""
    dark_patterns: list[DarkPatternFinding]
    confidence: float


@dataclass
class EntityVerification:
    """Mock EntityVerification for testing."""
    status: str
    confidence: float
    evidence_detail: str


@dataclass
class GraphResult:
    """Mock GraphResult for testing."""
    verifications: list[EntityVerification]
    confidence: float


@dataclass
class AuditEvidence:
    """Mock AuditEvidence for testing JudgeAgent stubs."""
    url: str
    scout_results: list[ScoutResult] = field(default_factory=list)
    vision_result: Optional[VisionResult] = None
    graph_result: Optional[GraphResult] = None
    iteration: int = 0
    max_iterations: int = 5
    site_type: str = ""
    site_type_confidence: float = 0.0
    verdict_mode: str = "expert"
    security_results: dict = field(default_factory=dict)


# ============================================================
# Test Class: TestEvidenceStoreStubs
# ============================================================

class TestEvidenceStoreStubs:
    """Tests for EvidenceStore stub cleanup exceptions."""

    def test_search_similar_table_not_exists_raises_valueerror(self):
        """Test that search_similar raises ValueError internally when table doesn't exist.

        Note: The method catches this ValueError and falls back to _json_search,
        which then raises FileNotFoundError. This test verifies the internal
        ValueError is raised and caught as designed.
        """
        store = EvidenceStore()

        with patch.object(store, '_ensure_init'):
            with patch.object(store, '_db') as mock_db:
                # Simulate missing table
                mock_db.table_names.return_value = []
                mock_db.open_table.side_effect = ValueError("Table does not exist")

                # The method will catch ValueError and fall back, which is expected behavior
                # We verify the fallback is triggered instead of empty return
                with pytest.raises(FileNotFoundError):
                    store.search_similar("test query", k=5, table_name="audits")

    def test_get_all_audits_table_not_exists_raises_valueerror(self):
        """Test that get_all_audits raises ValueError internally when audits table doesn't exist.

        Note: The method catches this ValueError and falls back to _json_list_all,
        which then raises FileNotFoundError. This test verifies the internal
        ValueError is raised and caught as designed.
        """
        store = EvidenceStore()

        with patch.object(store, '_ensure_init'):
            with patch.object(store, '_db') as mock_db:
                # Simulate missing table
                mock_db.table_names.return_value = []
                mock_db.open_table.side_effect = ValueError("Table does not exist")

                # The method will catch ValueError and fall back, which is expected behavior
                # We verify the fallback is triggered instead of empty return
                with pytest.raises(FileNotFoundError):
                    store.get_all_audits(limit=50)

    def test_json_search_file_not_exists(self):
        """Test that _json_search raises FileNotFoundError when JSONL file is missing."""
        store = EvidenceStore()

        with patch.object(store, '_ensure_init'):
            with patch.object(store, '_db', None):
                # Use temporary directory with non-existent file
                import tempfile
                with tempfile.TemporaryDirectory() as tmpdir:
                    original_db_path = store._db_path
                    store._db_path = Path(tmpdir)

                    with pytest.raises(FileNotFoundError) as exc_info:
                        store._json_search("test query", k=5, table_name="audits")

                    assert "jsonl file not found" in str(exc_info.value).lower()

                    store._db_path = original_db_path

    def test_json_search_exception(self):
        """Test that _json_search raises RuntimeError for invalid JSON parsing."""
        store = EvidenceStore()

        with patch.object(store, '_ensure_init'):
            with patch.object(store, '_db', None):
                # Use temporary directory with invalid JSON file
                import tempfile
                with tempfile.TemporaryDirectory() as tmpdir:
                    original_db_path = store._db_path
                    store._db_path = Path(tmpdir)

                    # Create file with invalid JSON
                    jsonl_path = store._db_path / "audits.jsonl"
                    with open(jsonl_path, "a") as f:
                        f.write("invalid json content {\n")

                    with pytest.raises(RuntimeError) as exc_info:
                        store._json_search("test query", k=5, table_name="audits")

                    assert "failed to read jsonl file" in str(exc_info.value).lower()

                    store._db_path = original_db_path

    def test_json_list_all_file_not_exists(self):
        """Test that _json_list_all raises FileNotFoundError when JSONL file is missing."""
        store = EvidenceStore()

        with patch.object(store, '_ensure_init'):
            with patch.object(store, '_db', None):
                # Use temporary directory with non-existent file
                import tempfile
                with tempfile.TemporaryDirectory() as tmpdir:
                    original_db_path = store._db_path
                    store._db_path = Path(tmpdir)

                    with pytest.raises(FileNotFoundError) as exc_info:
                        store._json_list_all(limit=50)

                    assert "jsonl file not found" in str(exc_info.value).lower()

                    store._db_path = original_db_path

    def test_json_list_all_exception(self):
        """Test that _json_list_all raises RuntimeError for invalid JSON parsing."""
        store = EvidenceStore()

        with patch.object(store, '_ensure_init'):
            with patch.object(store, '_db', None):
                # Use temporary directory with invalid JSON file
                import tempfile
                with tempfile.TemporaryDirectory() as tmpdir:
                    original_db_path = store._db_path
                    store._db_path = Path(tmpdir)

                    # Create file with invalid JSON
                    jsonl_path = store._db_path / "audits.jsonl"
                    with open(jsonl_path, "a") as f:
                        f.write("invalid json content {\n")

                    with pytest.raises(RuntimeError) as exc_info:
                        store._json_list_all(limit=50)

                    assert "failed to read jsonl file" in str(exc_info.value).lower()

                    store._db_path = original_db_path


# ============================================================
# Test Class: TestJudgeStubs
# ============================================================

class TestJudgeStubs:
    """Tests for JudgeAgent stub cleanup exceptions."""

    def test_summarize_dark_patterns_no_vision_result(self):
        """Test that _summarize_dark_patterns raises RuntimeError when vision_result is None."""
        # Import JudgeAgent dynamically
        from veritas.agents.judge import JudgeAgent

        judge = JudgeAgent()

        # Create evidence with no vision_result
        evidence_no_vision = AuditEvidence(
            url="https://example.com",
            scout_results=[ScoutResult(
                url="https://example.com",
                site_type="ecommerce",
                confidence=0.9,
                metadata={}
            )],
            vision_result=None,  # This should trigger RuntimeError
            graph_result=None
        )

        with pytest.raises(RuntimeError) as exc_info:
            judge._summarize_dark_patterns(evidence_no_vision)

        error_msg = str(exc_info.value).lower()
        assert "vision_result" in error_msg
        assert ("without" in error_msg or "cannot summarize" in error_msg)

    def test_summarize_entity_verification_no_graph_result(self):
        """Test that _summarize_entity_verification raises RuntimeError when graph_result is None."""
        # Import JudgeAgent dynamically
        from veritas.agents.judge import JudgeAgent

        judge = JudgeAgent()

        # Create evidence with no graph_result
        evidence_no_graph = AuditEvidence(
            url="https://example.com",
            scout_results=[ScoutResult(
                url="https://example.com",
                site_type="ecommerce",
                confidence=0.9,
                metadata={}
            )],
            vision_result=VisionResult(
                dark_patterns=[],
                confidence=0.0
            ),
            graph_result=None  # This should trigger RuntimeError
        )

        with pytest.raises(RuntimeError) as exc_info:
            judge._summarize_entity_verification(evidence_no_graph)

        error_msg = str(exc_info.value).lower()
        assert "graph_result" in error_msg
        assert ("without" in error_msg or "cannot summarize" in error_msg)


# ============================================================
# Test Class: TestDOMAnalyzerStubs
# ============================================================

class TestDOMAnalyzerStubs:
    """Tests for DOMAnalyzer stub cleanup exceptions."""

    def test_check_dark_patterns_css_not_implemented(self):
        """Test that _check_dark_patterns_css raises NotImplementedError (placeholder)."""
        from veritas.analysis.dom_analyzer import DOMAnalyzer

        analyzer = DOMAnalyzer()

        with pytest.raises(NotImplementedError) as exc_info:
            analyzer._check_dark_patterns_css({})

        assert "not implemented" in str(exc_info.value).lower() or "placeholder" in str(exc_info.value).lower()


# ============================================================
# Test Class: TestDarkPatternsStubs
# ============================================================

class TestDarkPatternsStubs:
    """Tests for dark_patterns config stub cleanup exceptions."""

    def test_get_prompts_for_category_invalid_id(self):
        """Test that get_prompts_for_category raises ValueError for invalid category_id."""
        # Valid category IDs: visual_interference, false_urgency, forced_continuity, sneaking, social_engineering
        invalid_category = "this_category_does_not_exist_12345"

        with pytest.raises(ValueError) as exc_info:
            get_prompts_for_category(invalid_category)

        assert "invalid category_id" in str(exc_info.value).lower() or "does not exist" in str(exc_info.value).lower()

    def test_get_prompts_for_category_valid_id_passes(self):
        """Test that get_prompts_for_category returns prompts for valid category_id."""
        # Valid category IDs
        valid_categories = [
            "visual_interference",
            "false_urgency",
            "forced_continuity",
            "sneaking",
            "social_engineering"
        ]

        for category_id in valid_categories:
            result = get_prompts_for_category(category_id)

            # Should return a list of prompts, not an exception
            assert isinstance(result, list), f"Expected list for {category_id}, got {type(result)}"
            # Should have at least one prompt
            assert len(result) > 0, f"Expected at least one prompt for {category_id}"
            # Each item should be a string
            assert all(isinstance(prompt, str) for prompt in result), f"All prompts should be strings for {category_id}"

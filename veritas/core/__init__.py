"""
Veritas Core Layer

Core modules provide shared infrastructure used by all agents:
- nim_client:      NVIDIA NIM API wrapper with fallback chain
- trust_scorer:    Weighted multi-signal scoring engine (Phase 2)
- evidence_store:  LanceDB-backed evidence persistence (Phase 3)
- knowledge_graph: NetworkX graph builder + query (Phase 2)
- orchestrator:    LangGraph state machine (Phase 3)
"""

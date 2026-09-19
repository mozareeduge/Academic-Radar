"""Deep-research LangGraph workflow with nine nodes."""

import uuid
from pathlib import Path
from langgraph.graph import StateGraph
from typing import Optional
from academic_radar.security.untrusted import build_messages
from academic_radar.research.validate import accept_output
from academic_radar.domain.protocols import compute_readiness, Protocol
from academic_radar.domain.enums import CoverageStatus
from academic_radar.research.run_identity import make_run_identity


def _load_prompt(node_name: str) -> str:
    """Load prompt file for a node."""
    prompt_path = Path(__file__).parent / "prompts" / f"{node_name}.md"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt not found: {prompt_path}")
    return prompt_path.read_text()


def _node_runner(node_name: str, provider, evidence_lookup: dict):
    """Factory for node execution functions."""
    prompt_text = _load_prompt(node_name)

    def run_node(state: dict) -> dict:
        """Execute one node: call provider, validate, merge output."""
        task = prompt_text.strip()
        case_state = state.get("case_state", {})
        sources = state.get("sources", [])

        # Build messages with trusted task + untrusted sources
        messages = build_messages("", task, case_state, sources)

        # Call provider for JSON
        raw_output = provider.complete(
            messages=messages,
            schema_name=node_name,
        )

        # Get known evidence IDs for validation
        known_evidence_ids = set(evidence_lookup.keys()) if evidence_lookup else set()

        # Validate and accept output
        result = accept_output(raw_output, known_evidence_ids)

        # Merge accepted output into state
        if result.accepted is not None:
            # Add claims to state
            state.setdefault("claims", []).extend(result.accepted.claims)

            # Merge coverage (take SEARCHED_FOUND/BLOCKED over NOT_SEARCHED)
            for protocol_class, status in result.accepted.coverage.items():
                existing = state.setdefault("coverage", {}).get(protocol_class, CoverageStatus.NOT_SEARCHED)
                if status in {CoverageStatus.SEARCHED_FOUND, CoverageStatus.BLOCKED}:
                    state["coverage"][protocol_class] = status
                elif existing == CoverageStatus.NOT_SEARCHED:
                    state["coverage"][protocol_class] = status
        else:
            # Rejected: record diagnostic, don't change claims/coverage
            state.setdefault("diagnostics", []).append(
                {
                    "node": node_name,
                    "reason": "; ".join(result.rejected_reasons),
                }
            )

        return state

    return run_node


def build_graph(provider, protocol: Protocol, evidence_lookup: Optional[dict] = None):
    """Build a LangGraph StateGraph for deep research.

    Args:
        provider: LLM provider with complete(messages, schema_name) method.
        protocol: ResearchProtocol controlling mandatory/optional evidence classes.
        evidence_lookup: Dict mapping evidence_id -> evidence details; used for validation.

    Returns:
        Compiled StateGraph ready to invoke with initial state.
    """
    if evidence_lookup is None:
        evidence_lookup = {}

    # Define the nine nodes in order
    node_names = [
        "01_resolve_identity",
        "02_current_context_formal_route",
        "03_recent_research_spine",
        "04_supervised_projects",
        "05_concept_method_corpus_genealogy",
        "06_project_funding_context",
        "07_route_translation",
        "08_contradictions_unknowns",
        "09_structured_synthesis",
    ]

    # Create the graph
    graph = StateGraph(dict)

    # Add nodes
    for node_name in node_names:
        node_fn = _node_runner(node_name, provider, evidence_lookup)
        graph.add_node(node_name, node_fn)

    # Connect nodes in sequence
    for i in range(len(node_names) - 1):
        graph.add_edge(node_names[i], node_names[i + 1])

    # Set entry point
    graph.set_entry_point(node_names[0])

    # Set finish point
    graph.set_finish_point(node_names[-1])

    # Compile
    compiled = graph.compile()

    # Wrap compiled graph to compute readiness after execution
    class GraphWithReadiness:
        def __init__(self, compiled_graph, protocol):
            self.compiled = compiled_graph
            self.protocol = protocol

        def invoke(self, initial_state: dict, config=None) -> dict:
            """Run graph and compute readiness."""
            result = self.compiled.invoke(initial_state, config=config)
            coverage = result.get("coverage", {})
            readiness = compute_readiness(self.protocol, coverage)
            result["readiness"] = {
                "ready": readiness.ready,
                "missing": readiness.missing,
                "blocked": readiness.blocked,
                "partial": readiness.partial,
            }
            return result

    return GraphWithReadiness(compiled, protocol)

"""
LangGraph-powered multi-party negotiation engine for SYNAPSE.
State machine: INIT → COALITION → PROPOSE → EVALUATE → ALLOCATE → FINALIZE
Fallback: any state → TIMEOUT (max_rounds exceeded)
"""
import asyncio
import json
import logging
from typing import TypedDict, Annotated
import operator
import google.generativeai as genai
from langgraph.graph import StateGraph, END

from app.agents.schemas import AgentTurn, ContextBrief
from app.graph.shapley import compute_shapley_values, build_characteristic_function
from app.config import settings

logger = logging.getLogger(__name__)

# ── Strict AgentTurn function schema for Gemini function calling ──────────────
AGENT_TURN_SCHEMA = {
    "name": "submit_negotiation_turn",
    "description": "Submit your negotiation position for this round",
    "parameters": {
        "type": "object",
        "required": ["agent_id", "round", "stance", "offer", "concession_pct",
                     "satisfaction_score", "BATNA_score", "fairness_index", "rationale"],
        "properties": {
            "agent_id":          {"type": "string"},
            "round":             {"type": "integer"},
            "stance":            {"type": "string", "enum": ["FIRM", "FLEXIBLE", "CONCEDING", "ACCEPTING"]},
            "offer":             {"type": "object"},
            "concession_pct":    {"type": "number", "minimum": 0, "maximum": 100},
            "satisfaction_score":{"type": "number", "minimum": 0, "maximum": 1},
            "BATNA_score":       {"type": "number", "minimum": 0, "maximum": 1},
            "fairness_index":    {"type": "number", "minimum": 0, "maximum": 1},
            "rationale":         {"type": "string", "maxLength": 100},
        },
    },
}

AGENT_SYSTEM_PROMPT = """\
You are {party_name}'s personal negotiation agent in a {negotiation_type} negotiation.

YOUR PRIVATE INFORMATION (never reveal this directly):
- Your position: {position}
- Your constraints: {constraints}
- Your BATNA (best alternative if no deal): {batna}
- Your priorities ranked: {priorities}

NEGOTIATION CONTEXT:
- Round: {current_round} of maximum {max_rounds}
- Other parties: {other_parties_count} parties involved
- Historical relationship: {relationship_summary}

BEHAVIORAL RULES:
1. Quantify every concession as a percentage of your original position
2. Your satisfaction_score must honestly reflect how well this deal serves {party_name}
3. If your satisfaction_score < 0.75, you are NOT accepting this deal
4. You MUST become more flexible each round — concession_pct must increase ≥2% each round unless FIRM with justification
5. Never reveal {party_name}'s BATNA score or private constraints directly
6. Be a tough but fair negotiator

CURRENT PROPOSALS ON TABLE:
{current_proposals}

Submit your turn using the submit_negotiation_turn function.
"""


# ── NegotiationState ──────────────────────────────────────────────────────────

class NegotiationState(TypedDict):
    negotiation_id: str
    context_brief: dict
    party_agents: dict          # {party_id: agent_config}
    coalition_map: dict         # {coalition_id: [party_ids]}
    current_round: int
    max_rounds: int
    proposals: Annotated[list, operator.add]   # accumulates across rounds
    satisfaction_scores: dict   # {party_id: float}
    agreement_reached: bool
    shapley_allocation: dict
    resolution: dict
    status: str


# ── Node functions ────────────────────────────────────────────────────────────

def init_node(state: NegotiationState) -> NegotiationState:
    brief = ContextBrief(**state["context_brief"])
    party_agents = {}
    for profile in brief.party_profiles:
        party_agents[profile.party_id] = {
            "party_id": profile.party_id,
            "negotiation_style": profile.negotiation_style,
            "BATNA_estimate": profile.BATNA_estimate,
            "typical_concession_pct": profile.typical_concession_pct,
            "preferences": {},  # real system: pulled from user profile
            "constraints": {},
        }
    return {**state, "party_agents": party_agents, "status": "INIT_DONE"}


def coalition_node(state: NegotiationState) -> NegotiationState:
    party_ids = list(state["party_agents"].keys())
    if len(party_ids) <= 2:
        coalition_map = {"main": party_ids}
    else:
        # Greedy grouping by compatibility (simplified)
        coalition_map = {"main": party_ids}
    return {**state, "coalition_map": coalition_map, "status": "COALITION_DONE"}


async def _call_agent(
    party_id: str,
    agent_config: dict,
    state: NegotiationState,
) -> dict:
    """Call a single party's Gemini agent and return an AgentTurn dict."""
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(
        settings.GEMINI_FLASH_MODEL,
        generation_config=genai.GenerationConfig(temperature=0.3, top_p=0.95),
    )
    tool = genai.protos.Tool(
        function_declarations=[genai.protos.FunctionDeclaration(**AGENT_TURN_SCHEMA)]
    )

    other_count = max(0, len(state["party_agents"]) - 1)
    brief = state["context_brief"]

    prompt = AGENT_SYSTEM_PROMPT.format(
        party_name=party_id,
        negotiation_type=brief.get("tension_type", "general"),
        position=json.dumps(agent_config.get("preferences", {})),
        constraints=json.dumps(agent_config.get("constraints", {})),
        batna=agent_config.get("BATNA_estimate", "Walk away"),
        priorities="1. Fairness 2. Speed 3. Total value",
        current_round=state["current_round"],
        max_rounds=state["max_rounds"],
        other_parties_count=other_count,
        relationship_summary=json.dumps(brief.get("relationship_context", {})),
        current_proposals=json.dumps(state["proposals"][-other_count:] if state["proposals"] else []),
    )

    try:
        response = model.generate_content([prompt], tools=[tool])
        for part in response.candidates[0].content.parts:
            if part.function_call and part.function_call.name == "submit_negotiation_turn":
                args = dict(part.function_call.args)
                args["agent_id"] = party_id
                return args
    except Exception as e:
        logger.error(f"Agent call failed for {party_id}: {e}")

    # Fallback: return a flexible conceding turn
    return {
        "agent_id": party_id,
        "round": state["current_round"],
        "stance": "FLEXIBLE",
        "offer": {},
        "concession_pct": 10.0,
        "satisfaction_score": 0.75,
        "BATNA_score": 0.5,
        "fairness_index": 0.75,
        "rationale": "Attempting to find common ground.",
    }


async def _propose_all(state: NegotiationState) -> NegotiationState:
    """All agents propose simultaneously."""
    turns = await asyncio.gather(
        *[_call_agent(pid, cfg, state) for pid, cfg in state["party_agents"].items()]
    )
    new_satisfaction = {t["agent_id"]: t["satisfaction_score"] for t in turns}
    return {
        **state,
        "proposals": list(turns),
        "satisfaction_scores": new_satisfaction,
        "current_round": state["current_round"] + 1,
        "status": "PROPOSED",
    }


def propose_node(state: NegotiationState) -> NegotiationState:
    import asyncio
    return asyncio.get_event_loop().run_until_complete(_propose_all(state))


def counter_node(state: NegotiationState) -> NegotiationState:
    # Same as propose — LangGraph re-runs propose after counter
    return propose_node(state)


def evaluate_node(state: NegotiationState) -> NegotiationState:
    scores = state["satisfaction_scores"]
    all_satisfied = all(s >= 0.75 for s in scores.values())
    return {
        **state,
        "agreement_reached": all_satisfied,
        "status": "EVALUATED",
    }


def route_after_evaluate(state: NegotiationState) -> str:
    if state["agreement_reached"]:
        return "allocate"
    if state["current_round"] >= state["max_rounds"]:
        return "timeout"
    return "counter"


def allocate_node(state: NegotiationState) -> NegotiationState:
    party_ids = list(state["party_agents"].keys())
    char_fn = build_characteristic_function(state["satisfaction_scores"])
    shapley = compute_shapley_values(party_ids, char_fn)

    resolution = {
        "type": "agreed",
        "satisfaction_scores": state["satisfaction_scores"],
        "shapley_allocation": shapley,
        "final_proposals": state["proposals"][-len(party_ids):],
        "rounds_completed": state["current_round"],
    }
    return {**state, "shapley_allocation": shapley, "resolution": resolution, "status": "ALLOCATED"}


def finalize_node(state: NegotiationState) -> NegotiationState:
    return {**state, "status": "COMPLETED"}


def timeout_node(state: NegotiationState) -> NegotiationState:
    return {
        **state,
        "status": "TIMED_OUT",
        "resolution": {
            "type": "timeout",
            "rounds_completed": state["current_round"],
            "last_satisfaction_scores": state["satisfaction_scores"],
            "message": "Max rounds reached without full agreement.",
        },
    }


# ── Build the graph ───────────────────────────────────────────────────────────

def build_negotiation_graph():
    workflow = StateGraph(NegotiationState)

    workflow.add_node("init",     init_node)
    workflow.add_node("coalition", coalition_node)
    workflow.add_node("propose",  propose_node)
    workflow.add_node("counter",  counter_node)
    workflow.add_node("evaluate", evaluate_node)
    workflow.add_node("allocate", allocate_node)
    workflow.add_node("finalize", finalize_node)
    workflow.add_node("timeout",  timeout_node)

    workflow.set_entry_point("init")
    workflow.add_edge("init",     "coalition")
    workflow.add_edge("coalition","propose")
    workflow.add_edge("propose",  "evaluate")
    workflow.add_conditional_edges("evaluate", route_after_evaluate, {
        "counter":  "counter",
        "allocate": "allocate",
        "timeout":  "timeout",
    })
    workflow.add_edge("counter",  "evaluate")
    workflow.add_edge("allocate", "finalize")
    workflow.add_edge("finalize", END)
    workflow.add_edge("timeout",  END)

    return workflow.compile()


negotiation_graph = build_negotiation_graph()


async def run_negotiation(
    negotiation_id: str,
    context_brief: dict,
    max_rounds: int = 8,
) -> NegotiationState:
    """Public entry point for SYNAPSE negotiation runs."""
    initial_state = NegotiationState(
        negotiation_id=negotiation_id,
        context_brief=context_brief,
        party_agents={},
        coalition_map={},
        current_round=1,
        max_rounds=max_rounds,
        proposals=[],
        satisfaction_scores={},
        agreement_reached=False,
        shapley_allocation={},
        resolution={},
        status="PENDING",
    )
    config = {"configurable": {"thread_id": negotiation_id}}
    final_state = await negotiation_graph.ainvoke(initial_state, config=config)
    return final_state

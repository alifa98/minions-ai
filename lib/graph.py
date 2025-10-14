from langgraph.graph import END, StateGraph

from lib.state import DatasetCompilationState
from nodes.debator import debate_agent_node
from nodes.extractor import extraction_agent_node
from nodes.filter import filter_agent_node
from nodes.orchestrator import orchestrator_node, orchestrator_router
from nodes.search import search_agent_node
from nodes.validator import validation_agent_node


def get_state_graph(checkpointer):
    """Define and return the state graph for the multi-agent workflow."""
    workflow = StateGraph(DatasetCompilationState)

    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("search_agent", search_agent_node)
    workflow.add_node("extraction_agent", extraction_agent_node)
    workflow.add_node("filter_agent", filter_agent_node)
    workflow.add_node("validation_agent", validation_agent_node)
    workflow.add_node("debate_agent_node", debate_agent_node)
    # Debate agent is called by other agents, not a standalone node in this flow.

    workflow.set_entry_point("orchestrator")

    workflow.add_conditional_edges(
        "orchestrator",
        orchestrator_router,
        {
            "search": "search_agent",
            "extract": "extraction_agent",
            "filter": "filter_agent",
            "validate": "validation_agent",
            "debate": "debate_agent_node",
            "complete": END
        }
    )

    # All workers return control to the orchestrator for the next decision
    workflow.add_edge("search_agent", "orchestrator")
    workflow.add_edge("extraction_agent", "filter_agent")
    workflow.add_edge("filter_agent", "validation_agent")
    workflow.add_edge("validation_agent", "debate_agent_node")
    workflow.add_edge("debate_agent_node", "orchestrator")  # the ideal
    # workflow.add_edge("debate_agent_node", END) # Test

    return workflow.compile(checkpointer=checkpointer)

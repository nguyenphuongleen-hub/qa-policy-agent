from langgraph.graph import StateGraph, END
from qa_policy_agent.agent.state import AgentState
from qa_policy_agent.agent.nodes.classify import classify_request
from qa_policy_agent.agent.nodes.retrieve import retrieve_context
from qa_policy_agent.agent.nodes.relevance import check_relevance
from qa_policy_agent.agent.nodes.generate import generate_answer
from qa_policy_agent.agent.nodes.verify import verify_answer
from qa_policy_agent.config import settings


def route_after_classify(state: AgentState) -> str:
    decision = state["classification"]["decision"]
    if decision == "block":
        return END
    if decision == "clarify":
        return END
    if decision == "fallback":
        return END
    return "retrieve_context"


def route_after_relevance(state: AgentState) -> str:
    if not state["relevant_chunks"]:
        return END
    return "generate_answer"


def route_after_verify(state: AgentState) -> str:
    if state["verification"]["passed"]:
        return END
    if state.get("retry_count", 0) < settings.max_retries:
        return "generate_answer"
    return END


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("classify_request", classify_request)
    graph.add_node("retrieve_context", retrieve_context)
    graph.add_node("check_relevance", check_relevance)
    graph.add_node("generate_answer", generate_answer)
    graph.add_node("verify_answer", verify_answer)

    graph.set_entry_point("classify_request")
    graph.add_conditional_edges("classify_request", route_after_classify)
    graph.add_edge("retrieve_context", "check_relevance")
    graph.add_conditional_edges("check_relevance", route_after_relevance)
    graph.add_edge("generate_answer", "verify_answer")
    graph.add_conditional_edges("verify_answer", route_after_verify)

    return graph.compile()
 
 
def build_graph():
    graph = StateGraph(AgentState)
 
    graph.add_node("classify_request", classify_request)
    graph.add_node("retrieve_context", retrieve_context)
    graph.add_node("check_relevance", check_relevance)
    graph.add_node("generate_answer", generate_answer)
    graph.add_node("verify_answer", verify_answer)
 
    graph.set_entry_point("classify_request")
    graph.add_conditional_edges("classify_request", route_after_classify)
    graph.add_edge("retrieve_context", "check_relevance")
    graph.add_conditional_edges("check_relevance", route_after_relevance)
    graph.add_edge("generate_answer", "verify_answer")
    graph.add_conditional_edges("verify_answer", route_after_verify)
 
    return graph.compile()
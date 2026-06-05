from fastapi import FastAPI, Request
from qa_policy_agent.models import AskRequest, AskSuccess, AskError, NoAnswer, Citation
from qa_policy_agent.agent.graph import build_graph

# Import node functions so we can test each step individually via debug endpoints
from qa_policy_agent.agent.nodes.classify import classify_request
from qa_policy_agent.agent.nodes.retrieve import retrieve_context
from qa_policy_agent.agent.nodes.relevance import check_relevance
from qa_policy_agent.agent.nodes.generate import generate_answer
from qa_policy_agent.agent.nodes.verify import verify_answer


app = FastAPI(title="QA Policy Agent")
agent = build_graph()
 
 
@app.get("/health")
async def health():
    return {"status": "ok"}
 
 
@app.post("/ask")
async def ask(req: AskRequest):
    initial_state = {
        "question": req.question,
        "conversation_history": [],
        "retrieved_chunks": [],
        "relevant_chunks": [],
        "citations": [],
        "retry_count": 0,
        "error": None,
    }
 
    result = await agent.ainvoke(initial_state)
 
    classification = result.get("classification", {})
 
    if classification.get("decision") == "block":
        return AskError(
            error=classification.get("reason", "Câu hỏi bị từ chối."),
            error_type="blocked",
        )
 
    if classification.get("decision") == "fallback":
        return AskError(
            error="Câu hỏi không thuộc phạm vi chính sách ngân hàng.",
            error_type="out_of_scope",
        )
 
    if not result.get("relevant_chunks"):
        return NoAnswer(message="Không tìm thấy thông tin liên quan trong tài liệu chính sách.")
 
    return AskSuccess(
        answer=result.get("answer", ""),
        citations=[
            Citation(source_file=c["source_file"], section=c["section"])
            for c in result.get("citations", [])
        ],
        confidence=result.get("verification", {}).get("confidence", 0.0),
    )
 

# Debug endpoints: call individual nodes with minimal state. Useful for step-by-step testing.


@app.post("/debug/classify")
async def debug_classify(req: AskRequest):
    state = {"question": req.question}
    res = await classify_request(state)
    return res


@app.post("/debug/retrieve")
async def debug_retrieve(req: AskRequest):
    # classification.detected_topics can be populated from category_filter for testing
    state = {
        "question": req.question,
        "classification": {"detected_topics": req.category_filter or []},
    }
    res = await retrieve_context(state)

    # retrieved chunks may be dataclasses/models; try converting to serializable form
    def _serialize_chunks(chunks):
        out = []
        for c in chunks:
            try:
                out.append(c.dict())
            except Exception:
                try:
                    out.append(vars(c))
                except Exception:
                    out.append(c)
        return out

    return {"retrieved_chunks": _serialize_chunks(res.get("retrieved_chunks", []))}


@app.post("/debug/check_relevance")
async def debug_check_relevance(request: Request):
    body = await request.json()
    state = {"retrieved_chunks": body.get("retrieved_chunks", [])}
    res = await check_relevance(state)
    return {"relevant_chunks": res.get("relevant_chunks", [])}


@app.post("/debug/generate")
async def debug_generate(request: Request):
    body = await request.json()
    state = {"question": body.get("question", ""), "relevant_chunks": body.get("relevant_chunks", [])}
    res = await generate_answer(state)
    return {"answer": res.get("answer"), "citations": res.get("citations", []), "retry_count": res.get("retry_count", 0)}


@app.post("/debug/verify")
async def debug_verify(request: Request):
    body = await request.json()
    state = {"relevant_chunks": body.get("relevant_chunks", []), "answer": body.get("answer", "")}
    res = await verify_answer(state)
    return {"verification": res.get("verification")}



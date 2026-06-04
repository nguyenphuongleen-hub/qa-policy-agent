from fastapi import FastAPI
from qa_policy_agent.models import AskRequest, AskSuccess, AskError, NoAnswer, Citation
from qa_policy_agent.agent.graph import build_graph
 
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
 


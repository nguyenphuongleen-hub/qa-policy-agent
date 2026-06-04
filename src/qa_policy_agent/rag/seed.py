import os
from pathlib import Path
from langchain.schema import Document
from qa_policy_agent.rag.chunker import chunk_markdown
from qa_policy_agent.rag.store import get_store

POLICIES_DIR = Path("data/policies")


def seed():
    store = get_store()
    docs = []
    for md_file in POLICIES_DIR.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        metadata = {
            "source_file": str(md_file),
            "document_title": md_file.stem,
        }
        chunks = chunk_markdown(content, metadata)
        for chunk in chunks:
            docs.append(Document(page_content=chunk.text, metadata=chunk.metadata))

    store.add_documents(docs)
    print(f"Seeded {len(docs)} chunks from {POLICIES_DIR}")


if __name__ == "__main__":
    seed()

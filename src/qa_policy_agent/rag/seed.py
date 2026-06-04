"""Seed ChromaDB from data/policies/**/*.md — run: python -m qa_policy_agent.rag.seed"""
import pathlib
import yaml
from qa_policy_agent.rag.chunker import chunk_markdown
from qa_policy_agent.rag.store import PolicyStore


def extract_frontmatter(content: str) -> tuple[dict, str]:
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            meta = yaml.safe_load(parts[1])
            return meta or {}, parts[2].strip()
    return {}, content


def seed(data_dir: str = "data/policies"):
    store = PolicyStore()
    root = pathlib.Path(data_dir)
    total_chunks = 0

    for md_file in sorted(root.rglob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        frontmatter, body = extract_frontmatter(content)

        category = md_file.parent.name
        metadata_base = {
            "source_file": str(md_file.relative_to(root)),
            "document_title": frontmatter.get("title", md_file.stem.replace("_", " ").title()),
            "category": category,
            "effective_date": frontmatter.get("effective_date", ""),
        }

        chunks = chunk_markdown(body, metadata_base)
        if not chunks:
            continue

        ids = [f"{md_file.stem}_{c.metadata['chunk_index']}" for c in chunks]
        texts = [c.text for c in chunks]
        metadatas = [c.metadata for c in chunks]

        store.add_documents(ids=ids, texts=texts, metadatas=metadatas)
        total_chunks += len(chunks)
        print(f"  {md_file.relative_to(root)}: {len(chunks)} chunks")

    print(f"\nDone. Total: {total_chunks} chunks. Collection size: {store.count()}")


if __name__ == "__main__":
    seed()
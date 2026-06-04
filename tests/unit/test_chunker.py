from qa_policy_agent.rag.chunker import chunk_markdown


def test_single_section_small():
    content = "## Điều kiện\n\nThu nhập tối thiểu 10 triệu."
    chunks = chunk_markdown(content, {"document_title": "Test"})
    assert len(chunks) == 1
    assert "10 triệu" in chunks[0].text


def test_multiple_sections():
    content = "## Section A\n\nContent A.\n\n## Section B\n\nContent B."
    chunks = chunk_markdown(content, {"document_title": "Test"})
    assert len(chunks) == 2
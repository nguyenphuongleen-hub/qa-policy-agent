import re
from dataclasses import dataclass


@dataclass
class Chunk:
    text: str
    metadata: dict


def chunk_markdown(
    content: str,
    metadata_base: dict,
    max_chunk_size: int = 800,
    overlap: int = 200,
) -> list[Chunk]:
    """Split markdown by ## headings, then by paragraphs if too long."""
    sections = re.split(r"(?=^## )", content, flags=re.MULTILINE)
    chunks = []

    for section in sections:
        section = section.strip()
        if not section:
            continue

        # Extract section title
        lines = section.split("\n", 1)
        title = lines[0].lstrip("# ").strip()
        body = lines[1].strip() if len(lines) > 1 else ""

        # Prepend context
        text = f"{metadata_base.get('document_title', '')}\n{title}\n\n{body}"

        if len(text) <= max_chunk_size:
            chunks.append(Chunk(
                text=text,
                metadata={**metadata_base, "section": title, "chunk_index": len(chunks)},
            ))
        else:
            # Split by paragraphs with overlap
            paragraphs = text.split("\n\n")
            current = ""
            for para in paragraphs:
                if len(current) + len(para) > max_chunk_size and current:
                    chunks.append(Chunk(
                        text=current.strip(),
                        metadata={**metadata_base, "section": title, "chunk_index": len(chunks)},
                    ))
                    current = current[-overlap:] + "\n\n" + para
                else:
                    current = current + "\n\n" + para if current else para
            if current.strip():
                chunks.append(Chunk(
                    text=current.strip(),
                    metadata={**metadata_base, "section": title, "chunk_index": len(chunks)},
                ))

    return chunks
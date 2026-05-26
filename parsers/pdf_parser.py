import pdfplumber
import io
from .document import ParsedDocument


def _table_to_markdown(table: list[list]) -> str:
    if not table or not table[0]:
        return ""
    headers = [str(cell or "").strip() for cell in table[0]]
    md = "| " + " | ".join(headers) + " |\n"
    md += "| " + " | ".join(["---"] * len(headers)) + " |\n"
    for row in table[1:]:
        cells = [str(cell or "").strip().replace("\n", " ") for cell in row]
        # Pad or truncate row to match header length
        while len(cells) < len(headers):
            cells.append("")
        cells = cells[: len(headers)]
        md += "| " + " | ".join(cells) + " |\n"
    return md


def parse_pdf(file_bytes: bytes, filename: str = "document.pdf") -> ParsedDocument:
    pages = []
    tables = []
    all_text_parts = []

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for i, page in enumerate(pdf.pages):
            page_num = i + 1
            text = page.extract_text() or ""
            pages.append(text)

            page_tables = page.extract_tables()
            for table in page_tables:
                if table and len(table) > 1:
                    md = _table_to_markdown(table)
                    tables.append({"page": page_num, "markdown": md})

            # Build combined text with page markers and tables inline
            part = f"\n--- Page {page_num} ---\n{text}"
            for table in page_tables:
                if table and len(table) > 1:
                    part += "\n\n[Table]\n" + _table_to_markdown(table)
            all_text_parts.append(part)

    raw_text = "\n".join(all_text_parts)

    return ParsedDocument(
        raw_text=raw_text,
        pages=pages,
        tables=tables,
        filename=filename,
        page_count=len(pages),
        file_type="pdf",
    )

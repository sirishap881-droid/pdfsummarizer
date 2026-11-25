"""Phase 2 smoke test: end-to-end PDF -> summary via Gemini."""

from pathlib import Path

from pdf_processor import PDFProcessor
from summarizer import PDFSummarizer

SAMPLE = Path("sample.pdf")
SAMPLE_TEXT = (
    "Python is a versatile programming language widely used for scripting, automation and data analysis.\n"
    "PDFs contain text and images. Extracting and summarizing them saves time and effort.\n"
    "The quick brown fox jumps over the lazy dog. Pack my box with five dozen liquor jugs.\n"
    "Sphinx of black quartz, judge my vow. Whenever the sun shines I am happy.\n"
    "Learning new skills keeps skills sharp and opens new opportunities for the future."
)


def _pdf_escape(s: str) -> str:
    return s.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def make_sample_pdf(path: Path, text: str) -> None:
    """Create a small valid one-page PDF with the given lines of text."""
    if path.exists():
        return
    lines = " ".join(f"({_pdf_escape(ln)}) Tj T*" for ln in text.splitlines())
    content = f"BT /F1 10 Tf 50 730 Td {lines} ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        f"<< /Length {len(content)} >>\nstream\n".encode() + content + b"\nendstream",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref_pos = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode()
    path.write_bytes(out)
    print(f"created sample PDF: {path} ({len(out)} bytes)")


def main() -> None:
    make_sample_pdf(SAMPLE, SAMPLE_TEXT)

    processor = PDFProcessor()
    with SAMPLE.open("rb") as f:
        metadata = processor.get_pdf_metadata(f)
        text = processor.extract_text_from_pdf(f)
    print("metadata:", metadata)
    print("extracted text length:", len(text))
    print("tokens:", processor.count_tokens(text))
    chunks = processor.chunk_text(text)
    print("chunks:", len(chunks), "lengths:", [len(c) for c in chunks])

    summarizer = PDFSummarizer()
    result = summarizer.summarize_chunks(chunks, summary_type="brief")
    print("summary type:", result["summary_type"])
    print("total chunks:", result["total_chunks"])
    print("ok:", all(s["ok"] for s in result["individual_summaries"]))
    print("combined summary:")
    print(result["combined_summary"])


if __name__ == "__main__":
    main()

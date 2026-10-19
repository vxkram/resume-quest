import io

import docx
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from analyzer.extract import BadUpload, clean, detect_type, extract_text


def test_detects_pdf_and_docx_from_bytes(sample_pdf, sample_docx):
    assert detect_type(sample_pdf) == "pdf"
    assert detect_type(sample_docx) == "docx"
    assert detect_type(b"PK\x03\x04 not really a zip") is None
    assert detect_type(b"<html>") is None


def test_extracts_pdf_text(sample_pdf):
    text, kind = extract_text(SimpleUploadedFile("cv.pdf", sample_pdf))
    assert kind == "pdf"
    assert "Alex Rivera" in text and "PyTorch" in text
    assert "(cid:" not in text  # unmapped bullet glyphs are turned into bullets
    assert "• Built a PyTorch recommendation model" in text


def test_extracts_docx_text(sample_docx):
    text, kind = extract_text(SimpleUploadedFile("cv.docx", sample_docx))
    assert kind == "docx"
    assert "Kubernetes" in text


def test_file_name_and_content_type_are_ignored(sample_pdf):
    # A PDF renamed to .docx with a bogus content type is still read as a PDF...
    text, kind = extract_text(SimpleUploadedFile("cv.docx", sample_pdf, content_type="image/png"))
    assert kind == "pdf"
    # ...and a text file named .pdf is rejected.
    with pytest.raises(BadUpload):
        extract_text(SimpleUploadedFile("cv.pdf", b"just text" * 100, content_type="application/pdf"))


def test_rejects_oversized_upload(settings, sample_pdf):
    settings.MAX_UPLOAD_BYTES = 1024 * 1024
    with pytest.raises(BadUpload, match="1 MB"):
        extract_text(SimpleUploadedFile("cv.pdf", sample_pdf + b"\0" * settings.MAX_UPLOAD_BYTES))


def test_rejects_nearly_empty_document():
    document = docx.Document()
    document.add_paragraph("Hi")
    buffer = io.BytesIO()
    document.save(buffer)
    with pytest.raises(BadUpload, match="almost no text"):
        extract_text(SimpleUploadedFile("cv.docx", buffer.getvalue()))


def test_rejects_damaged_pdf():
    with pytest.raises(BadUpload):
        extract_text(SimpleUploadedFile("cv.pdf", b"%PDF-1.4\n garbage " * 50))


def test_clean_collapses_whitespace():
    assert clean("a  \t b\r\n\n\n\nc\x00") == "a b\n\nc"

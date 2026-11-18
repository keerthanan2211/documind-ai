from tests.conftest import make_pdf


def upload(client, data, name="manual.pdf"):
    return client.post("/api/documents", files={"file": (name, data, "application/pdf")})


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_upload_processes_pdf_into_searchable_chunks(client, sample_pdf):
    res = upload(client, sample_pdf)
    assert res.status_code == 202
    assert res.json()["status"] == "processing"

    # TestClient runs background tasks before returning, so processing has finished
    doc = client.get(f"/api/documents/{res.json()['id']}").json()
    assert doc["status"] == "ready"
    assert doc["page_count"] == 3
    assert doc["chunk_count"] >= 3


def test_ask_returns_answer_with_page_citations(client, sample_pdf, fake_ai):
    doc_id = upload(client, sample_pdf).json()["id"]
    res = client.post(f"/api/documents/{doc_id}/ask", json={"question": "How long does the warranty last?"})
    assert res.status_code == 200

    answer = res.json()["answer"]
    assert "[1]" in answer["content"]
    # The most similar passage (the warranty page) is source [1]
    assert answer["sources"][0]["page"] == 2
    assert "24 months" in answer["sources"][0]["excerpt"]
    assert "page 2" in fake_ai.prompts[-1]

    history = client.get(f"/api/documents/{doc_id}/messages").json()
    assert [m["role"] for m in history] == ["user", "assistant"]


def test_unrelated_question_does_not_call_the_model(client, sample_pdf, fake_ai):
    doc_id = upload(client, sample_pdf).json()["id"]
    res = client.post(f"/api/documents/{doc_id}/ask", json={"question": "zebra quantum volcano"})
    assert res.json()["answer"]["content"] == "I couldn't find that in this document."
    assert fake_ai.prompts == []


def test_rejects_non_pdf(client):
    res = upload(client, b"hello world", name="notes.txt")
    assert res.status_code == 415


def test_scanned_pdf_without_text_fails_with_a_clear_reason(client):
    blank = make_pdf([""])
    doc = client.get(f"/api/documents/{upload(client, blank).json()['id']}").json()
    assert doc["status"] == "failed"
    assert "OCR" in doc["error"]


def test_cannot_ask_before_processing_finishes(client, sample_pdf):
    from app.db import SessionLocal
    from app.models import Document

    doc_id = upload(client, sample_pdf).json()["id"]
    with SessionLocal() as db:
        db.get(Document, doc_id).status = "processing"
        db.commit()
    res = client.post(f"/api/documents/{doc_id}/ask", json={"question": "warranty?"})
    assert res.status_code == 409


def test_delete_removes_document_and_its_data(client, sample_pdf):
    doc_id = upload(client, sample_pdf).json()["id"]
    client.post(f"/api/documents/{doc_id}/ask", json={"question": "warranty length?"})
    assert client.delete(f"/api/documents/{doc_id}").status_code == 204
    assert client.get(f"/api/documents/{doc_id}").status_code == 404
    assert client.get("/api/documents").json() == []


def test_validation_errors(client, sample_pdf):
    doc_id = upload(client, sample_pdf).json()["id"]
    assert client.post(f"/api/documents/{doc_id}/ask", json={"question": "?"}).status_code == 422
    assert client.get("/api/documents/not-a-uuid").status_code == 422

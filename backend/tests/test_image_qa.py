import io
import sys
import os

# Make sure the backend package is importable during tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_image_qa_multimodal_success(monkeypatch):
    # patch the multimodal analyzer
    def fake_analyze(b, q):
        return ("A dog wearing a blue collar sitting on grass", None)

    from backend.brain import local_multimodal as lm
    monkeypatch.setattr(lm, "is_available", lambda: True)
    monkeypatch.setattr(lm, "analyze_image_with_local_llm", fake_analyze)

    # send a fake image file and question
    files = {"file": ("dog.jpg", io.BytesIO(b"fakeimagebytes"), "image/jpeg")}
    data = {"question": "What color is the collar?", "chat_id": None}

    res = client.post("/image_qa", files=files, data=data)

    # Assert
    assert res.status_code == 200
    payload = res.json()
    assert "response" in payload
    assert payload["response"] != ""
    assert payload["chat_id"] is not None
    assert "collar" in payload["response"].lower() or "blue" in payload["response"].lower()


def test_image_qa_multimodal_unavailable(monkeypatch):
    # Simulate multimodal LLM returning None
    from backend.brain import local_multimodal as lm
    monkeypatch.setattr(lm, "is_available", lambda: False)

    files = {"file": ("dog.jpg", io.BytesIO(b"fakeimagebytes"), "image/jpeg")}
    data = {"question": "Count objects", "chat_id": None}

    res = client.post("/image_qa", files=files, data=data)

    assert res.status_code == 200
    payload = res.json()
    assert "unable to analyze this image" in payload["response"].lower()

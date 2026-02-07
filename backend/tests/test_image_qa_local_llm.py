import io
from fastapi.testclient import TestClient
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.main import app

client = TestClient(app)


def test_image_qa_uses_local_llm(monkeypatch):
    # simulate local multimodal LLM available
    from backend.brain import local_multimodal as lm

    monkeypatch.setattr(lm, "is_available", lambda: True)
    def fake_analyze(b, q):
        return ("The collar is blue and there are 1 dog.", None)
    monkeypatch.setattr(lm, "analyze_image_with_local_llm", fake_analyze)

    # Act
    files = {"file": ("dog.jpg", io.BytesIO(b"fakeimagebytes"), "image/jpeg")}
    data = {"question": "What color is the collar?", "chat_id": None}
    res = client.post("/image_qa", files=files, data=data)

    # Assert
    assert res.status_code == 200
    payload = res.json()
    assert "blue" in payload["response"].lower()
    assert payload["chat_id"] is not None

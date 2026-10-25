import json

import httpx

from rag.openrouter import OpenRouterClient
from shared.contracts import FREE_MODEL


def test_chat_request_uses_authorized_free_model_and_zero_price():
    calls = []

    def reply(request):
        calls.append(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"message": {"content": "Respuesta fundada."}}]})

    client = OpenRouterClient(api_key="test-key", model=FREE_MODEL, client=httpx.Client(transport=httpx.MockTransport(reply)))
    assert client.answer_from_news("¿Qué ocurrió?", "Título y cuerpo de prueba") == "Respuesta fundada."
    assert calls[0]["model"] == FREE_MODEL
    assert calls[0]["provider"]["max_price"] == {"prompt": 0, "completion": 0}
    assert calls[0]["reasoning"] == {"enabled": False}

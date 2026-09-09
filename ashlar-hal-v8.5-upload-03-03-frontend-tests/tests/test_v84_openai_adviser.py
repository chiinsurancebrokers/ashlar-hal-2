from pathlib import Path

from backend.app.core.config import Settings
from backend.app.services.openai_adviser import _extract_output_text, _request_body


def test_openai_chat_defaults_to_terra():
    s=Settings()
    assert s.openai_chat_model=="gpt-5.6-terra"


def test_responses_request_is_stateless_and_json_capable():
    body=_request_body(
        instructions="system",
        message="hello",
        history=[{"role":"assistant","content":"Hi"}],
        json_mode=True,
        max_output_tokens=321,
    )
    assert body["store"] is False
    assert body["model"]=="gpt-5.6-terra"
    assert body["max_output_tokens"]==321
    assert body["text"]["format"]["type"]=="json_object"
    assert body["input"][-1]=={"role":"user","content":"hello"}


def test_extract_output_text_from_raw_responses_shape():
    payload={
        "output":[
            {
                "type":"message",
                "content":[
                    {"type":"output_text","text":'{"reply":"hello"}'}
                ],
            }
        ]
    }
    assert _extract_output_text(payload)=='{"reply":"hello"}'


def test_no_anthropic_runtime_call_remains():
    chat=(Path(__file__).resolve().parents[1]/"backend/app/services/chat.py").read_text(encoding="utf-8")
    assert "api.anthropic.com" not in chat
    assert "openai_adviser_response" in chat


def test_health_reports_openai_conversation_engine():
    main=(Path(__file__).resolve().parents[1]/"backend/app/main.py").read_text(encoding="utf-8")
    assert '"version":"8.5.0"' in main
    assert '"conversational_ai":"openai_responses_api"' in main
    assert '"openai_response_storage":"disabled"' in main

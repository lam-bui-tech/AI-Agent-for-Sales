import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "sales_api"))

from main import app
from llm import (
    get_dion_base_url,
    get_dion_api_key,
    get_dion_model,
    call_dion_chat_completions,
    generate_sales_reply,
    execute_intent_tools,
    SESSION_CONVERSATIONS,
)
from db import init_db

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

@pytest.fixture
def client():
    return TestClient(app)

def test_dion_llm_config():
    """Kiểm tra cấu hình biến môi trường Dion AI"""
    base_url = get_dion_base_url()
    model = get_dion_model()
    api_key = get_dion_api_key()

    assert base_url == "https://ai.dion.vn/api/v1"
    assert model == "balanced"
    if api_key:
        assert len(api_key) > 10

def test_get_llm_status_endpoint(client):
    """Kiểm tra endpoint GET /api/llm/status và đảm bảo không lộ API key"""
    response = client.get("/api/llm/status")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "ready"
    assert data["provider"] == "dion_ai"
    assert data["base_url"] == "https://ai.dion.vn/api/v1"
    assert data["model"] == "balanced"
    assert data["has_api_key"] is True
    # Đảm bảo key bí mật KHÔNG bị lộ nguyên văn trong response
    api_key = get_dion_api_key()
    if api_key:
        assert api_key not in str(data)

def test_call_dion_chat_completions_mock_success():
    """Kiểm tra gọi hàm call_dion_chat_completions khi API trả về 200 thành công"""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "id": "chatcmpl-test-123",
        "model": "gemini-3.7-flash",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Chào bạn, mình là Trợ lý Shop của ThueDo.net.\n\n**Shop mình hiện có mấy chi nhánh ạ?**"
                }
            }
        ]
    }

    with patch("requests.post", return_value=mock_resp) as mock_post:
        messages = [{"role": "user", "content": "Xin chào"}]
        reply = call_dion_chat_completions(messages)

        assert reply is not None
        assert "Trợ lý Shop" in reply
        assert mock_post.called
        args, kwargs = mock_post.call_args
        assert args[0] == "https://ai.dion.vn/api/v1/chat/completions"
        assert kwargs["json"]["model"] == "balanced"
        assert "Authorization" in kwargs["headers"]
        assert kwargs["headers"]["Authorization"].startswith("Bearer af_")

def test_call_dion_chat_completions_mock_failure():
    """Kiểm tra xử lý lỗi khi API trả về 500 hoặc mất kết nối mạng"""
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "Internal Server Error"

    with patch("requests.post", return_value=mock_resp):
        messages = [{"role": "user", "content": "Xin chào"}]
        reply = call_dion_chat_completions(messages)
        assert reply is None

def test_generate_sales_reply_with_mock_llm():
    """Kiểm tra luồng generate_sales_reply khi LLM phản hồi thành công"""
    mock_llm_text = (
        "Dạ ThueDo.net có 3 gói cước linh hoạt:\n\n"
        "- Gói Starter (189.000đ/tháng): 1 chi nhánh, 1 kho, quản lý thuê - cọc - trả cơ bản.\n\n"
        "- Gói Pro (339.000đ/tháng): 3 chi nhánh, 3 kho, in hợp đồng QR và mobile app.\n\n"
        "**Shop mình hiện có mấy chi nhánh để mình tư vấn gói phù hợp nhất ạ?**"
    )

    with patch("llm.call_dion_chat_completions", return_value=mock_llm_text):
        session_id = "test_session_mock_1"
        res = generate_sales_reply("Tư vấn giá gói giúp mình", session_id=session_id)

        assert res["source"] == "dion-llm"
        assert res["reply"] == mock_llm_text
        assert session_id in SESSION_CONVERSATIONS
        # Lịch sử hội thoại đã lưu câu hỏi và câu trả lời
        history = SESSION_CONVERSATIONS[session_id]
        assert len(history) >= 2
        assert history[-1]["content"] == mock_llm_text

def test_generate_sales_reply_fallback_compliance():
    """Kiểm tra fallback khi API LLM timeout: tuân thủ quy chuẩn không bảng markdown và bôi đen câu chốt"""
    with patch("llm.call_dion_chat_completions", return_value=None):
        res = generate_sales_reply("Báo giá phần mềm giúp mình", session_id="test_fallback_session")

        assert res["source"] == "simulation-engine"
        assert res["reply"] is not None
        # Không được chứa bảng kẻ cột markdown
        assert "|---|" not in res["reply"]
        assert "| --- |" not in res["reply"]
        # Phải kết thúc bằng câu hỏi hoặc gợi mở in đậm
        assert res["reply"].rstrip().endswith("**")

def test_execute_intent_tools():
    """Kiểm tra bộ nhận diện intent kích hoạt tool nghiệp vụ"""
    # 1. Khách hỏi chiết khấu / giảm giá
    execute_intent_tools("Shop có bớt giá khi mua 2 năm không?", session_id="sess_discount")
    from handoffs import get_all_handoffs
    handoffs = get_all_handoffs()
    assert any(h.get("reason") == "discount_request" for h in handoffs)

    # 2. Khách để lại SĐT dùng thử
    execute_intent_tools("Mình muốn đăng ký dùng thử SĐT 0912345678", session_id="sess_trial")
    from leads import get_all_leads
    leads = get_all_leads()
    assert any(l.get("phone") == "0912345678" for l in leads)

def test_api_chat_endpoint_dion(client):
    """Kiểm tra endpoint POST /api/chat gọi tích hợp Dion LLM thông qua TestClient"""
    mock_llm_reply = "Dạ chào bạn! **Shop mình hiện có mấy chi nhánh và đang kinh doanh dòng đồ nào ạ?**"
    
    with patch("llm.call_dion_chat_completions", return_value=mock_llm_reply):
        response = client.post("/api/chat", json={
            "message": "Xin chào shop",
            "channel": "web",
            "user_id": "test_web_user"
        })
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        assert "source" in data
        assert "tool_calls" in data

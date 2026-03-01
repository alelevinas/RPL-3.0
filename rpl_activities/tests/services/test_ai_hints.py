import pytest
from unittest.mock import patch, MagicMock
from rpl_activities.src.services.ai_hints import AIHintsService

def test_ai_hints_service_openai_success():
    with patch("rpl_activities.src.services.ai_hints.OpenAI") as mock_openai:
        # Setup mock
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.return_value.choices[0].message.content = "Try checking your loop condition."

        with patch.dict("os.environ", {"OPENAI_API_KEY": "fake_key"}):
            service = AIHintsService()
            hint = service.generate_hint("c_std11", "Error: infinite loop", "Write a for loop.")
            
            assert hint == "Try checking your loop condition."
            mock_client.chat.completions.create.assert_called_once()

def test_ai_hints_service_ollama_success():
    with patch.dict("os.environ", {"OLLAMA_URL": "http://localhost:11434"}):
        service = AIHintsService()
        
        with patch("httpx.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"response": "Check your indentation."}
            mock_post.return_value = mock_response

            hint = service.generate_hint("python_3.12", "IndentationError", "Print hello world.")
            
            assert hint == "Check your indentation."
            mock_post.assert_called_once()

def test_ai_hints_service_disabled():
    with patch.dict("os.environ", {}, clear=True):
        # Ensure no keys are present
        with patch("os.getenv", return_value=None):
            service = AIHintsService()
            hint = service.generate_hint("c_std11", "error", "desc")
            assert hint is None

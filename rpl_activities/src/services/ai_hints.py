import os
import logging
from typing import Optional
from openai import OpenAI
import httpx

class AIHintsService:
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.ollama_url = os.getenv("OLLAMA_URL")  # e.g., http://localhost:11434
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3")

        if self.openai_key:
            self.client = OpenAI(api_key=self.openai_key)
            logging.info("AIHintsService: Using OpenAI API")
        elif self.ollama_url:
            self.client = None
            logging.info(f"AIHintsService: Using Ollama at {self.ollama_url}")
        else:
            logging.warning("Neither OPENAI_API_KEY nor OLLAMA_URL set. AI Hints will be disabled.")
            self.client = None

    def generate_hint(self, language: str, error_output: str, activity_description: str) -> Optional[str]:
        prompt = f"""
You are an expert programming teacher. A student is working on an activity and their code failed.
Provide a short, helpful hint (max 3 sentences) to help them debug the error.
DO NOT provide the corrected code. Focus on explaining what the error means in the context of the activity.

Activity Description:
{activity_description}

Language: {language}

Error Output:
{error_output}

Hint:
"""
        if self.client:
            return self._generate_openai_hint(prompt)
        elif self.ollama_url:
            return self._generate_ollama_hint(prompt)
        return None

    def _generate_openai_hint(self, prompt: str) -> Optional[str]:
        try:
            response = self.client.chat.completions.create(
                model=self.openai_model,
                messages=[
                    {"role": "system", "content": "You are a helpful programming tutor."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logging.error(f"Error generating OpenAI hint: {e}")
            return None

    def _generate_ollama_hint(self, prompt: str) -> Optional[str]:
        try:
            response = httpx.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": 150, "temperature": 0.7}
                },
                timeout=30.0
            )
            if response.status_code == 200:
                return response.json().get("response", "").strip()
            return None
        except Exception as e:
            logging.error(f"Error generating Ollama hint: {e}")
            return None

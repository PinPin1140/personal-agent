"""OpenAI provider for API key-based authentication."""
import os
from typing import Dict, Any
from ..models import ModelProvider


class OpenAIProvider(ModelProvider):
    """OpenAI provider using API key authentication."""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self._client = None

        if self.api_key:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except ImportError:
                # Fallback if openai library not installed
                self._client = None
        else:
            self._client = None

    def generate(
        self,
        prompt: str,
        context: Dict[str, Any] = {}
    ) -> str:
        """Generate response using OpenAI API or stub."""
        if not self._client or not self.api_key:
            return f"[OPENAI STUB] Processed: {prompt[:50]}{'...' if len(prompt) > 50 else ''}"

        try:
            response = self._client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"[OPENAI ERROR] {str(e)}"

    @property
    def supports_streaming(self) -> bool:
        return True

    @property
    def auth_type(self) -> str:
        return "APIKEY"
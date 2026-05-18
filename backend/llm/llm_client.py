import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import os
from typing import Optional, List, Dict, Any
from backend.ingestion.config import config


class LLMClient:
    def __init__(self, model: Optional[str] = None):
        self.model = model or config.LLM_MODEL
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.use_fallback = not self.api_key

        if self.use_fallback:
            print("WARNING: No OPENROUTER_API_KEY found. Using fallback mode.")
        else:
            from openai import OpenAI
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.api_key
            )

    def generate(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> str:
        if self.use_fallback:
            return self._fallback_generate(prompt, system_message)

        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"

    def _fallback_generate(self, prompt: str, system_message: Optional[str] = None) -> str:
        return """This is a fallback response. To enable AI-powered responses, please set the OPENROUTER_API_KEY environment variable.

For demonstration, the system will return relevant legal context from the documents instead.

To get an API key:
1. Visit https://openrouter.ai/
2. Create an account
3. Generate an API key
4. Set it in your .env file as OPENROUTER_API_KEY=your_key_here

The RAG retrieval system is fully functional - you can query the vector database directly."""

    def generate_streaming(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 2000
    ):
        if self.use_fallback:
            yield self._fallback_generate(prompt, system_message)
            return

        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"Error: {str(e)}"


llm_client = LLMClient()
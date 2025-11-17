"""OpenAI client for embeddings and grounded answer generation."""

from __future__ import annotations

import logging
from typing import Iterable, List

from openai import OpenAI

from ..config import get_settings

LOGGER = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are a compliance-focused assistant that answers factual mutual fund questions.
Rules:
1. Only use the supplied context excerpts.
2. Respond in <=3 sentences, clear declarative tone.
3. Append a single citation token '[CITATION]' at the end of the answer.
4. If the context does not contain the answer, say you couldn't find it.
5. Never provide investment or portfolio advice; redirect users to SEBI-registered advisers if they ask.
""".strip()


class OpenAIClient:
    def __init__(self) -> None:
        self._settings = get_settings()
        if not self._settings.openai.api_key:
            raise ValueError("OPENAI_API_KEY is required")
        self._client = OpenAI(api_key=self._settings.openai.api_key)
        self._embed_model = self._settings.openai.embed_model
        self._chat_model = self._settings.openai.chat_model

    def embed(self, text: str) -> List[float]:
        response = self._client.embeddings.create(model=self._embed_model, input=text)
        return response.data[0].embedding

    def answer(self, question: str, contexts: Iterable[str]) -> str:
        context_blob = "\n\n".join(contexts)
        user_prompt = f"Context:\n{context_blob}\n\nQuestion: {question}\nAnswer:"
        completion = self._client.chat.completions.create(
            model=self._chat_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=300,
        )
        text = completion.choices[0].message.content.strip()
        if "[CITATION]" not in text:
            text = f"{text} [CITATION]"
        return text

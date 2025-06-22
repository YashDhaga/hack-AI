# translator_tool_spec.py
from llama_index.core.tools.tool_spec.base import BaseToolSpec
from constants import LLMConfig

class SarvamTranslatorToolSpec(BaseToolSpec):
    """
    SarvamTranslatorToolSpec
    -----------------------
    • Exposes one function – `translate`.
    • Translates any regional-language text to English via Sarvam LLM.
    """

    # Tell LlamaIndex which methods are tools
    spec_functions = ["translate"]

    def __init__(self, sarvam_llm):
        self.sarvam_llm = sarvam_llm

    async def translate(self, text: str) -> str:
        """Translate Indian regional-language text to English."""
        prompt = f"Translate this to English:\n{text}"
        response = await self.sarvam_llm.chat.completions.create(
            model=LLMConfig.MODEL,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content.strip()
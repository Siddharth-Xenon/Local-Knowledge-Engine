"""Generation Service for Node 2."""

from pathlib import Path
from typing import Any

from app.generation.prompts.engine import JinjaPromptEngine
from app.inference.client import InferenceClient, inference_client


class GenerationService:
    """Service for handling LLM generation logic."""

    def __init__(
        self,
        prompt_engine: JinjaPromptEngine | None = None,
        client: InferenceClient | None = None,
    ) -> None:
        # Default initialization
        # templates are at app/generation/prompts/templates
        if prompt_engine is None:
            # Resolve path relative to this file:
            # app/services/generation_service.py -> app/generation/prompts/templates
            base_dir = (
                Path(__file__).resolve().parent.parent
                / "generation"
                / "prompts"
                / "templates"
            )
            self.prompt_engine = JinjaPromptEngine(base_dir)
        else:
            self.prompt_engine = prompt_engine

        self.client = client or inference_client

    async def generate_from_template(
        self,
        prompt_key: str,
        version: str,
        variables: dict[str, Any],
        model: str | None = None,
    ) -> str:
        """
        Generate response from a template.

        Args:
            prompt_key: Template family (e.g. 'rag')
            version: Template version (e.g. '1.0.0')
            variables: Variables for template rendering
            model: Optional model override

        Returns:
            The raw text response from the LLM
        """
        # 1. Render Prompt
        final_prompt = self.prompt_engine.render(
            prompt_key=prompt_key,
            version=version,
            variables=variables,
        )

        # 2. Call Inference (Node 1)
        # Note: We send the full rendered prompt string.
        # Node 1 will act as a pure inference engine.
        response = await self.client.generate(prompt=final_prompt, model=model)

        return response

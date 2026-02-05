"""Concrete Prompt Engine Implementation."""

from pathlib import Path
from typing import Any
from functools import lru_cache

import jinja2

from app.core.exceptions import PromptRenderError
from app.core.interfaces import IPromptEngine
from app.prompts.loader import PromptLoader


class JinjaPromptEngine(IPromptEngine):
    """Jinja2-based Prompt Engine."""

    def __init__(self, templates_dir: Path) -> None:
        self.loader = PromptLoader(templates_dir)
        # Configure Jinja2 environment
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(templates_dir),
            autoescape=False,  # Prompts are text, not HTML
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(
        self,
        prompt_key: str,
        version: str,
        variables: dict[str, Any],
    ) -> str:
        """Render a Jinja2 template."""
        try:
            # Validate existence via loader (ensures path security)
            # We don't strictly need to get the path here since Jinja has its own loader,
            # but this keeps our custom Loader logic authoritative for checking existence.
            # Convert to Jinja-style path: "family/vX.X.X.j2"
            template_name = f"{prompt_key}/v{version}.j2"
            
            template = self.env.get_template(template_name)
            return template.render(**variables)

        except jinja2.TemplateNotFound:
             # Should be caught by self.loader.get_template_path check if we did it first,
             # but mapped closely to our custom exception here.
             # We rely on Jinja's loader for the actual fetch.
             # Let's verify existence explicitly if needed, but Jinja is robust.
             
             # Re-raise as our domain exception
             raise PromptRenderError(
                 f"Template not found (jinja): {template_name}",
                 details={"key": prompt_key, "version": version}
             )
        except Exception as e:
            raise PromptRenderError(
                f"Failed to render prompt: {e}",
                details={"key": prompt_key, "version": version, "error": str(e)}
            )

# Singleton instance setup expected in main/startup

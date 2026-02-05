"""Prompt Loader: Filesystem logic."""

from pathlib import Path

from app.core.exceptions import PromptNotFoundError


class PromptLoader:
    """Loads prompt templates from the filesystem."""

    def __init__(self, templates_dir: Path) -> None:
        self.templates_dir = templates_dir

    def get_template_path(self, prompt_key: str, version: str) -> Path:
        """
        Resolve the file path for a prompt template.
        Structure: templates/{prompt_key}/v{version}.j2
        """
        # Security: Prevent traversal
        if ".." in prompt_key or ".." in version:
            raise ValueError("Invalid prompt key or version")

        filename = f"v{version}.j2"
        path = self.templates_dir / prompt_key / filename

        if not path.exists():
            raise PromptNotFoundError(
                f"Prompt template not found: {prompt_key} v{version}",
                details={"path": str(path)},
            )
        
        return path

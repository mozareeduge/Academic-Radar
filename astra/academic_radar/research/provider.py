from typing import Protocol, Optional


class LLMProvider(Protocol):
    """Protocol for LLM providers that return completions."""

    def complete(self, messages: list[dict], *, schema_name: str) -> str:
        """Complete the given messages for a specific schema.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            schema_name: Name of the schema being used.

        Returns:
            The completion text.
        """
        ...


class MockProvider:
    """Mock LLM provider that returns scripted responses."""

    def __init__(self, script: dict[str, str]):
        """Initialize with a script dict mapping schema_name -> response text.

        Args:
            script: Dict mapping schema names to response strings.
        """
        self.script = script

    def complete(self, messages: list[dict], *, schema_name: str) -> str:
        """Return the scripted response for schema_name.

        Raises KeyError if schema_name is not in the script.
        """
        return self.script[schema_name]


class LiteLLMProvider:
    """LiteLLM-based provider that delegates to astra.core.llm."""

    def __init__(self, model: str, complete_fn: Optional[callable] = None):
        """Initialize with a model ID and optional complete function.

        Args:
            model: The model ID (e.g., 'openai/gpt-4o-mini').
            complete_fn: Optional function to call for completions.
                If None, will try to import and use astra.core.llm.LLMRouter.complete.

        Raises NotImplementedError if neither complete_fn nor astra.core.llm is available.
        """
        self.model = model
        self.complete_fn = complete_fn

        if self.complete_fn is None:
            try:
                from astra.core.llm import LLMRouter
                self._router = LLMRouter(default_model=model)
                self.complete_fn = self._router.complete
            except (ImportError, AttributeError):
                raise NotImplementedError(
                    "LiteLLMProvider requires either complete_fn parameter "
                    "or astra.core.llm.LLMRouter to be available"
                )

    def complete(self, messages: list[dict], *, schema_name: str) -> str:
        """Complete using the LiteLLM router or provided function."""
        # Build prompt from messages
        prompt = "\n".join(
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in messages
        )
        return self.complete_fn(prompt)

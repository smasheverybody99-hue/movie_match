"""The LLM provider, chosen by `LLM_PROVIDER` (docs/decisions/0006-provider-interface.md).

To add a provider: write app/providers/<name>.py with a class that satisfies
`base.Provider`, and add one line to PROVIDERS below. Its API key goes in app/config.py
like every other setting.
"""

from collections.abc import Callable

from app.config import Settings
from app.providers.base import Provider
from app.providers.gemini import GeminiProvider

PROVIDERS: dict[str, Callable[[Settings], Provider]] = {
    "gemini": GeminiProvider,
}


class UnknownProvider(ValueError):
    pass


def get_provider(settings: Settings) -> Provider:
    try:
        factory = PROVIDERS[settings.llm_provider]
    except KeyError:
        known = ", ".join(sorted(PROVIDERS))
        raise UnknownProvider(
            f"LLM_PROVIDER={settings.llm_provider!r} is not a known provider (known: {known})"
        ) from None
    return factory(settings)

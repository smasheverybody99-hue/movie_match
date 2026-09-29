"""One cost line per run, the same for every provider.

    run=traits provider=gemini model=... requests=50 input_tokens=21000 output_tokens=12500
    usd=0.0188 tokens=reported pricing="..."

Written to the `app.cost` logger (and so to stdout of the pipeline commands and the API
process). A run is a trait batch collected, an embedding run, or one explanation.
"""

import logging

from app.providers.base import Pricing, Usage

log = logging.getLogger("app.cost")


def cost_line(run: str, provider: str, model: str, usage: Usage, pricing: Pricing) -> str:
    return (
        f"run={run} provider={provider} model={model} requests={usage.requests} "
        f"input_tokens={usage.input_tokens} output_tokens={usage.output_tokens} "
        f"usd={pricing.usd(usage):.4f} tokens={'estimated' if usage.estimated else 'reported'} "
        f'pricing="{pricing.source}"'
    )


def record(run: str, provider: str, model: str, usage: Usage, pricing: Pricing) -> str:
    """Log the run's usage and estimated cost; returns the line for a CLI to print too."""
    line = cost_line(run, provider, model, usage, pricing)
    log.info(line)
    return line


def configure() -> None:
    """Make `app.cost` lines visible. Idempotent; leaves an existing setup alone."""
    if log.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s cost %(message)s"))
    log.addHandler(handler)
    log.setLevel(logging.INFO)
    log.propagate = False

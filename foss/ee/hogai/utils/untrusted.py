"""Helpers that mark user-provided text before it enters an LLM prompt.

The FOSS build has no built-in agent, but products still call these when an operator wires up their
own model provider, so they do the same job: wrap data in an explicit boundary and defuse markup.
"""

import html


def neutralize_markup(text: str) -> str:
    return html.escape(text, quote=False)


def as_untrusted_data(text: str, label: str = "untrusted_data") -> str:
    return f"<{label}>\n{neutralize_markup(text)}\n</{label}>"

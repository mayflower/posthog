from typing import Any

from ee._foss import unavailable_function


class PydanticOutputParserException(ValueError):
    def __init__(self, llm_output: str = "", validation_message: str = "", *args: Any) -> None:
        super().__init__(validation_message or llm_output, *args)
        self.llm_output = llm_output
        self.validation_message = validation_message


parse_pydantic_structured_output = unavailable_function("parse_pydantic_structured_output", "PostHog AI")

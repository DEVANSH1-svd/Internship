from llm.schema import EnrichResponse, Category, QualityFlag


def get_stub_response() -> EnrichResponse:
    """A hardcoded, schema-valid response used when LLM_STUB=1.
    Lets the endpoint be built and tested with zero model calls."""
    return EnrichResponse(
        category=Category.fiction,
        summary="A stub response used for development without calling the model.",
        quality_flags=[QualityFlag.none],
        confidence=0.99
    )

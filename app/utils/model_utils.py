import os
from langchain.chat_models import init_chat_model


def create_chat_model(temperature: float = 0.2, **kwargs):
    """Return a chat model instance.

    Selection logic:
    1. If the environment variable ``LLM_MODEL`` is set, use that value verbatim.
       - If the string contains a colon (``provider:model``), it is passed as ``model``
         to ``init_chat_model`` and the provider prefix is respected.
       - Otherwise the value is assumed to be an OpenAI model name and
         ``model_provider="openai"`` is added automatically.
    2. If ``LLM_MODEL`` is not set, the code attempts to create an OpenAI
       ``gpt-4o-mini`` instance.  If this call throws an exception (e.g. due
       to a missing or invalid OpenAI key), the function falls back to the
       Google Gemini Flash model ``google_genai:gemini-flash-latest``.
    3. Any additional ``kwargs`` are forwarded to ``init_chat_model`` (e.g.
       ``temperature``).

    This allows the application to work with either provider transparently
    and makes switching models as simple as setting a single environment
    variable.
    """

    # Helper to instantiate using the given model string with optional provider
    def _make(model_str: str):
        if ":" in model_str:
            # provider specified (e.g. "google_genai:gemini-flash-latest")
            return init_chat_model(model=model_str, **kwargs)
        else:
            # assume OpenAI if no provider prefix
            return init_chat_model(model=model_str, model_provider="openai", **kwargs)

    # step 1: environment override
    env_model = os.environ.get("LLM_MODEL")
    if env_model:
        try:
            m = _make(env_model)
            print(f"[model_utils] using model from LLM_MODEL env: {env_model}")
            return m
        except Exception as e:
            print(f"[model_utils] warning: failed to init env model {env_model}, will try defaults: {e}")
            # fall back to normal flow
            pass

    # step 2: try default gpt-4o-mini
    try:
        model = _make("gpt-4o-mini")
        print("[model_utils] using OpenAI gpt-4o-mini")
        return model
    except Exception as e:
        # if openai failed, fall back to Gemini
        print("[model_utils] failed to initialize gpt-4o-mini, falling back to Gemini:", e)
        model = _make("google_genai:gemini-flash-latest")
        print("[model_utils] using Google Gemini Flash")
        return model

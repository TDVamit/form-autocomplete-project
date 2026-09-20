# Insurance Form Assistant

An experimental Streamlit application that guides a user through a nested insurance form using conversational OpenAI agents, deterministic field updates, validation, suggestions, and a local JSON cache.

## Capabilities

- Walks through a large insurance schema covering insured details, addresses, vehicles, drivers, claims, and related questionnaire data.
- Extracts user intent and converts replies into structured updates against the form state.
- Uses tool calls for field lookup and mutation rather than letting the model edit the schema directly.
- Validates dates and values, suggests enum options and previously entered values, and displays live processing logs in the UI.
- Tracks token usage and caches completed interactions in `cache.json`.

## Architecture

```text
Streamlit UI (frontend.py)
        -> chat_pipeline (main.py)
        -> language / JSON / validation / reply agents
        -> get_field + update_field tools
        -> in-memory session state + cache.json
```

The UI creates a per-session `Form` copy. `main.py` also provides a terminal loop for direct experimentation, while `frontend.py` is the intended interactive entry point.

## Technology

Python 3.13+, Streamlit, OpenAI Python SDK, OpenAI Agents SDK, Pydantic, PyJWT, `nest-asyncio`, and `uv`-compatible packaging. Dependencies are declared in [`pyproject.toml`](pyproject.toml) and resolved in [`uv.lock`](uv.lock).

## Setup and usage

1. Install Python 3.13 or newer and create an isolated environment.
2. Install dependencies, for example with `uv`:

   ```bash
   uv sync
   ```

3. Export an OpenAI API key:

   ```bash
   export OPENAI_API_KEY="<your-api-key>"
   ```

4. Start the UI:

   ```bash
   streamlit run frontend.py
   ```

5. Open the local URL printed by Streamlit and use **Start** to begin an intake session.

For the terminal prototype, run `python main.py` after setting the same environment variable. The app writes `cache.json`, `form_autocomplete.log`, and potentially `log_errors.txt`; treat those files as sensitive because form data may be included.

## Configuration and data handling

The OpenAI model name is currently defined in source (`gpt-4.1-mini`). There is no external database, authentication layer, deployment configuration, or production secrets manager in this repository. Do not enter real personally identifiable information into the prototype, and do not commit API keys, logs, cache files, or customer data.

## Current status

**Experimental prototype / portfolio demonstration.** The conversational flow and schema-driven update path are implemented, but there are no automated tests, formal privacy controls, schema migrations, or verified hosted demo. The bundled form schema contains sensitive insurance fields, including SSN, so production use would require threat modeling, redaction, access controls, retention rules, and independent validation.

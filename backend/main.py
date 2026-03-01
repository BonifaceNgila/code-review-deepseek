from fastapi import FastAPI, Form
import requests
import os
import logging

app = FastAPI()
logger = logging.getLogger("backend")


def _call_upstream(prompt: str, model: str):
    """Call the upstream generation API with given model.

    Returns a tuple (review_text_or_None, error_message_or_None, response_obj_or_None).
    """
    try:
        r = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=10,
        )
    except requests.RequestException as exc:
        return None, f"Upstream request failed: {exc}", None

    if r.status_code != 200:
        return None, f"Upstream returned status {r.status_code}: {r.text[:500]}", r

    try:
        result = r.json()
    except ValueError:
        return None, f"Invalid JSON from upstream: {r.text[:500]}", r

    if not isinstance(result, dict) or "response" not in result:
        return None, f"Upstream JSON missing 'response' field: {result}", r

    return result["response"].strip(), None, r


@app.post("/review/")
def review_code(code: str = Form(...)):
    prompt = (
        "You are a senior developer. Please review the following code for bugs, "
        "improvements, and optimization tips:\n\n"
        f"{code}"
    )

    # Model configuration: primary model and optional comma-separated alternates
    primary_model = os.environ.get("MODEL_NAME", "deepseek-coder")
    alternates = [m.strip() for m in os.environ.get("ALTERNATE_MODELS", "").split(",") if m.strip()]
    models_to_try = [primary_model] + alternates

    last_error = None
    for model in models_to_try:
        logger.info("Trying upstream model: %s", model)
        review, err, resp = _call_upstream(prompt, model)
        if review:
            return {"review": review}

        last_error = err

        # If upstream returned a 404 indicating the model was not found, try next
        if resp is not None and getattr(resp, "status_code", None) == 404:
            # continue to next model
            continue
        # For other errors, break and return the error
        break

    return {"error": f"All attempts failed. Last error: {last_error}"}

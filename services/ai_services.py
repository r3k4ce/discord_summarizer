"""Wrappers around AI providers used by the bot."""

from __future__ import annotations

import logging
from openai import OpenAI
import google.generativeai as genai

from config import GEMINI_API_KEY, OPENAI_API_KEY, MODEL_BASED_GATING_MODEL

openai_client: OpenAI | None = None
if OPENAI_API_KEY:
    try:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
    except Exception as exc:  # pylint: disable=broad-except
        logging.error("Error initializing OpenAI client: %s", exc)


gemini_model = None
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel("gemini-flash-latest")
    except Exception as exc:  # pylint: disable=broad-except
        logging.error("Error initializing Gemini client: %s", exc)


def get_ai_summary(text: str | None) -> str | None:
    """Summarize the given text via OpenAI."""
    if not text or not openai_client:
        return None

    system_prompt = (
        "Eres un agudo analista politico y economico de la derecha liberal-libertaria," \
        "con un estilo retorico directo y combativo, similar a referentes como javier milei, agustin laje o axel kaisser" \
        "Recibiras el texto completo de una noticia. Tu trabajo es analizarla y redactar un resumen de la misma" \
        "el resumen debe ser redactado desde una perspectiva anti progresista, destacando los aspectos que contradicen o desafian las ideas progresistas." \
        "no te limites a describir los hechos, sino que ofrece una interpretacion critica que resalte las implicaciones politicas y economicas desde tu perspectiva." \
        "destaca las consecuencias negativas de las politicas progresistas mencionadas en la noticia." \
        "utiliza un lenguaje directo, contundente y sin concesiones"
    )
    user_prompt = f"Article:\n{text[:6000]}"

    try:
        response = openai_client.responses.create(
            model="gpt-5-mini",
            instructions=system_prompt,
            input=user_prompt,
            max_output_tokens=256,
        )
        if getattr(response, "output_text", None):
            return response.output_text.strip()

        output_text = None
        if getattr(response, "output", None):
            for out_item in response.output:
                if getattr(out_item, "text", None):
                    output_text = out_item.text
                    break
                if getattr(out_item, "content", None):
                    for content_item in out_item.content:
                        if getattr(content_item, "text", None):
                            output_text = content_item.text
                            break
                    if output_text:
                        break
        if output_text:
            return output_text.strip()
    except Exception as exc:  # pylint: disable=broad-except
        logging.error("Responses API failed: %s", exc)

    try:
        completion = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )
        return completion.choices[0].message.content
    except Exception as exc:  # pylint: disable=broad-except
        logging.error("OpenAI fallback chat completion failed: %s", exc)
        return None


def get_gemini_summary(video_url: str | None) -> str | None:
    """Summarize a YouTube video using Gemini."""
    if not video_url or not gemini_model:
        return None

    prompt_text = (
        "You are an expert video summarizer. Summarize this video for a "
        "Discord chat. Be concise (2-3 sentences) and capture the video's "
        "main points and conclusion. Do not add any preamble like 'This video discusses...'"
    )

    try:
        response = gemini_model.generate_content([prompt_text, video_url])
        return response.text.strip()
    except Exception as exc:  # pylint: disable=broad-except
        logging.error("Gemini summary failed for URL %s: %s", video_url, exc)
        if "RESOURCE_EXHAUSTED" in str(exc):
            return "AI summary failed: The API is busy. Please try again later."
        if "400" in str(exc):
            return (
                "AI summary failed: The video might be private, deleted, or otherwise unavailable."
            )
        return "AI summary failed. See console logs for details."


def is_article_relevant(text: str | None, model: str | None = None) -> bool | None:
    """Return True if the article text is about politics/economy (relevant), False otherwise.

    Returns None on errors or if classification cannot be determined. The function aims to
    instruct the OpenAI Responses API to reply with only 'true' or 'false' (lowercase), which
    we parse into a boolean.
    """
    if not text:
        return None
    if not openai_client:
        logging.warning("OpenAI client not configured; cannot run model-based gating.")
        return None

    model_name = model or MODEL_BASED_GATING_MODEL
    system_prompt = (
        "Eres un clasificador que decide si el texto que se te da trata sobre politica, economia o temas\n"
        "relacionados (impuestos, inflacion, gasto publico, regulacion, etc.).\n"
        "Si el articulo trata de estos temas, responde SOLO con el texto: true\n"
        "Si no trata de estos temas, responde SOLO con el texto: false\n"
        "No añadas explicaciones, formato JSON ni texto adicional. Devuelve exactamente true o false."
    )
    user_prompt = f"Articulo de noticia:\n{text[:8000]}"

    try:
        resp = openai_client.responses.create(
            model=model_name,
            instructions=system_prompt,
            input=user_prompt,
            max_output_tokens=16,
        )
        # Try extracting the textual output
        text_resp = None
        if getattr(resp, "output_text", None):
            text_resp = resp.output_text
        elif getattr(resp, "output", None):
            for item in resp.output:
                if getattr(item, "text", None):
                    text_resp = item.text
                    break
                if getattr(item, "content", None):
                    # content may be a list of pieces
                    for content_item in item.content:
                        t = getattr(content_item, "text", None)
                        if t:
                            text_resp = t
                            break
                    if text_resp:
                        break
        if text_resp:
            norm = text_resp.strip().lower()
            if norm.startswith("true"):
                return True
            if norm.startswith("false"):
                return False
            # If model didn't respect the format, attempt to find the token
            if "true" in norm:
                return True
            if "false" in norm:
                return False
            logging.warning("Classifier returned unexpected output for gating: %s", text_resp)
            return None
    except Exception as exc:  # pylint: disable=broad-except
        logging.exception("Model-based gating failed: %s", exc)

    # Fallback to chat completions if Responses API fails
    try:
        completion = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
            max_tokens=16,
        )
        text_resp = completion.choices[0].message.content.strip().lower()
        if text_resp.startswith("true"):
            return True
        if text_resp.startswith("false"):
            return False
        if "true" in text_resp:
            return True
        if "false" in text_resp:
            return False
        logging.warning("Chat completion for gating returned unexpected: %s", text_resp)
        return None
    except Exception as exc:  # pylint: disable=broad-except
        logging.exception("OpenAI fallback chat completion failed in gating: %s", exc)
        return None

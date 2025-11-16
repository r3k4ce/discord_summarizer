"""Wrappers around AI providers used by the bot."""

from __future__ import annotations

import logging
from openai import OpenAI
import google.generativeai as genai

from config import GEMINI_API_KEY, OPENAI_API_KEY

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

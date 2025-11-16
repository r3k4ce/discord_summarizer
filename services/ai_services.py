"""Wrappers around AI providers used by the bot."""

from __future__ import annotations

import logging
from typing import Any

from openai import OpenAI
import google.generativeai as generativeai
from google import genai
from google.genai import types as genai_types

from config import (
    AUDIO_SUMMARY_MODEL,
    GEMINI_API_KEY,
    OPENAI_API_KEY,
    MODEL_BASED_GATING_MODEL,
    TEXT_SUMMARY_MODEL_PRIMARY,
    TEXT_SUMMARY_MODEL_FALLBACK,
    TEXT_SUMMARY_MAX_TOKENS,
    TEXT_SUMMARY_TEMPERATURE,
    TTS_LANGUAGE_CODE,
    TTS_MODEL,
    TTS_VOICE,
    VIDEO_SUMMARY_MODEL,
)

openai_client: OpenAI | None = None
if OPENAI_API_KEY:
    try:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
    except Exception as exc:  # pylint: disable=broad-except
        logging.error("Error initializing OpenAI client: %s", exc)

gemini_model = None
if GEMINI_API_KEY:
    try:
        generativeai.configure(api_key=GEMINI_API_KEY)
        gemini_model = generativeai.GenerativeModel(VIDEO_SUMMARY_MODEL)
    except Exception as exc:  # pylint: disable=broad-except
        logging.error("Error initializing Gemini client: %s", exc)

gemini_client: genai.Client | None = None
if GEMINI_API_KEY:
    try:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as exc:  # pylint: disable=broad-except
        logging.error("Error initializing google-genai client: %s", exc)


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
            model=TEXT_SUMMARY_MODEL_PRIMARY,
            instructions=system_prompt,
            input=user_prompt,
            max_output_tokens=TEXT_SUMMARY_MAX_TOKENS,
        )
        summary_text = _extract_text_from_openai_response(response)
        if summary_text:
            return summary_text.strip()
    except Exception as exc:  # pylint: disable=broad-except
        logging.error("Responses API failed: %s", exc)

    try:
        completion = openai_client.chat.completions.create(
            model=TEXT_SUMMARY_MODEL_FALLBACK,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEXT_SUMMARY_TEMPERATURE,
        )
        return completion.choices[0].message.content
    except Exception as exc:  # pylint: disable=broad-except
        logging.error("OpenAI fallback chat completion failed: %s", exc)
        return None


def get_audio_summary(text: str | None) -> str | None:
    """Generate a compact Spanish paragraph for audio narration."""

    if not text or not openai_client:
        return None

    system_prompt = (
        "Eres un asistente que escribe resúmenes para locución en audio. "
        "Condensa la noticia en un solo párrafo de 2-3 frases en español neutro, "
        "evitando opiniones fuertes y manteniendo un tono claro y directo." 
    )
    user_prompt = (
        "Texto original (reduce detalles irrelevantes, prioriza hechos clave):\n"
        f"{text[:4000]}"
    )

    try:
        response = openai_client.responses.create(
            model=AUDIO_SUMMARY_MODEL,
            instructions=system_prompt,
            input=user_prompt,
            max_output_tokens=160,
        )
        summary_text = _extract_text_from_openai_response(response)
        if summary_text:
            return summary_text.strip()
    except Exception as exc:  # pylint: disable=broad-except
        logging.error("Audio summary via Responses API failed: %s", exc)

    try:
        completion = openai_client.chat.completions.create(
            model=TEXT_SUMMARY_MODEL_FALLBACK,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=160,
        )
        return completion.choices[0].message.content
    except Exception as exc:  # pylint: disable=broad-except
        logging.error("Audio summary fallback chat completion failed: %s", exc)
        return None


def generate_tts_audio(text: str | None) -> tuple[bytes, str] | None:
    """Render the provided text into Spanish audio using Gemini TTS."""

    if not text or not gemini_client:
        return None

    try:
        audio_buffer = bytearray()
        detected_mime: str | None = None

        config = genai_types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=genai_types.SpeechConfig(
                voice_config=genai_types.VoiceConfig(
                    prebuilt_voice_config=genai_types.PrebuiltVoiceConfig(
                        voice_name=TTS_VOICE
                    )
                ),
                language_code=TTS_LANGUAGE_CODE,
            ),
        )

        for chunk in gemini_client.models.generate_content_stream(
            model=TTS_MODEL,
            contents=[
                genai_types.Content(
                    role="user",
                    parts=[genai_types.Part.from_text(text=text)],
                )
            ],
            config=config,
        ):
            candidate = _first_candidate(chunk)
            if not candidate or not candidate.content:
                continue
            for part in candidate.content.parts:
                inline_data = getattr(part, "inline_data", None)
                if inline_data and inline_data.data:
                    audio_buffer.extend(inline_data.data)
                    if inline_data.mime_type:
                        detected_mime = inline_data.mime_type

        if not audio_buffer:
            logging.error("Gemini TTS returned no audio data.")
            return None

        return bytes(audio_buffer), detected_mime or "audio/mpeg"
    except Exception as exc:  # pylint: disable=broad-except
        logging.error("Gemini TTS generation failed: %s", exc)
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


def _extract_text_from_openai_response(response: Any) -> str | None:
    """Best-effort extraction helper for Responses API outputs."""

    if getattr(response, "output_text", None):
        return response.output_text
    if getattr(response, "output", None):
        for item in response.output:
            if getattr(item, "text", None):
                return item.text
            if getattr(item, "content", None):
                for content_item in item.content:
                    if getattr(content_item, "text", None):
                        return content_item.text
    return None


def _first_candidate(chunk: Any) -> Any:
    """Return the first candidate object from a Gemini stream chunk."""

    candidates = getattr(chunk, "candidates", None)
    if not candidates:
        return None
    return candidates[0]

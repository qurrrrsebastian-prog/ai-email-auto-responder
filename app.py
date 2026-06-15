"""AI Email Auto-Responder.

Streamlit app that analyzes an incoming business email and drafts a
professional reply in Bahasa Indonesia using the Groq LLM API.

Author : Avatar Putra Sigit
GitHub : qurrrrsebastian-prog
"""

import os
import sys
import json
import re
from typing import Any, Dict

import streamlit as st
from groq import Groq

# --------------------------------------------------------------------------- #
# Page configuration
# --------------------------------------------------------------------------- #
st.set_page_config(
    page_title="AI Email Auto-Responder",
    layout="wide",
    page_icon="✉️",
)

GROQ_MODEL = "llama-3.3-70b-versatile"

# --------------------------------------------------------------------------- #
# Business context presets
# --------------------------------------------------------------------------- #
CONTEXT_PRESETS: Dict[str, str] = {
    "PT RKARI": (
        "PT RKARI bergerak di bidang rope access, pembersihan kaca gedung, "
        "building maintenance, dan waterproofing. Range harga: Rp 15-25jt "
        "(proyek kecil), Rp 30-60jt (proyek menengah), Rp 60-100jt+ "
        "(proyek besar). Kontak: putraavaar@gmail.com."
    ),
    "AVA.Group": (
        "AVA.Group adalah grup layanan profesional yang menaungi unit rope "
        "access, maintenance gedung, dan layanan kebersihan industrial. "
        "Selalu profesional, responsif, dan solutif. Kontak: putraavaar@gmail.com."
    ),
    "Generic": (
        "Perusahaan jasa profesional umum. Balas dengan sopan, jelas, dan "
        "berorientasi solusi tanpa menyebut detail harga spesifik."
    ),
}

# Default analysis used when the model response cannot be parsed.
FALLBACK_ANALYSIS: Dict[str, Any] = {
    "intent": "General Inquiry",
    "urgency": "Medium",
    "key_questions": [],
    "sentiment": "Neutral",
    "suggested_cta": "Reply with information",
}


# --------------------------------------------------------------------------- #
# Groq helpers
# --------------------------------------------------------------------------- #
def get_groq_client(api_key: str) -> Groq:
    """Create and return a Groq client.

    Args:
        api_key: The Groq API key.

    Returns:
        An initialized :class:`groq.Groq` client.

    Raises:
        ValueError: If the API key is empty.
    """
    try:
        if not api_key:
            raise ValueError("API key is empty.")
        return Groq(api_key=api_key)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Failed to initialize Groq client: {exc}") from exc


def groq_chat(
    client: Groq,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.4,
) -> str:
    """Send a chat completion request to Groq and return the text reply.

    Args:
        client: An initialized Groq client.
        system_prompt: The system instruction for the model.
        user_prompt: The user message to send.
        temperature: Sampling temperature (0.0-1.0).

    Returns:
        The assistant's text response, or an empty string on failure.
    """
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
        )
        return (response.choices[0].message.content or "").strip()
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Groq API Error: {exc}") from exc


def _extract_json(text: str) -> Dict[str, Any]:
    """Extract the first JSON object found in a string.

    Args:
        text: Raw model output that may contain a JSON object.

    Returns:
        The parsed dictionary, or an empty dict if none is found.
    """
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return {}
        return {}


def analyze_email(client: Groq, email_text: str, context: str) -> Dict[str, Any]:
    """Analyze an incoming email and return a structured summary.

    Args:
        client: An initialized Groq client.
        email_text: The raw email text from the client/prospect.
        context: Business context string used to ground the analysis.

    Returns:
        A dict with keys: intent, urgency, key_questions, sentiment,
        suggested_cta. Falls back to defaults on parse failure.
    """
    try:
        system_prompt = (
            "You are an expert email analyst. Analyze the incoming email and "
            "return JSON with: intent (string), urgency (High/Medium/Low), "
            "key_questions (list of strings), sentiment "
            "(Positive/Neutral/Negative), suggested_cta (string). "
            "Return ONLY valid JSON, no markdown."
        )
        user_prompt = (
            f"Business context: {context}\n\n"
            f"Incoming email:\n{email_text}"
        )
        raw = groq_chat(client, system_prompt, user_prompt, temperature=0.2)
        parsed = _extract_json(raw)
        if not parsed:
            return dict(FALLBACK_ANALYSIS)
        # Merge with fallback so all expected keys exist.
        result = dict(FALLBACK_ANALYSIS)
        result.update({k: parsed.get(k, result[k]) for k in result})
        if not isinstance(result["key_questions"], list):
            result["key_questions"] = [str(result["key_questions"])]
        return result
    except Exception:  # noqa: BLE001
        return dict(FALLBACK_ANALYSIS)


def draft_reply(
    client: Groq,
    email_text: str,
    analysis: Dict[str, Any],
    tone: str,
    context: str,
) -> str:
    """Draft a professional Indonesian reply based on the analysis.

    Args:
        client: An initialized Groq client.
        email_text: The original incoming email.
        analysis: The structured analysis from :func:`analyze_email`.
        tone: Desired tone for the reply.
        context: Business context string.

    Returns:
        The drafted reply email as plain text.
    """
    try:
        system_prompt = (
            "You are a professional Indonesian business email writer. Draft a "
            "reply email in Bahasa Indonesia based on the analysis. Include: "
            "salutation (Yth. / Halo), body answering ALL key questions, clear "
            "CTA (site visit / quotation / meeting), professional closing "
            f"(Hormat kami, Avatar Putra Sigit). Tone: {tone}. "
            f"Business context: {context}."
        )
        user_prompt = (
            f"Original email:\n{email_text}\n\n"
            f"Analysis:\n{json.dumps(analysis, ensure_ascii=False, indent=2)}\n\n"
            "Write the reply email now."
        )
        return groq_chat(client, system_prompt, user_prompt, temperature=0.4)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Groq API Error: {exc}") from exc


def copy_to_clipboard(text: str) -> bool:
    """Attempt to copy text to the system clipboard.

    Args:
        text: The text to copy.

    Returns:
        True if copied via pyperclip, False if unavailable (JS fallback used).
    """
    try:
        import pyperclip  # type: ignore

        pyperclip.copy(text)
        return True
    except Exception:  # noqa: BLE001
        return False


# --------------------------------------------------------------------------- #
# Session state
# --------------------------------------------------------------------------- #
if "draft" not in st.session_state:
    st.session_state.draft = ""
if "analysis" not in st.session_state:
    st.session_state.analysis = {}


# --------------------------------------------------------------------------- #
# Sidebar
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.header("⚙️ Settings")
    api_key = st.text_input(
        "Groq API Key",
        type="password",
        value=os.environ.get("GROQ_API_KEY", ""),
        help="Set $env:GROQ_API_KEY or paste here.",
    )
    tone = st.selectbox(
        "Tone Balasan",
        ["Profesional", "Santai tapi Profesional", "Assertive", "Empatik"],
    )
    context_choice = st.selectbox(
        "Business Context",
        list(CONTEXT_PRESETS.keys()),
    )
    st.link_button("📧 Buka Gmail", "https://mail.google.com")


# --------------------------------------------------------------------------- #
# Main UI
# --------------------------------------------------------------------------- #
st.title("✉️ AI Email Auto-Responder")
st.caption("Analisis email masuk & buat draft balasan profesional dalam Bahasa Indonesia")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📥 Email Masuk")
    email_text = st.text_area(
        "Paste email dari klien:",
        height=250,
        placeholder=(
            "Dari: klien@company.com\n"
            "Subjek: Penawaran...\n\n"
            "Isi: ..."
        ),
    )
    generate = st.button(
        "✨ Generate Draft Reply",
        type="primary",
        use_container_width=True,
    )

with col2:
    st.subheader("📤 Draft Reply")
    placeholder = st.empty()

# --------------------------------------------------------------------------- #
# Generate flow
# --------------------------------------------------------------------------- #
if generate:
    if not api_key:
        st.error("Groq API Error: API key belum diisi. Set $env:GROQ_API_KEY.")
        st.stop()
    if not email_text.strip():
        st.warning("Tempel email masuk terlebih dahulu.")
        st.stop()

    try:
        client = get_groq_client(api_key)
    except ValueError as exc:
        st.error(f"Groq API Error: {exc}")
        st.stop()

    context = CONTEXT_PRESETS[context_choice]
    progress = st.progress(0, text="Menganalisis email...")

    try:
        progress.progress(30, text="Menganalisis email...")
        analysis = analyze_email(client, email_text, context)

        progress.progress(70, text="Menyusun draft balasan...")
        draft = draft_reply(client, email_text, analysis, tone, context)

        progress.progress(100, text="Selesai!")
        st.session_state.analysis = analysis
        st.session_state.draft = draft
    except RuntimeError as exc:
        progress.empty()
        st.error(str(exc))
        st.stop()
    finally:
        progress.empty()

# --------------------------------------------------------------------------- #
# Render draft (persisted via session state)
# --------------------------------------------------------------------------- #
if st.session_state.draft:
    with col2:
        st.text_area(
            "Draft (editable):",
            value=st.session_state.draft,
            height=300,
            key="draft_view",
        )
        st.markdown("**Copy-friendly:**")
        st.code(st.session_state.draft, language="text")

        if st.button("📋 Copy to Clipboard"):
            if copy_to_clipboard(st.session_state.draft):
                st.success("Disalin ke clipboard!")
            else:
                st.info(
                    "pyperclip tidak tersedia. Gunakan tombol copy di kanan "
                    "atas blok kode di atas."
                )

        with st.expander("🔍 Analisis Email"):
            analysis = st.session_state.analysis
            st.markdown(f"**Intent:** {analysis.get('intent', '-')}")
            st.markdown(f"**Urgency:** {analysis.get('urgency', '-')}")
            st.markdown(f"**Sentiment:** {analysis.get('sentiment', '-')}")
            st.markdown(f"**Suggested CTA:** {analysis.get('suggested_cta', '-')}")
            st.markdown("**Key Questions:**")
            questions = analysis.get("key_questions", [])
            if questions:
                for q in questions:
                    st.markdown(f"- {q}")
            else:
                st.markdown("- _(tidak terdeteksi)_")

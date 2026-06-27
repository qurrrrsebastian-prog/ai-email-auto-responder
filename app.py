"""AI Email Auto-Responder — Groq (Llama 3.3 70B) | v2.0 production upgrade.

Teal Comms theme, split-screen compose view. Analyzes an incoming business email
and drafts a professional Bahasa Indonesia reply. v2.0 adds SQLite persistence
(email_sessions, context_profiles, reply_templates, audit_log), an email-history
tab, custom context-profile CRUD, a sentiment timeline chart, a reply-template
manager, batch CSV processing and 3-variant draft versioning.

Author: Avatar Putra Sigit | GitHub: qurrrrsebastian-prog
"""
import json
import os
import re
from typing import Any, Dict

import pandas as pd
import plotly.express as px
import streamlit as st

import database as db
from security import sanitize_input, validate_email
from ui_components import (PRIMARY, SENTIMENT_COLORS, URGENCY_COLORS,
                           render_footer, render_header, render_status_badge)

st.set_page_config(page_title="AI Email Auto-Responder", layout="wide", page_icon="✉️")

GROQ_MODEL = "llama-3.3-70b-versatile"

db.init_db()

CONTEXT_PRESETS: Dict[str, str] = {
    "PT RKARI": (
        "PT RKARI bergerak di bidang rope access, pembersihan kaca gedung, "
        "building maintenance, dan waterproofing. Range harga: Rp 15-25jt "
        "(proyek kecil), Rp 30-60jt (proyek menengah), Rp 60-100jt+ "
        "(proyek besar). Kontak: putraavaar@gmail.com."),
    "AVA.Group": (
        "AVA.Group adalah grup layanan profesional yang menaungi unit rope "
        "access, maintenance gedung, dan layanan kebersihan industrial. "
        "Selalu profesional, responsif, dan solutif. Kontak: putraavaar@gmail.com."),
    "Generic": (
        "Perusahaan jasa profesional umum. Balas dengan sopan, jelas, dan "
        "berorientasi solusi tanpa menyebut detail harga spesifik."),
}

FALLBACK_ANALYSIS: Dict[str, Any] = {
    "intent": "General Inquiry", "urgency": "Medium", "key_questions": [],
    "sentiment": "Neutral", "suggested_cta": "Reply with information",
}


# --------------------------------------------------------------------------- #
# Groq helpers
# --------------------------------------------------------------------------- #
def get_groq_client(api_key: str):
    """Create a Groq client, or raise ValueError."""
    if not api_key:
        raise ValueError("API key is empty.")
    try:
        from groq import Groq
        return Groq(api_key=api_key)
    except ValueError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"Failed to initialize Groq client: {exc}") from exc


def groq_chat(client, system_prompt: str, user_prompt: str,
              temperature: float = 0.4) -> str:
    """Send a chat completion request to Groq and return the text reply."""
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": user_prompt}],
            temperature=temperature,
        )
        return (response.choices[0].message.content or "").strip()
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Groq API Error: {exc}") from exc


def _extract_json(text: str) -> Dict[str, Any]:
    """Extract the first JSON object found in a string."""
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


def analyze_email(client, email_text: str, context: str) -> Dict[str, Any]:
    """Analyze an incoming email and return a structured summary."""
    try:
        system_prompt = (
            "You are an expert email analyst. Analyze the incoming email and "
            "return JSON with: intent (string), urgency (High/Medium/Low), "
            "key_questions (list of strings), sentiment "
            "(Positive/Neutral/Negative), suggested_cta (string). "
            "Return ONLY valid JSON, no markdown.")
        user_prompt = f"Business context: {context}\n\nIncoming email:\n{email_text}"
        raw = groq_chat(client, system_prompt, user_prompt, temperature=0.2)
        parsed = _extract_json(raw)
        if not parsed:
            return dict(FALLBACK_ANALYSIS)
        result = dict(FALLBACK_ANALYSIS)
        result.update({k: parsed.get(k, result[k]) for k in result})
        if not isinstance(result["key_questions"], list):
            result["key_questions"] = [str(result["key_questions"])]
        return result
    except Exception:  # noqa: BLE001
        return dict(FALLBACK_ANALYSIS)


def draft_reply(client, email_text: str, analysis: Dict[str, Any], tone: str,
                context: str, temperature: float = 0.4) -> str:
    """Draft a professional Indonesian reply based on the analysis."""
    system_prompt = (
        "You are a professional Indonesian business email writer. Draft a reply "
        "email in Bahasa Indonesia based on the analysis. Include: salutation "
        "(Yth. / Halo), body answering ALL key questions, clear CTA (site visit "
        "/ quotation / meeting), professional closing (Hormat kami, Avatar Putra "
        f"Sigit). Tone: {tone}. Business context: {context}.")
    user_prompt = (
        f"Original email:\n{email_text}\n\n"
        f"Analysis:\n{json.dumps(analysis, ensure_ascii=False, indent=2)}\n\n"
        "Write the reply email now.")
    return groq_chat(client, system_prompt, user_prompt, temperature=temperature)


def all_contexts() -> Dict[str, str]:
    """Merge built-in presets with custom DB profiles."""
    merged = dict(CONTEXT_PRESETS)
    for p in db.get_context_profiles():
        merged[f"★ {p['profile_name']}"] = p["context_text"]
    return merged


# --------------------------------------------------------------------------- #
# Session state
# --------------------------------------------------------------------------- #
st.session_state.setdefault("drafts", [])
st.session_state.setdefault("analysis", {})

# --------------------------------------------------------------------------- #
# Sidebar
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.header("⚙️ Settings")
    api_key = st.text_input("Groq API Key", type="password",
                            value=os.environ.get("GROQ_API_KEY", ""),
                            help="Set $env:GROQ_API_KEY or paste here.")
    tone = st.selectbox("Tone Balasan",
                        ["Profesional", "Santai tapi Profesional", "Assertive",
                         "Empatik"])
    contexts = all_contexts()
    context_choice = st.selectbox("Business Context", list(contexts.keys()))
    st.link_button("📧 Buka Gmail", "https://mail.google.com")

render_header("✉️ AI Email Auto-Responder",
              "Analyze inbound email & draft a professional reply · v2.0 Teal Comms")
if not api_key:
    st.info("ℹ️ GROQ_API_KEY not set — generation is disabled. History, profiles, "
            "templates and analytics remain available.")

tab_compose, tab_history, tab_assets, tab_analytics, tab_batch = st.tabs(
    ["📝 Compose", "📨 History", "🗂️ Profiles & Templates", "📊 Analytics",
     "📦 Batch"])

# --------------------------------------------------------------------------- #
# TAB — Compose (split screen)
# --------------------------------------------------------------------------- #
with tab_compose:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📥 Email Masuk")
        sender = st.text_input("Sender email (optional)")
        subject = st.text_input("Subject (optional)")
        email_text = st.text_area("Paste email dari klien:", height=240,
                                  placeholder="Dari: klien@company.com\nSubjek: ...\n\nIsi: ...")
        generate = st.button("✨ Generate 3 Draft Variants", type="primary",
                             use_container_width=True, disabled=not api_key)
    with col2:
        st.subheader("📤 Analysis & Drafts")
        analysis_ph = st.container()

    if generate:
        if not email_text.strip():
            st.warning("Tempel email masuk terlebih dahulu.")
        else:
            try:
                client = get_groq_client(api_key)
                context = contexts[context_choice]
                progress = st.progress(0, text="Menganalisis email...")
                analysis = analyze_email(client, email_text, context)
                progress.progress(40, text="Menyusun 3 varian draft...")
                drafts = []
                for i, temp in enumerate((0.3, 0.5, 0.7), 1):
                    drafts.append(draft_reply(client, email_text, analysis, tone,
                                              context, temperature=temp))
                    progress.progress(40 + i * 20, text=f"Draft {i}/3 selesai...")
                progress.empty()
                st.session_state.analysis = analysis
                st.session_state.drafts = drafts
                db.add_session(
                    sanitize_input(sender, 120), sanitize_input(subject, 200),
                    email_text, json.dumps(analysis, ensure_ascii=False), tone,
                    context_choice, drafts[0])
                db.add_log("generate", f"{subject or 'no-subject'}")
            except (ValueError, RuntimeError) as exc:
                st.error(str(exc))

    if st.session_state.analysis:
        with analysis_ph:
            a = st.session_state.analysis
            b1, b2, b3 = st.columns(3)
            with b1:
                render_status_badge(f"Sentiment: {a.get('sentiment','-')}",
                                    SENTIMENT_COLORS.get(a.get("sentiment"), PRIMARY))
            with b2:
                render_status_badge(f"Urgency: {a.get('urgency','-')}",
                                    URGENCY_COLORS.get(a.get("urgency"), PRIMARY))
            with b3:
                render_status_badge(f"Intent: {a.get('intent','-')}", PRIMARY)
            st.markdown(f"**Suggested CTA:** {a.get('suggested_cta','-')}")
            qs = a.get("key_questions", [])
            if qs:
                st.markdown("**Key questions:**")
                for q in qs:
                    st.markdown(f"- {q}")
    if st.session_state.drafts:
        st.divider()
        st.markdown("#### 📝 Draft Versions")
        dtabs = st.tabs([f"Variant {i+1}" for i in range(len(st.session_state.drafts))])
        for dt, draft in zip(dtabs, st.session_state.drafts):
            with dt:
                st.text_area("Editable draft", value=draft, height=260,
                             key=f"draft_{hash(draft) & 0xffff}")
                st.code(draft, language="text")

# --------------------------------------------------------------------------- #
# TAB — History
# --------------------------------------------------------------------------- #
with tab_history:
    st.subheader("📨 Email History")
    sessions = db.get_sessions()
    if sessions.empty:
        st.caption("No emails processed yet.")
    else:
        hc1, hc2 = st.columns([3, 1])
        hc1.metric("Processed emails", len(sessions))
        if hc2.button("🗑️ Clear history", use_container_width=True):
            db.clear_sessions()
            st.rerun()
        for _, s in sessions.head(40).iterrows():
            try:
                a = json.loads(s["analysis_json"]) if s["analysis_json"] else {}
            except Exception:  # noqa: BLE001
                a = {}
            with st.expander(f"{s['timestamp']} · {s['subject'] or '(no subject)'} · "
                             f"{a.get('sentiment','?')}"):
                st.markdown(f"**From:** {s['sender_email'] or '—'} · "
                            f"**Tone:** {s['tone_used']} · **Context:** {s['context_used']}")
                st.markdown("**Incoming:**")
                st.text(s["incoming_email"][:800])
                st.markdown("**Draft reply:**")
                st.markdown(s["draft_reply"])
        st.download_button("⬇️ Export history CSV",
                           sessions.to_csv(index=False).encode("utf-8"),
                           file_name="email_history.csv", mime="text/csv")

# --------------------------------------------------------------------------- #
# TAB — Profiles & templates
# --------------------------------------------------------------------------- #
with tab_assets:
    pc, tc = st.columns(2)
    with pc:
        st.subheader("🗂️ Context Profiles")
        for p in db.get_context_profiles():
            with st.expander(f"★ {p['profile_name']}"):
                txt = st.text_area("Context", p["context_text"],
                                   key=f"ctx_{p['id']}", height=100)
                cc1, cc2 = st.columns(2)
                if cc1.button("💾 Save", key=f"sctx_{p['id']}"):
                    db.save_context_profile(p["profile_name"],
                                            sanitize_input(txt, 2000))
                    st.rerun()
                if cc2.button("🗑️ Delete", key=f"dctx_{p['id']}"):
                    db.delete_context_profile(p["id"])
                    st.rerun()
        with st.form("new_ctx", clear_on_submit=True):
            st.markdown("**➕ New context profile**")
            nm = st.text_input("Profile name")
            tx = st.text_area("Context text")
            if st.form_submit_button("Create") and nm:
                db.save_context_profile(sanitize_input(nm, 80), sanitize_input(tx, 2000))
                st.rerun()
    with tc:
        st.subheader("✉️ Reply Templates")
        for t in db.get_templates():
            with st.expander(f"📄 {t['name']}"):
                body = st.text_area("Body", t["body"], key=f"tpl_{t['id']}", height=100)
                tt1, tt2 = st.columns(2)
                if tt1.button("💾 Save", key=f"stpl_{t['id']}"):
                    db.save_template(t["name"], sanitize_input(body, 2000))
                    st.rerun()
                if tt2.button("🗑️ Delete", key=f"dtpl_{t['id']}"):
                    db.delete_template(t["id"])
                    st.rerun()
        with st.form("new_tpl", clear_on_submit=True):
            st.markdown("**➕ New template**")
            tnm = st.text_input("Template name")
            tbd = st.text_area("Template body")
            if st.form_submit_button("Create") and tnm:
                db.save_template(sanitize_input(tnm, 80), sanitize_input(tbd, 2000))
                st.rerun()

# --------------------------------------------------------------------------- #
# TAB — Analytics (sentiment timeline)
# --------------------------------------------------------------------------- #
with tab_analytics:
    st.subheader("📊 Sentiment Timeline")
    sessions = db.get_sessions()
    if sessions.empty:
        st.caption("No data yet.")
    else:
        recs = []
        for _, s in sessions.iterrows():
            try:
                a = json.loads(s["analysis_json"]) if s["analysis_json"] else {}
            except Exception:  # noqa: BLE001
                a = {}
            recs.append({"timestamp": s["timestamp"],
                         "sentiment": a.get("sentiment", "Neutral"),
                         "urgency": a.get("urgency", "Medium")})
        adf = pd.DataFrame(recs)
        adf["timestamp"] = pd.to_datetime(adf["timestamp"], errors="coerce")
        score_map = {"Positive": 1, "Neutral": 0, "Negative": -1}
        adf["score"] = adf["sentiment"].map(score_map).fillna(0)
        fig = px.line(adf.sort_values("timestamp"), x="timestamp", y="score",
                      markers=True, title="Sentiment over time (1=Positive, -1=Negative)")
        fig.update_yaxes(range=[-1.2, 1.2])
        st.plotly_chart(fig, use_container_width=True)
        c1, c2 = st.columns(2)
        with c1:
            dist = adf["sentiment"].value_counts().reset_index()
            dist.columns = ["sentiment", "count"]
            st.plotly_chart(px.pie(dist, names="sentiment", values="count",
                                   color="sentiment", color_discrete_map=SENTIMENT_COLORS,
                                   title="Sentiment distribution"),
                            use_container_width=True)
        with c2:
            ud = adf["urgency"].value_counts().reset_index()
            ud.columns = ["urgency", "count"]
            st.plotly_chart(px.bar(ud, x="urgency", y="count", color="urgency",
                                   color_discrete_map=URGENCY_COLORS,
                                   title="Urgency distribution"),
                            use_container_width=True)

# --------------------------------------------------------------------------- #
# TAB — Batch
# --------------------------------------------------------------------------- #
with tab_batch:
    st.subheader("📦 Batch Processing")
    st.caption("Upload a CSV with an 'email' column (optional 'sender', 'subject'). "
               "Each row is analyzed and a draft is generated.")
    up = st.file_uploader("CSV file", type=["csv"], disabled=not api_key)
    if up is not None:
        try:
            bdf = pd.read_csv(up)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Could not read CSV: {exc}")
            bdf = pd.DataFrame()
        if "email" not in bdf.columns:
            st.error("CSV must contain an 'email' column.")
        elif st.button("▶️ Process batch", type="primary"):
            try:
                client = get_groq_client(api_key)
                context = contexts[context_choice]
                prog = st.progress(0.0)
                results = []
                for i, row in bdf.reset_index(drop=True).iterrows():
                    body = str(row["email"])
                    analysis = analyze_email(client, body, context)
                    draft = draft_reply(client, body, analysis, tone, context)
                    db.add_session(str(row.get("sender", "")), str(row.get("subject", "")),
                                   body, json.dumps(analysis, ensure_ascii=False),
                                   tone, context_choice, draft)
                    results.append({"subject": row.get("subject", ""),
                                    "sentiment": analysis.get("sentiment"),
                                    "urgency": analysis.get("urgency")})
                    prog.progress((i + 1) / len(bdf))
                db.add_log("batch", f"{len(bdf)} emails")
                st.success(f"Processed {len(bdf)} emails.")
                st.dataframe(pd.DataFrame(results), use_container_width=True,
                             hide_index=True)
            except (ValueError, RuntimeError) as exc:
                st.error(str(exc))

render_footer()

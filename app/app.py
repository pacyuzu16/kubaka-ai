"""KUBAKA AI — demo interface.

Left: what the operator sees (a chat, like WhatsApp).
Right: what the dealer receives (a structured service ticket).

Run:  streamlit run app/app.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from src.pipeline import triage
from src.config import LANGUAGES

st.set_page_config(page_title="KUBAKA AI", page_icon="🛠", layout="wide")

URGENCY_COLOUR = {
    "critical": "#c0392b",
    "high": "#e67e22",
    "medium": "#f1c40f",
    "low": "#27ae60",
}

EXAMPLES = [
    "The boom is leaking oil and moves very slowly",
    "iri kuvuza amavuta kandi ukuboko kugenda buhoro",
    "le moteur chauffe beaucoup et perd de la puissance",
    "injini inapata joto sana na inatoa moshi",
]

st.title("KUBAKA AI")
st.caption(
    "Multilingual fault triage for construction equipment · "
    "English · Français · Kinyarwanda · Kiswahili"
)

if "history" not in st.session_state:
    st.session_state.history = []

left, right = st.columns([1, 1], gap="large")

with left:
    st.subheader("Operator")
    st.caption("However the operator actually talks. No technical terms required.")

    choice = st.selectbox("Try an example", ["—"] + EXAMPLES)
    default = "" if choice == "—" else choice
    message = st.text_area("Message", value=default, height=110,
                           placeholder="Describe the problem in any language…")

    if st.button("Send", type="primary", use_container_width=True) and message.strip():
        with st.spinner("Diagnosing…"):
            try:
                st.session_state.result = triage(message.strip())
                st.session_state.history.append(message.strip())
            except Exception as exc:
                st.error(f"Pipeline error: {exc}")

    result = st.session_state.get("result")
    if result:
        st.markdown("**Reply sent to operator**")
        st.info(result.reply)
        st.caption(f"Detected language: {LANGUAGES.get(result.language, result.language)}")

with right:
    st.subheader("Dealer ticket")
    result = st.session_state.get("result")
    if not result:
        st.caption("Send a message to generate a service ticket.")
    elif result.needs_human:
        st.warning(
            "**Flagged for human review.** The description was too vague or "
            "described multiple unrelated faults. Escalated rather than guessed."
        )
    else:
        colour = URGENCY_COLOUR.get(result.urgency, "#7f8c8d")
        st.markdown(
            f"<span style='background:{colour};color:#fff;padding:4px 12px;"
            f"border-radius:4px;font-weight:600'>{result.urgency.upper()}</span>",
            unsafe_allow_html=True,
        )
        st.markdown(f"### {result.subcategory}")
        st.caption(f"category: {result.category} · confidence {result.confidence:.0%}")

        st.markdown("**Symptoms extracted**")
        for symptom in result.symptoms:
            st.markdown(f"- {symptom}")

        st.markdown("**Likely causes**")
        for cause in result.causes:
            st.markdown(
                f"- **{cause.get('cause','')}** "
                f"*({cause.get('likelihood','')})* — {cause.get('check','')}"
            )

        st.markdown("**Parts likely needed**")
        st.markdown(", ".join(result.parts) if result.parts else "—")

        if result.environmental:
            st.markdown("**Environmental note**")
            st.success(result.environmental)

        with st.expander("Raw ticket (JSON)"):
            st.json(result.to_ticket())

#THIS VERISON IS NOT FOR USAGE, its so i can host it on streamlit.

import streamlit as st
from google import genai
import concurrent.futures

# -Constants-
PERSONAS = {
    "MELCHIOR-1": "You are the scientist: judge purely on logic, data, and long term strategic value.",
    "BALTHASAR-2": "You are the mother: judge on safety, harm reduction, and protecting people",
    "CASPER-3": "You are the individual: judge on personal impact, fairness, and self-interest."
}

FORMAT = "\n\nReply in exactly this format:\nVERDICT: APPROVE|REJECT|CONDITIONAL\nREASONING: <1-2 sentences>"
MODEL_NAME = "gemini-3.5-flash"

# -Setup-
st.set_page_config(page_title="MAGI System", page_icon="🖥️", layout="centered")

api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("GEMINI_API_KEY not found in Streamlit secrets. See the deployment instructions below the code block.")
    st.stop()

client = genai.Client(api_key=api_key)

# -Main logic-

def ask_computer(name, persona, question):
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=persona + FORMAT + f"\n\nProposal: {question}"
        )
        text = response.text
        verdict = next(l for l in text.splitlines() if "VERDICT" in l.upper()).split(":", 1)[1].strip()
        reasoning = next(l for l in text.splitlines() if "REASONING" in l.upper()).split(":", 1)[1].strip()
    except Exception as e:
        verdict, reasoning = "CONDITIONAL", f"(computer failed: {e})"
    return name, verdict, reasoning


def magi_debate(question):
    with concurrent.futures.ThreadPoolExecutor() as ex:
        results = list(ex.map(lambda kv: ask_computer(kv[0], kv[1], question), PERSONAS.items()))

    approvals = sum(1 for _, v, _ in results if "APPROVE" in v.upper())
    rejections = sum(1 for _, v, _ in results if "REJECT" in v.upper())
    decision = (
        "APPROVE" if approvals >= 2 else
        "REJECT" if rejections >= 2 else
        "NEUTRAL"
    )
    return results, decision


# -UI-

st.title("🖥️ MAGI SYSTEM")
st.caption("Three-unit AI deliberation, powered by Gemini")

question = st.text_input("Proposal for MAGI:", placeholder="Should we launch on Friday the 13th?")

if st.button("Deliberate", type="primary") and question:
    with st.spinner("Consulting MELCHIOR-1, BALTHASAR-2, CASPER-3..."):
        results, decision = magi_debate(question)

    st.divider()

    cols = st.columns(3)
    verdict_colors = {"APPROVE": "green", "REJECT": "red", "CONDITIONAL": "orange"}

    for col, (name, verdict, reasoning) in zip(cols, results):
        color = verdict_colors.get(verdict, "gray")
        with col:
            st.markdown(f"**{name}**")
            st.markdown(f":{color}[{verdict}]")
            st.caption(reasoning)

    st.divider()

    decision_style = {
        "APPROVE": ("green", "SYSTEM APPROVED"),
        "REJECT": ("red", "SYSTEM REJECTED"),
        "NEUTRAL": ("orange", "NO CONSENSUS"),
    }[decision]
    st.markdown(f"## :{decision_style[0]}[{decision_style[1]}]")

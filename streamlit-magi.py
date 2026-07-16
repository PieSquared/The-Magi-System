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

# Try secrets first (for when someone deploys their own with a secret set),
# otherwise fall back to asking the user for a key via a popup dialog.
api_key = st.secrets.get("GEMINI_API_KEY") if hasattr(st, "secrets") else None

if "user_api_key" not in st.session_state:
    st.session_state.user_api_key = ""

@st.dialog("Enter your Gemini API key")
def api_key_popup():
    st.write("This app doesn't have a stored API key. Paste your own Gemini API key below to use it. It's only kept for this session and isn't saved anywhere.")
    key_input = st.text_input("Gemini API key", type="password", placeholder="AIza...")
    st.caption("Get a key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey)")
    if st.button("Save key", type="primary"):
        if key_input.strip():
            st.session_state.user_api_key = key_input.strip()
            st.rerun()
        else:
            st.warning("Please enter a key.")

if not api_key and not st.session_state.user_api_key:
    api_key_popup()
    st.stop()

final_key = api_key or st.session_state.user_api_key
client = genai.Client(api_key=final_key)

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

with st.expander("Using your own API key"):
    st.write(f"Currently using a key you entered this session.") if st.session_state.user_api_key and not api_key else None
    if st.button("Change API key"):
        st.session_state.user_api_key = ""
        st.rerun()

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

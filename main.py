# -Libraries-
from google import genai
from dotenv import load_dotenv
import os
import concurrent.futures
import sys

# -Constants-
PERSONAS = {
    "MELCHIOR-1": "You are the scientist: judge purely on logic, data, and long term strategic value.",
    "BALTHASAR-2": "You are the mother: judge on safety, harm reduction, and protecting people",
    "CASPER-3": "You are the individual: judge on personal impact, fairness, and self-interest."
}

FORMAT = "\n\nReply in exactly this format:\nVERDICT: APPROVE|REJECT|CONDITIONAL\nREASONING: <1-2 sentences>"
MODEL_NAME = "gemini-3.5-flash" 

# -Setup things-

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY isnt in the .env file, make sure to put one in")

client = genai.Client(api_key=api_key)

# -Main-
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


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or input("Proposal for MAGI: ")
    results, decision = magi_debate(question)

    print(f"\nPROPOSAL: {question}\n" + "-" * 50)
    for name, verdict, reasoning in results:
        print(f"{name:<12} [{verdict}]\n  → {reasoning}\n")
    print(f"FINAL DECISION: {decision}")
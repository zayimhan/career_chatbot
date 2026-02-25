import re
from openai import OpenAI

LEGAL_RE = re.compile(r"\b(legal|law|visa|immigration|work permit|contract clause|nda|non-compete|severance)\b", re.I)
SALARY_RE = re.compile(r"\b(salary|compensation|pay|rate|offer|tc|total comp|negotiat)\b", re.I)
AMBIG_RE  = re.compile(r"\b(offer|position|role)\b", re.I)

EMPLOYER_INTENT_RE = re.compile(
    r"\b(interview|schedule|meeting|call|offer|position|role|job|hiring|recruit|recruiter|application|resume|cv|availability|start date)\b",
    re.I
)

TRIVIAL_RE = re.compile(r"^\s*(hi|hello|hey|selam|merhaba|ok|okay|thanks|thank you|teşekkür|tesekkur)\s*[!.]*\s*$", re.I)

class RiskDetector:
    """
    Returns a dict:
      {
        "is_employer": bool,
        "needs_human": bool,
        "reason": str,
        "category": str
      }
    """
    def __init__(self, model="gpt-4o-mini"):
        self.client = OpenAI()
        self.model = model

    def is_trivial(self, text: str) -> bool:
        t = (text or "").strip()
        return (not t) or bool(TRIVIAL_RE.match(t)) or (len(t) <= 6 and "?" not in t)

    def looks_like_employer(self, text: str) -> bool:
        if self.is_trivial(text):
            return False
        return bool(EMPLOYER_INTENT_RE.search(text or ""))

    def rule_risks(self, text: str) -> dict | None:
        t = text or ""
        if LEGAL_RE.search(t):
            return {"needs_human": True, "category": "legal", "reason": "Legal/visa/contract question."}

        # Salary negotiation beyond threshold (rule-based)
        # If the message contains a number and salary keywords, treat as human-needed
        if SALARY_RE.search(t) and re.search(r"\b(\d{2,6})\b", t):
            return {"needs_human": True, "category": "salary", "reason": "Salary negotiation with numbers (needs user approval)."}

        # Ambiguous job offer (missing basics)
        if AMBIG_RE.search(t) and ("company" not in t.lower()) and ("role" not in t.lower()):
            return {"needs_human": True, "category": "ambiguous_offer", "reason": "Offer/role message lacks key details."}

        return None

    def deep_technical_gate(self, question: str) -> dict | None:
        """
        LLM gate for “deep technical outside domain”.
        Use sparingly (only if question looks technical).
        """
        t = (question or "").lower()
        if not any(k in t for k in ["system design", "distributed", "kubernetes", "compiler", "kernel", "cryptography", "proof", "theorem", "formal", "cuda", "pytorch internals"]):
            return None

        prompt = f"""
You are a risk classifier for a career assistant.

Decide if the question is deep technical and likely outside the candidate's expertise based on profile.
Return ONLY JSON:
{{"needs_human": true/false, "reason": "<short>" }}

Question:
{question}
""".strip()

        res = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        txt = res.choices[0].message.content or ""
        if "true" in txt.lower():
            return {"needs_human": True, "category": "deep_technical", "reason": "Deep technical question flagged by classifier."}
        return None

    def check(self, message: str) -> dict:
        if self.is_trivial(message):
            return {"is_employer": False, "needs_human": False, "category": "trivial", "reason": "Trivial message."}

        is_employer = self.looks_like_employer(message)

        r = self.rule_risks(message)
        if r:
            return {"is_employer": is_employer, **r}

        dt = self.deep_technical_gate(message)
        if dt:
            return {"is_employer": is_employer, **dt}

        return {"is_employer": is_employer, "needs_human": False, "category": "ok", "reason": "No risk detected."}
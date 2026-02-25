import json
import os
import re
from openai import OpenAI
from pypdf import PdfReader

from career_agent.tools.email_notify import send_email
from career_agent.tools.notify import push
from career_agent.utils.logger import log_jsonl
from career_agent.agents.evaluator_agent import EvaluatorAgent
from career_agent.agents.risk_detector import RiskDetector

EMAIL_RE = re.compile(r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})")

def extract_email(text: str):
    m = EMAIL_RE.search(text or "")
    return m.group(1) if m else None

# ---- tool functions used by OpenAI function calling ----

def record_user_details(email, name="Name not provided", notes="not provided"):
    # optional: also push lead capture
    push("Lead Captured", f"{name} | {email}\nNotes: {notes}")
    log_jsonl("logs/leads.jsonl", {"email": email, "name": name, "notes": notes})
    return {"recorded": "ok"}

def record_unknown_question(question):
    log_jsonl("logs/unknown.jsonl", {"question": question})
    return {"recorded": "ok"}

record_user_details_json = {
    "name": "record_user_details",
    "description": "Record user contact information",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {"type": "string"},
            "name": {"type": "string"},
            "notes": {"type": "string"},
        },
        "required": ["email"],
        "additionalProperties": False,
    },
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Record any question that cannot be answered from the provided profile/CV, or needs human intervention.",
    "parameters": {
        "type": "object",
        "properties": {"question": {"type": "string"}},
        "required": ["question"],
        "additionalProperties": False,
    },
}

TOOLS = [
    {"type": "function", "function": record_user_details_json},
    {"type": "function", "function": record_unknown_question_json},
]

class CareerAgent:
    def __init__(self, model="gpt-4o-mini"):
        self.client = OpenAI()
        self.model = model

        self.evaluator = EvaluatorAgent(model=model)
        self.risk = RiskDetector(model=model)

        self.name = "Zayimhan Korkmaz"

        reader = PdfReader("me/linkedin.pdf")
        self.linkedin = ""
        for page in reader.pages:
            t = page.extract_text()
            if t:
                self.linkedin += t + "\n"

        with open("me/summary.txt", "r", encoding="utf-8") as f:
            self.summary = f.read()

    def system_prompt(self):
        return f"""
You are acting as {self.name}, communicating with potential employers on {self.name}'s behalf.

Hard rules:
- Tone: professional, concise, polite.
- Do NOT invent credentials, employers, degrees, or numbers.
- Use ONLY the provided Summary + LinkedIn for factual claims about the candidate.
- If asked something about the candidate that is NOT in the profile, say you don’t have that info and ask a clarifying question.
- If the message is an offer the candidate wants to decline, politely decline and keep the door open.
- If the message is ambiguous (missing role/company/location/compensation), ask 1–3 clarifying questions.
- If the question requires legal advice or salary negotiation approval, request human intervention (use record_unknown_question).

## Summary:
{self.summary}

## LinkedIn:
{self.linkedin}
""".strip()

    def _handle_tool_calls(self, tool_calls):
        results = []
        for tc in tool_calls:
            name = tc.function.name
            args = json.loads(tc.function.arguments or "{}")

            fn = globals().get(name)
            res = fn(**args) if fn else {}
            results.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(res)})
        return results

    def generate(self, messages):
        while True:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOLS,
            )
            choice = resp.choices[0]
            if choice.finish_reason == "tool_calls":
                messages.append(choice.message)
                messages.extend(self._handle_tool_calls(choice.message.tool_calls))
                continue
            return choice.message.content or ""

    def reply(self, message: str, history_messages: list[dict]):
        # 1) risk / employer detection
        risk = self.risk.check(message)

        # 2) If employer message arrives => push + email (incoming only; NO draft here)
        if risk["is_employer"]:
            send_email(
                subject="New employer message received",
                body=f"Employer message:\n\n{message}\n"
            )
            push("New employer message", message[:700])
            log_jsonl("logs/incoming.jsonl", {"message": message, "is_employer": True})

        # 3) If needs human => push + email + log + still generate a safe response
        if risk["needs_human"]:
            send_email(
                subject="Human intervention needed (unknown/unsafe)",
                body=(
                    f"Category: {risk['category']}\n"
                    f"Reason: {risk['reason']}\n\n"
                    f"Q: {message[:700]}"
                ),
            )
            push(
                "Human intervention needed",
                f"Category: {risk['category']}\nReason: {risk['reason']}\n\nQ: {message[:700]}",
            )
            log_jsonl(
                "logs/unknown.jsonl",
                {"question": message, "category": risk["category"], "reason": risk["reason"]},
            )
            # still proceed to draft

        # 4) email capture
        email = extract_email(message)
        if email:
            record_user_details(email=email, notes="Email detected in message")

        # 5) compose messages
        messages = [{"role": "system", "content": self.system_prompt()}]
        messages.extend(history_messages)
        messages.append({"role": "user", "content": message})

        # 6) draft + evaluator revise loop
        draft = self.generate(messages)

        max_revisions = 2
        eval_log = []
        for i in range(max_revisions + 1):
            ev = self.evaluator.evaluate(message, draft)
            eval_log.append({"iter": i, "score": ev["score"], "feedback": ev["feedback"]})
            log_jsonl(
                "logs/evals.jsonl",
                {"message": message, "draft": draft, "score": ev["score"], "feedback": ev["feedback"], "iter": i},
            )

            if ev["score"] >= 7:
                break

            messages.append({"role": "assistant", "content": draft})
            messages.append({"role": "user", "content": f"Revise using this feedback: {ev['feedback']}. Keep concise and professional."})
            draft = self.generate(messages)

        # 7) approved + sent notification (only if employer message) + approved email (draft now exists)
        if risk["is_employer"]:
            push("Approved response sent", draft[:700])
            log_jsonl("logs/sent.jsonl", {"message": message, "response": draft})

            send_email(
                subject="Approved response sent",
                body=f"Employer message:\n\n{message}\n\nApproved response:\n\n{draft}\n"
            )

        return draft
import json
from openai import OpenAI

class EvaluatorAgent:
    def __init__(self, model="gpt-4o-mini"):
        self.client = OpenAI()
        self.model = model

    def evaluate(self, employer_message: str, draft: str) -> dict:
        prompt = f"""
You are a strict response evaluator for a career assistant.

Score 0-10 based on:
1) Professional tone
2) Clarity
3) Completeness
4) Safety & correctness (no false claims / hallucinations)
5) Relevance to employer’s message

Return ONLY valid JSON:
{{"score": <number>, "feedback": "<short feedback>"}}

Employer message:
{employer_message}

Draft response:
{draft}
""".strip()

        res = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        txt = res.choices[0].message.content or ""
        try:
            data = json.loads(txt)
            return {
                "score": float(data.get("score", 7)),
                "feedback": str(data.get("feedback", "")),
            }
        except:
            # fail safe: do not block sending
            return {"score": 7, "feedback": "Evaluator parse failed (default pass)."}
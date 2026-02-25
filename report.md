
---

```markdown
# Career Assistant AI Agent – Short Report (3–5 pages)

## 1. Objective
The goal of this project is to build a **Career Assistant AI Agent** that can communicate with potential employers on behalf of the candidate. The system must generate professional replies using CV/profile context, self-evaluate before sending, and trigger human-in-the-loop alerts for unknown/unsafe situations. It must also demonstrate working notifications and include test cases.

---

## 2. System Design & Architecture

### 2.1 Components
1. **Primary Agent (CareerAgent)**
   - Input: employer message + conversation history
   - Context: candidate summary (`me/summary.txt`) and LinkedIn PDF (`me/linkedin.pdf`)
   - Output: draft response in professional tone

2. **Response Evaluator Agent (EvaluatorAgent)**
   - LLM-as-a-Judge
   - Scores response on: professionalism, clarity, completeness, safety/correctness, relevance
   - If below threshold: returns feedback and triggers automatic revision

3. **Unknown/Risk Detector**
   - Detects messages that the agent should not fully handle autonomously (e.g., legal advice, salary negotiation beyond threshold, unverified personal questions, deep out-of-domain technical details)
   - Triggers human intervention notification

4. **Notification Tools**
   - **Pushover**: mobile push notifications
   - **SMTP Email Tool**: optional email alerts (to satisfy “Email Notification Tool” requirement)

5. **Logging**
   - JSONL logs for traceability:
     - incoming, evaluations, sent replies, unknown alerts, leads

### 2.2 Agent Loop Design
The system runs two loops:
- **Tool loop**: if the model requests tool calls (e.g., record lead / record unknown), the tool is executed and the result is appended to the conversation.
- **Evaluation loop**:
  1) Generate draft  
  2) Evaluate (score + feedback)  
  3) If score < threshold -> revise draft and re-evaluate (limited number of revisions)  
  4) If approved -> send final reply (and notify)

### 2.3 Tool Invocation Mechanism
Tools are exposed to the LLM using structured function/tool schemas. When the model produces `tool_calls`, the application:
- Parses tool name + arguments
- Executes the local Python function
- Appends a tool result message back into the conversation
This enables reliable side effects such as notifications and logging.

---

## 3. Prompt Design

### 3.1 Primary Agent Prompt
Key rules:
- Professional, concise, polite
- Use only Summary + LinkedIn content for factual claims about the candidate
- Do not hallucinate credentials or experience
- Ask clarifying questions if required
- If the question is outside the profile or unsafe, request human intervention and log it

### 3.2 Evaluator Prompt (LLM-as-a-Judge)
The evaluator receives:
- Employer message
- Draft response
It returns strict JSON:
`{"score":0-10, "feedback":"..."}`

The threshold-based policy ensures responses improve automatically without human effort in most normal cases.

### 3.3 Unknown/Risk Detection
Detection triggers include:
- Legal/contract advice requests
- Salary negotiation beyond a defined threshold
- Questions about personal facts not present in the profile
- Deep technical questions outside domain

On trigger:
- Notify the user (push + optional email)
- Log the event
- Provide a safe response requesting clarification or human input

---

## 4. Evaluation Strategy
A hybrid strategy is used:
- **LLM judge scoring** for tone/clarity/safety/relevance (more flexible than pure rules)
- **Hard-rule triggers** for known unsafe areas (legal, salary)
This balances robustness and cost.

Logging captures evaluator scores and feedback for later review and improvement.

---

## 5. Failure Cases & Mitigations

### 5.1 Hallucination Risk
Failure: model claims unverified skills/experience  
Mitigation:
- System prompt forbids unverified claims
- Evaluator checks correctness and safety
- Unknown detector triggers alerts if not answerable from profile

### 5.2 Over-notification / Spam
Failure: notifications trigger for casual messages  
Mitigation:
- Incoming notifications can be gated by “employer intent” or a toggle
- Unknown push triggers only on unknown/unsafe conditions

### 5.3 Ambiguous Employer Messages
Failure: unclear scheduling, role details, compensation terms  
Mitigation:
- Agent asks clarifying questions
- Escalates negotiation/legal parts to human

---

## 6. Test Cases (Required)

1) **Interview Invitation**
- Input: invitation with a proposed time window
- Expected: polite acceptance and request for confirmation + availability

2) **Technical Question**
- Input: technical interview question
- Expected: clear answer, no exaggeration of experience, concise

3) **Unknown/Unsafe Question**
- Input: legal contract review + aggressive salary negotiation
- Expected: human intervention alert + safe response

All cases generate logs and notifications.

---

## 7. Reflection
This project demonstrates:
- Tool-using agent architecture
- Self-evaluating response pipelines
- Human-in-the-loop escalation for uncertainty
- External API integration for real notifications
The most important practical lesson is that reliability comes from layered controls: good prompts, evaluator feedback loops, and explicit risk triggers.

---
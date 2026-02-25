---
title: zayimhans_chatbot https://huggingface.co/spaces/zayimhan/zayimhans_chatbot
app_file: app.py
sdk: gradio
sdk_version: 4.44.1
python_version: "3.11"
---
# Career Assistant AI Agent (Career Agent + Evaluator + Notifications)

This project implements a **Career Assistant AI Agent** that replies to potential employers on behalf of the candidate, using CV/Profile context.  
It includes:
- **Primary Career Agent**
- **Evaluator / Critic Agent (LLM-as-a-Judge)** with automatic revision loop
- **Unknown / Risk detection** with human-in-the-loop alerts
- **Mobile notifications** via **Pushover**
- **Email notifications** via **SMTP** (optional but included)
- **Logs** (JSONL) for incoming messages, evaluations, sent replies, and unknown events
- **3 required test cases** via script

---

## Architecture Overview

### High-level Flow (Mermaid)
```mermaid
flowchart TD
    A[Employer Message] --> B[CareerAgent Draft Reply]
    B --> C[EvaluatorAgent Score & Feedback]
    C -->|score >= threshold| D[Approved Reply]
    C -->|score < threshold| E[Auto Revision Loop]
    E --> B

    D --> F[Risk/Unknown Detector]
    F -->|unknown/unsafe| G[Human Intervention Alert]
    F -->|ok| H[Send Reply]

    A --> N[Mobile Notification: New Msg]
    D --> M[Mobile Notification: Approved Reply]
    G --> O[Mobile/Email Notification: Unknown/Unsafe]

    H --> L[Logs: incoming/evals/sent]
    G --> K[Logs: unknown]

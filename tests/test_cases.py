import os
from dotenv import load_dotenv
load_dotenv(override=True)


from career_agent.agents.career_agent import CareerAgent

agent = CareerAgent(model="gpt-4o-mini")

H = []  # no history for simple test

cases = [
    ("Interview invitation",
     "Hi Zayimhan, we'd like to invite you to an interview next week. Are you available on Tuesday or Wednesday?"),

    ("Technical question",
     "Can you explain how you would design a scalable notification service? Please include key components and trade-offs."),

    ("Unknown/unsafe question (salary/legal)",
     "We can offer 120000 USD base + equity. Can you negotiate to 150000 and review the contract terms for me?")
]

for title, msg in cases:
    print("\n" + "="*80)
    print("CASE:", title)
    print("Q:", msg)
    ans = agent.reply(msg, H)
    print("A:", ans)
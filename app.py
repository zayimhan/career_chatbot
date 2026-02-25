import os, sys
sys.path.insert(0, os.path.dirname(__file__))

import gradio as gr
from dotenv import load_dotenv
load_dotenv()

from utils.history import gradio_history_to_openai
from agents.career_agent import CareerAgent

agent = CareerAgent(model="gpt-4o-mini")

def chat(message, history):
    hist_msgs = gradio_history_to_openai(history)
    return agent.reply(message, hist_msgs)

demo = gr.ChatInterface(chat)

if __name__ == "__main__":
    demo.launch()
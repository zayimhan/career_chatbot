import os
from dotenv import load_dotenv
import gradio as gr

# ✅ ENV yükle (CareerAgent'ten önce!)
load_dotenv()

from career_agent.utils.history import gradio_history_to_openai
from career_agent.agents.career_agent import CareerAgent

agent = CareerAgent(model="gpt-4o-mini")

def chat(message, history):
    hist_msgs = gradio_history_to_openai(history)
    return agent.reply(message, hist_msgs)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    gr.ChatInterface(chat).launch(server_name="0.0.0.0", server_port=port)
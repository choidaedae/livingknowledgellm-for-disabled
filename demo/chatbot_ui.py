import openai
from getpass import getpass
from typing import Optional
import gradio as gr

openai.api_key = getpass('Enter your OpenAI API Key: ')

class Chat:

    def __init__(self, system: Optional[str] = None):
        self.system = system
        self.messages = []
        
        if system is not None:
            self.messages.append({
                "role": "system",
                "content": system
            })

    def prompt(self, content: str) -> str:
          self.messages.append({
              "role": "user",
              "content": content
          })
          response = openai.ChatCompletion.create(
              model="gpt-3.5-turbo",
              messages=self.messages
          )
          response_content = response["choices"][0]["message"]["content"]
          self.messages.append({
              "role": "assistant",
              "content": response_content
          })
          return response_content
      
chat = Chat(system="You are a helpful assistant.") # Define the system prompt

def respond(message, chat_history):
    bot_message = chat.prompt(content=message)
    chat_history.append((message, bot_message))
    return "", chat_history # chat 기록을 저장 가능, 추후 활용 가능


with gr.Blocks() as demo:
    chatbot = gr.Chatbot()
    msg = gr.Textbox()
    clear = gr.Button("Clear")

    msg.submit(respond, [msg, chatbot], [msg, chatbot])
    clear.click(lambda: None, None, chatbot, queue=False)

demo.launch(debug=True)
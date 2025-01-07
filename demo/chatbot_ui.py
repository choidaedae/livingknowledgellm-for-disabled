import os
import openai
from typing import Optional
import gradio as gr
from datetime import datetime
import base64

# 프롬프트 읽어오기
with open("../prompts/v2.2.txt", "r", encoding="utf-8") as f:
    system_prompt = f.read()

openai.api_key = os.environ.get("OPENAI_API_KEY")

class Chat:
    def __init__(self, system: Optional[str] = None):
        self.system = system
        self.messages = []
        self.log_file = None
        
        if system is not None:
            self.messages.append({
                "role": "system",
                "content": system
            })

    def prompt(self, content: str) -> str:
        self.messages.append({"role": "user", "content": content})
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=self.messages
        )
        response_content = response["choices"][0]["message"]["content"]
        self.messages.append({"role": "assistant", "content": response_content})
        self.save_log(content, response_content)
        return response_content

    def save_log(self, user_message: str, bot_message: str):
        if self.log_file is None:
            now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            self.log_file = f"상담_{now}.txt"
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(f"User: {user_message}\n")
            f.write(f"Bot: {bot_message}\n\n")

    def clear_log(self):
        self.messages = []
        self.log_file = None

chat = Chat(system=system_prompt)

def respond(message, chat_history):
    import base64

    # 이미지 경로
    bot_profile_path = "../assets/bot_profile.png"
    
    # 이미지를 Base64로 인코딩
    with open(bot_profile_path, "rb") as f:
        encoded_image = base64.b64encode(f.read()).decode("utf-8")

    # 이미지와 텍스트를 같은 줄에 표시하기 위한 HTML/CSS
    image_html = f"""
    <div style="display: flex; align-items: center;">
        <img src='data:image/png;base64,{encoded_image}' 
             style='max-width: 30px; max-height: 30px; margin-right: 10px;' 
             alt='bot_profile'/>
        <span>{chat.prompt(content=message)}</span>
    </div>
    """

    # 메시지 기록 업데이트
    chat_history.append({"role": "user", "content": message, "image": "../assets/user_profile.png"})
    chat_history.append({"role": "assistant", "content": image_html})

    return "", chat_history


def download_log():
    if chat.log_file and os.path.exists(chat.log_file):
        return chat.log_file
    return None

def clear_chat(chat_history):
    chat.clear_log()
    return []

# Gradio Blocks UI 구성
with gr.Blocks() as demo:
    with gr.Row():
        gr.Markdown("# MoodBin - 당신의 감정을 공유하세요 🌈")
        #gr.Image(value="../assets/logo.png", shape="square", label=None, elem_id="logo", interactive=False)

    gr.Markdown("한국고등교육재단 인재림 3기 (황경서, 박소혜, 배서현, 최대현) - SOUL Project의 연구 결과물입니다.")

    chatbot = gr.Chatbot(type='messages')  # 'messages' 타입 사용
    msg = gr.Textbox(label="메시지를 입력하세요", placeholder="무엇이든 물어보세요!")
    download_output = gr.File(label="채팅 로그")

    with gr.Row():
        submit_btn = gr.Button("보내기", variant="primary")
        clear_btn = gr.Button("채팅 비우기", variant="secondary")
        download_btn = gr.Button("채팅 로그 다운로드", variant="success")

    # 이벤트 연결
    msg.submit(respond, [msg, chatbot], [msg, chatbot])
    submit_btn.click(respond, [msg, chatbot], [msg, chatbot])
    clear_btn.click(clear_chat, inputs=[chatbot], outputs=chatbot)
    download_btn.click(download_log, inputs=None, outputs=download_output)

demo.launch(debug=True, share=True)

import gradio as gr
import openai
from datetime import datetime
import base64
import os
import json
from typing import Optional
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()
# 프롬프트 읽어오기
with open("../prompts/v2.2.txt", "r", encoding="utf-8") as f:
    system_prompt = f.read()

openai.api_key = os.environ.get("OPENAI_API_KEY")

# 심리검사 완료 상태 플래그
is_test_completed = [False]  # 상태를 저장하는 플래그

# CES-D 문항 정의
questions = [
    "비교적 잘 지냈다.",
    "상당히 우울했다.",
    "모든 일들이 힘들게 느껴졌다.",
    "잠을 설쳤다(잠을 잘 이루지 못했다).",
    "세상에 홀로 있는 듯한 외로움을 느꼈다.",
    "큰 불만 없이 생활했다.",
    "사람들이 나에게 차갑게 대하는 것 같았다.",
    "마음이 슬펐다.",
    "사람들이 나를 싫어하는 것 같았다.",
    "도무지 뭘 해 나갈 엄두가 나지 않았다."
]

# 심리검사 결과 처리 함수
def validate_and_translate(*responses):
    if None in responses:
        return "⚠️ 모든 문항에 답변하세요!", gr.update(visible=True), gr.update(visible=False), gr.update(visible=False)

    # 응답 결과를 기반으로 점수 계산
    translation = [[1,0,0,0,0,1,0,0,0,0],[0,1,1,1,1,0,1,1,1,1]]
    print("response", responses)
    total_score = sum([translation[0 if response=="아니다" else 1][index] for index, response in enumerate(responses)])

    if total_score < 3:
        result = "우울 관련 정서적 문제를 호소하는 정도가 일반 사람들과 비슷한 수준입니다."
        success_message = True
    else:
        result = "우울과 관련된 증상들을 유의한 수준으로 보고하였습니다. 스트레스가 가중되면, 우울 증상이 확산될 수 있으니 주의가 필요합니다."
        success_message = False

    # 메시지 확인 후에 화면 전환
    return (
        f"총 점수: {total_score}\n해석: {result}",
        gr.update(visible=True),  # 결과 메시지 표시
        gr.update(visible=False), # 심리검사 UI 숨김
        gr.update(visible=True)  # 확인 버튼 표시
    )

def on_confirm_click():
    return gr.update(visible=False), gr.update(visible=True)  # 채팅 UI 표시

# ChatGPT 클래스
class Chat:
    def __init__(self, system: Optional[str] = None):
        self.system = system
        self.messages = []
        self.log_file = None

        if system is not None:
            self.messages.append({"role": "system", "content": system})

    def prompt(self, content: str) -> str:
        self.messages.append({"role": "user", "content": content})
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=self.messages
        )
        response_content = response["choices"][0]["message"]["content"]
        self.messages.append({"role": "assistant", "content": response_content})
        self.save_log()
        return response_content

    def save_log(self):
        """현재 채팅 기록을 JSON 파일로 저장"""
        if self.log_file is None:
            now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            self.log_file = f"chat_log_{now}.json"
        with open(self.log_file, "w", encoding="utf-8") as f:
            json.dump(self.messages, f, ensure_ascii=False, indent=2)

    def load_log(self, file_path: str):
        """JSON 파일에서 채팅 기록을 불러와 복원"""
        with open(file_path, "r", encoding="utf-8") as f:
            self.messages = json.load(f)

    def clear_log(self):
        self.messages = []
        with open(self.log_file, "w", encoding="utf-8") as f:
            f.write("")  # 파일 비우기

chat = Chat(system=system_prompt)
# ChatGPT 응답 처리 함수
def respond(message, chat_history):
    # ChatGPT 응답 처리
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
    """현재 채팅 기록 JSON 파일 다운로드"""
    if chat.log_file and os.path.exists(chat.log_file):
        return chat.log_file
    return None

def load_chat(file):
    """저장된 채팅 기록을 불러와 UI에 반영"""
    chat.load_log(file.name)
    chat_history = []
    for msg in chat.messages:
        if msg["role"] == "user":
            chat_history.append({"role": "user", "content": msg["content"], "image": "../assets/user_profile.png"})
        elif msg["role"] == "assistant":
            chat_history.append({"role": "assistant", "content": msg["content"], "image": "../assets/bot_profile.png"})
    return chat_history

def clear_chat(chat_history):
    """채팅 기록 초기화"""
    chat.clear_log()
    return []


# Gradio UI 구성
with gr.Blocks() as demo:
    # 검사 UI
    with gr.Tab("CES-D 검사", visible=True) as test_ui:
        gr.Markdown("""### CESD-10-D 우울 척도 검사

아래의 문항을 잘 읽으신 후, 지난 1주 동안 당신이 느끼고 행동한 것을 가장 잘 나타낸다고 생각되는 답변에 표시하여 주십시오. 한 문항도 빠짐없이 답해 주시기 바랍니다. 
""")
        response_inputs = []
        for question in questions:
            response_inputs.append(gr.Radio(choices=["아니다", "그렇다"], label=question))

        submit_btn = gr.Button("제출")
        result = gr.Textbox(label="검사 결과")
        confirm_btn = gr.Button("확인", visible=False)

    # 채팅 UI
    with gr.Column(visible=False) as chat_ui:
        with gr.Row():
            with gr.Column():
                gr.Markdown("# MoodBin - 당신의 감정을 공유하세요 🌈")

                gr.Markdown("한국고등교육재단 인재림 3기 (황경서, 박소혜, 배서현, 최대현) - SOUL Project의 연구 결과물입니다.")

                chatbot = gr.Chatbot(type='messages')  # 'messages' 타입 사용
                msg = gr.Textbox(label="메시지를 입력하세요", placeholder="무엇이든 물어보세요!")
                load_file = gr.File(label="채팅 불러오기")
                download_output = gr.File(label="채팅 로그 다운로드")

                with gr.Row():
                    clear_btn = gr.Button("채팅 비우기", variant="secondary")
                    download_btn = gr.Button("채팅 로그 다운로드", variant="success")

                # 이벤트 연결
                msg.submit(respond, [msg, chatbot], [msg, chatbot])
                clear_btn.click(clear_chat, inputs=[chatbot], outputs=chatbot)
                download_btn.click(download_log, inputs=None, outputs=download_output)
                load_file.upload(load_chat, inputs=[load_file], outputs=[chatbot])  # 채팅 로그 불러오기
            # 명상 및 요가 링크를 제공하는 사이드바 추가
            with gr.Column(scale=0.3):
                gr.Markdown("""## 🌿 명상 & 요가

스트레스를 관리하고 마음의 평화를 찾는 데 도움이 되는 리소스를 확인하세요:

- [Headspace 명상 가이드](https://www.headspace.com/)
- [Down Dog 요가 앱](https://www.downdogapp.com/)
- [Calm: 명상과 수면](https://www.calm.com/)

""")
    # 심리검사 결과 및 UI 업데이트
    submit_btn.click(
        validate_and_translate,
        inputs=response_inputs,
        outputs=[result, test_ui, chat_ui, confirm_btn],
    )

    confirm_btn.click(
        on_confirm_click,
        inputs=[],
        outputs=[test_ui, chat_ui],
    )

demo.launch(debug=True, share=True)

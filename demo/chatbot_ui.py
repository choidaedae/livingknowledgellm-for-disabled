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
with open("../prompts/v3.txt", "r", encoding="utf-8") as f:
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

# -------------------------------------------------------------
# 1) 상담 스타일 프롬프트를 만드는 함수 (사용자 옵션별로 다르게 설정)
# -------------------------------------------------------------
def personalize_prompt(advice_amount, speech_style, answer_length, tension):
    """
    사용자가 선택한 상담 스타일 옵션을 바탕으로
    system_prompt 앞에 추가될 프롬프트 문자열을 만들어서 반환한다.
    """
    # Example text settings for each option (customize as needed)
    advice_text = {
        "조금": "Focus on understanding and empathizing with the user, providing minimal advice unless specifically requested.",
        "많이": "Actively provide advice and solutions, while remaining empathetic and approachable."
    }
    speech_style_text = {
        "부드럽고 친근하게": "Use a warm, casual tone, making the user feel as though they're talking to a close friend.",
        "다소 격식 있게": "Maintain a respectful and polite tone, while still showing empathy and understanding."
    }
    answer_length_text = {
        "짧게": "Keep responses brief and focused, limiting answers to one or two sentences.",
        "중간": "Provide responses of moderate length, balancing detail with clarity.",
        "길게": "Offer detailed and comprehensive responses, ensuring all aspects of the user's concerns are addressed."
    }
    tension_text = {
        "낮게": "Maintain a calm and soothing energy to help the user feel at ease.",
        "중간": "Keep a balanced and neutral energy to engage naturally with the user.",
        "높게": "Adopt an enthusiastic and uplifting energy to make the conversation lively and engaging."
    }

    
    # 맞춤형 프롬프트 생성
    personalized = (
        f"The chatbot should provide a conversational experience tailored to the user's preferences. "
        f"Please adhere to the following style:\n"
        f"- Advice Level: {advice_text[advice_amount]}\n"
        f"- Speech Style: {speech_style_text[speech_style]}\n"
        f"- Response Length: {answer_length_text[answer_length]}\n"
        f"- Energy Level: {tension_text[tension]}\n\n"
        f"Context:\n"
        f"This chatbot is designed to support users in their 20s and 30s dealing with emotional challenges, "
        f"work-related stress, and personal issues. It should engage users as a friendly companion, mimicking the tone "
        f"of a chat on KakaoTalk. All responses should feel natural, empathetic, and conversational, avoiding repetition "
        f"or overly formal expressions.\n\n"
        f"Example Scenario:\n"
        f"User: 오늘 너무 힘들었어. 상사가 너무 힘들게 해서 머리 터질 것 같아.\n"
        f"Chatbot: 무슨 일이야? 오늘 상사랑 어떤 일이 있었길래 그래? 내가 들어줄게."
        f"""Follow the basic guidelines below, but if there are any conflicting instructions with prior commands, prioritize following the prior commands. Specifically, "advice level" and "speech style" should strictly adhere to the previous instructions."""
    )
    return personalized

# -------------------------------------------------------------
# 2) 심리검사 결과 처리 함수
# -------------------------------------------------------------
def validate_and_translate(*responses):
    if None in responses:
        return "⚠️ 모든 문항에 답변하세요!", gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)

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
        gr.update(visible=True),   # 검사 결과 표시
        gr.update(visible=False),  # 검사 UI 숨김
        gr.update(visible=True),   # 검사 "확인" 버튼 표시
        gr.update(visible=False)   # 스타일 선택 탭은 아직 숨김
    )

# -------------------------------------------------------------
# 3) '검사 결과 확인' -> 스타일 선택 탭 열어주는 함수
# -------------------------------------------------------------
def on_confirm_click():
    # test_ui(검사 탭)는 숨기고, style_ui(스타일 선택 탭)는 보여줌
    # chat_ui는 아직 숨긴 상태
    return (
        gr.update(visible=False),  # test_ui
        gr.update(visible=True),   # style_ui
        gr.update(visible=False)   # chat_ui
    )

# -------------------------------------------------------------
# 4) 스타일 최종 확정 -> 챗봇 UI 열어주기
# -------------------------------------------------------------
def apply_personalization(advice_amount, speech_style, answer_length, tension):
    # 새로운 프롬프트 생성
    new_prompt = personalize_prompt(advice_amount, speech_style, answer_length, tension)
    # 기존 system_prompt 앞에 붙여서 chat.system 업데이트
    final_prompt = new_prompt + "\n" + system_prompt

    # 기존 chat 객체를 버리고 새롭게 생성
    global chat
    chat = Chat(system=final_prompt)
    print(chat.system)

    # style_ui를 숨기고 chat_ui를 보여준다
    return gr.update(visible=False), gr.update(visible=True)

# -------------------------------------------------------------
# 5) ChatGPT 클래스
# -------------------------------------------------------------
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
            model="gpt-4o",
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
        if self.log_file:
            with open(self.log_file, "w", encoding="utf-8") as f:
                f.write("")  # 파일 비우기

# -------------------------------------------------------------
# 6) 챗봇 함수들
# -------------------------------------------------------------

# chat = Chat(system=system_prompt)

def respond(message, chat_history):
    # ChatGPT 응답 처리
    bot_profile_path = "../assets/bot_profile.png"
    with open(bot_profile_path, "rb") as f:
        encoded_image = base64.b64encode(f.read()).decode("utf-8")

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

# -------------------------------------------------------------
# 7) Gradio UI 구성
# -------------------------------------------------------------
with gr.Blocks() as demo:
    # 1) 검사 UI
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

    # 2) 상담 스타일 선택 UI (새 탭 추가, 초기에는 숨김)
    with gr.Column("상담 스타일 선택", visible=False) as style_ui:
        # with gr.Column():  # Column으로 묶어서 UI 컴포넌트가 제대로 렌더링되도록 수정
        gr.Markdown("## 어떤 상담 스타일을 원하시나요?")
        advice_amount = gr.Radio(["조금", "많이"], label="조언 제공")
        speech_style = gr.Radio(["부드럽고 친근하게", "다소 격식 있게"], label="말투")
        answer_length = gr.Radio(["짧게", "중간", "길게"], label="답변 길이")
        tension = gr.Radio(["낮게", "중간", "높게"], label="텐션")

        style_confirm_btn = gr.Button("스타일 지정")


    # 3) 채팅 UI
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

            # 명상 및 요가 링크를 제공하는 사이드바
            with gr.Column(scale=0.3):
                gr.Markdown("""
## 🌿 명상 & 요가
- [**Headspace**](https://www.headspace.com/)
- [**Down Dog**](https://www.downdogapp.com/)
- [**Calm**](https://www.calm.com/)
- [**Insight Timer**](https://insighttimer.com/)
- [**Smiling Mind**](https://www.smilingmind.com.au/)

## ☎️ 긴급전화번호
- **정신건강위기상담**: 1577-0199  
- **정신건강복지센터**: 1668-2919  
- **한국생명의전화**: 1588-9191  
- **청소년 상담 전화**: 1388  
- **여성 긴급전화**: 1366  
""")

    # --------------------------------------------
    # 연결: 검사 결과 제출 -> 결과 표시 -> 확인 버튼 누르면 스타일 탭 표시
    # --------------------------------------------
    submit_btn.click(
        validate_and_translate,
        inputs=response_inputs,
        outputs=[result,               # f"총 점수"
                 test_ui,             # 검사 탭
                 chat_ui,             # 챗봇 UI(숨김 처리용)
                 confirm_btn,         # 검사 결과 확인 버튼
                 style_ui],           # 스타일 선택 탭(숨김 처리용)
    )

    # confirm_btn -> 검사 탭 숨기고, 스타일 탭 보이게, 챗봇은 숨김
    confirm_btn.click(
        on_confirm_click,
        inputs=[],
        outputs=[test_ui, style_ui, chat_ui],
    )

    # 스타일 탭에서 스타일 확정 버튼 -> 프롬프트 업데이트 후, 챗봇 UI 열기
    style_confirm_btn.click(
        apply_personalization,
        inputs=[advice_amount, speech_style, answer_length, tension],
        outputs=[style_ui, chat_ui]
    )

demo.launch(debug=True, share=True)

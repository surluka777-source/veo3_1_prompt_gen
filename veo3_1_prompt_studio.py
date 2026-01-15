# pip install streamlit google-genai pydantic


import streamlit as st
import os
import json
from datetime import datetime
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# --- 1. 페이지 설정 (심플 모드) ---
st.set_page_config(
    page_title="Veo 3.1 Prompt Studio",
    page_icon="🎬",
    layout="wide"
)

# --- 2. 데이터 스키마 정의 (변경 없음) ---
class ProjectMeta(BaseModel):
    title: str = Field(description="Snake case title of the video idea.")
    created_at: str

class VideoElements(BaseModel):
    subject: str = Field(description="The main character or object, A detailed visual description of the main subject.")
    action: str = Field(description="What the subject is doing.")
    context: str = Field(description="The environment, lighting, and time of day.")
    cinematography: str = Field(description="Camera angles, movement, and lens choices.")
    style: str = Field(description="Visual style, color palette, and artistic reference.")

class AudioElements(BaseModel):
    ambient_music: str = Field(description="Background music mood and instruments.")
    sfx: str = Field(description="Specific sound effects synchronous with action.")
    dialogue: str = Field(description="Spoken words or voiceover. Empty if none.")

class TechnicalSettings(BaseModel):
    aspect_ratio: str = Field(description="e.g., 16:9, 9:16")
    duration_sec: int = Field(description="Duration in seconds, typically 8.")
    resolution: str = Field(description="e.g. 720p, 1080p")

class VeoData(BaseModel):
    project_meta: ProjectMeta
    video_5_elements: VideoElements
    audio_3_elements: AudioElements
    technical_settings: TechnicalSettings

# --- 3. Gemini 서비스 로직 (변경 없음) ---
def generate_veo_structure(api_key, user_title, user_prompt):
    client = genai.Client(api_key=api_key)

    system_instruction = """
    You are a professional Prompt Architect for Google Veo 3.1.
    Your task is to take a raw user idea and expand it into a rich, detailed, cinematic structure.
    
    **LANGUAGE RULE:** Generate all content in the SAME language as the user input.

    Expand into 8 narrative elements:
    1. Subject: Appearance, clothing, texture.
    2. Action: Movement, physics.
    3. Context: Environment, lighting, weather.
    4. Cinematography: Camera type, angles, movement.
    5. Style: Art style, film stock, color grading.
    6. Ambient Music: Mood, tempo.
    7. SFX: Diegetic sounds.
    8. Dialogue: Optional.

    Infer technical settings suitable for the content.
    Return strictly JSON.
    """

    try:
        # 모델명을 실제 사용 가능한 모델(gemini-3-pro-preview 등)로 설정하세요.
        response = client.models.generate_content(
            model="gemini-3-pro-preview", 
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=VeoData,
                temperature=0.9   # 창의성 조절 (0.0-2.0) 높을수록 창의성이 올라간다
            )
        )
        
        parsed_data = response.parsed
        parsed_data.project_meta.created_at = datetime.now().isoformat()
        parsed_data.project_meta.title = user_title
        
        return parsed_data

    except Exception as e:
        st.error(f"Gemini API Error: {str(e)}")
        return None

# --- 4. 메인 UI 로직 (심플 버전) ---
def main():
    # [상단] 타이틀 및 설명
    st.title("🎬 Veo 3.1 Prompt Studio")
    st.markdown("""
    Google Veo 3.1 비디오 생성 모델을 위한 **JSON 구조화 도구**입니다.
    간단한 아이디어를 입력하면 AI가 **5가지 영상 요소**와 **3가지 오디오 요소**로 확장해줍니다.
    """)
    
    st.divider()

    # [상단] API 키 입력 (메인 화면 배치)
    api_key = os.environ.get("API_KEY")
    if not api_key:
        api_key = st.text_input("🔑 Enter Google API Key", type="password", help="AI Studio에서 발급받은 키를 입력하세요.")
    
    if not api_key:
        st.info("👆 위 칸에 API Key를 입력해야 작동합니다.")
        st.stop()

    # [초기 상태 설정]
    if "veo_data" not in st.session_state:
        st.session_state.veo_data = VeoData(
            project_meta=ProjectMeta(title="untitled_project", created_at=datetime.now().isoformat()),
            video_5_elements=VideoElements(subject="", action="", context="", cinematography="", style=""),
            audio_3_elements=AudioElements(ambient_music="", sfx="", dialogue=""),
            technical_settings=TechnicalSettings(aspect_ratio="16:9", duration_sec=8, resolution="720p")
        )

    # [입력 섹션]
    col_input1, col_input2 = st.columns([1, 2])
    
    with col_input1:
        title_input = st.text_input("Project Name (File Name)", value=st.session_state.veo_data.project_meta.title)
    
    with col_input2:
        prompt_input = st.text_area("Video Idea Prompt", height=100, placeholder="예: 비 오는 사이버펑크 도시를 걷는 로봇...")
    
    # 버튼 (전체 너비 사용 안 함, 기본 스타일)
    if st.button("✨ 구조화 실행 (Structure Prompt)", type="primary"):
        if not title_input or not prompt_input:
            st.warning("제목과 내용을 모두 입력해주세요.")
        else:
            with st.spinner("AI가 프롬프트를 설계 중입니다..."):
                result = generate_veo_structure(api_key, title_input, prompt_input)
                if result:
                    st.session_state.veo_data = result
                    st.rerun()

    st.divider()

    # [에디터 섹션] 2단 컬럼
    col_left, col_right = st.columns([1, 1])

    # 왼쪽: Video Elements
    with col_left:
        st.subheader("🎥 Video Elements (5)")
        v_data = st.session_state.veo_data.video_5_elements
        
        new_subject = st.text_area("1. Subject (피사체)", value=v_data.subject, height=120)
        new_action = st.text_area("2. Action (행동)", value=v_data.action, height=120)
        new_context = st.text_area("3. Context (배경)", value=v_data.context, height=120)
        new_cine = st.text_area("4. Cinematography (촬영)", value=v_data.cinematography, height=120)
        new_style = st.text_area("5. Style (스타일)", value=v_data.style, height=120)

        # 상태 업데이트
        st.session_state.veo_data.video_5_elements.subject = new_subject
        st.session_state.veo_data.video_5_elements.action = new_action
        st.session_state.veo_data.video_5_elements.context = new_context
        st.session_state.veo_data.video_5_elements.cinematography = new_cine
        st.session_state.veo_data.video_5_elements.style = new_style

    # 오른쪽: Audio & Tech
    with col_right:
        st.subheader("🔊 Audio Elements (3)")
        a_data = st.session_state.veo_data.audio_3_elements
        
        new_music = st.text_area("1. Ambient/Music (배경음)", value=a_data.ambient_music, height=100)
        new_sfx = st.text_area("2. SFX (효과음)", value=a_data.sfx, height=100)
        new_dialogue = st.text_area("3. Dialogue (대사)", value=a_data.dialogue, height=100)

        st.session_state.veo_data.audio_3_elements.ambient_music = new_music
        st.session_state.veo_data.audio_3_elements.sfx = new_sfx
        st.session_state.veo_data.audio_3_elements.dialogue = new_dialogue

        st.markdown("### ⚙️ Settings")
        t_data = st.session_state.veo_data.technical_settings

        # [안전장치가 적용된 Selectbox 코드]
        ar_options = ["16:9", "9:16", "1:1", "4:3", "3:4"]
        res_options = ["720p", "1080p"]

        try:
            ar_idx = ar_options.index(t_data.aspect_ratio)
        except ValueError:
            ar_idx = 0
        
        try:
            res_idx = res_options.index(t_data.resolution)
        except ValueError:
            res_idx = 1

        c1, c2 = st.columns(2)
        with c1:
            new_ar = st.selectbox("Aspect Ratio", ar_options, index=ar_idx)
            new_res = st.selectbox("Resolution", res_options, index=res_idx)
        with c2:
            new_dur = st.number_input("Duration (sec)", value=t_data.duration_sec, min_value=1, max_value=60)
            st.write("") # Spacer

        st.session_state.veo_data.technical_settings.aspect_ratio = new_ar
        st.session_state.veo_data.technical_settings.resolution = new_res
        st.session_state.veo_data.technical_settings.duration_sec = new_dur
        
        # 메타데이터 타이틀 동기화
        st.session_state.veo_data.project_meta.title = title_input

        st.markdown("<br>", unsafe_allow_html=True)
        
        # [다운로드 버튼]
        json_str = st.session_state.veo_data.model_dump_json(indent=2)
        safe_title = st.session_state.veo_data.project_meta.title.strip().replace(" ", "_")
        date_str = st.session_state.veo_data.project_meta.created_at.split("T")[0]
        file_name = f"{safe_title}_{date_str}.json"

        st.download_button(
            label="⬇️ Download JSON File",
            data=json_str,
            file_name=file_name,
            mime="application/json",
            use_container_width=True,
            type="primary"
        )

if __name__ == "__main__":
    main()
import os
import streamlit as st
from groq import Client
from gtts import gTTS
from io import BytesIO
import speech_recognition as sr

# ---------------- GROQ CLIENT ----------------
client = Client(api_key=os.getenv("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"))

# ---------------- AI RESPONSE ----------------
def ai_response(prompt, role="plaintiff"):
    legal_prompt = f"""
You are a skilled {role} lawyer. Reply to the opponent argument using:
- Relevant IPC sections
- Past legal case references
- Strong legal reasoning
- Clear structured argument

{prompt}
"""
    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": legal_prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

# ---------------- SPEECH TO TEXT ----------------
def speak_into_text_box(key):
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            st.info("🎤 Listening...")
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)
            text = recognizer.recognize_google(audio)
            
            # Append new speech to the current text in session state
            if f"{key}_voice_input" not in st.session_state:
                st.session_state[f"{key}_voice_input"] = text
            else:
                st.session_state[f"{key}_voice_input"] += " " + text

    except sr.UnknownValueError:
        st.error("❌ Could not understand the speech.")
    except sr.RequestError as e:
        st.error(f"❌ Speech recognition service error: {e}")

# ---------------- TEXT TO SPEECH ----------------
def text_to_speech(text):
    tts = gTTS(text)
    mp3_fp = BytesIO()
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    st.audio(mp3_fp, format="audio/mp3")

# ---------------- JUDGE VERDICT ----------------
def judge_verdict(case_description, arg_a, arg_b):
    prompt = f"""
You are a courtroom judge. Analyze the case and both sides and give a fair final judgment.

Case Description:
{case_description}

Lawyer A: {arg_a}
Lawyer B: {arg_b}

Final Judgment:"""
    return ai_response(prompt)

# ---------------- STREAMLIT APP ----------------
st.set_page_config(page_title="AI Courtroom Simulator", layout="wide")
st.title("⚖️ AI Courtroom Simulator ⚖️")

mode = st.radio("Choose Mode:", ["Courtroom Mode", "Judge Mode"])
left_col, right_col = st.columns([1, 1])

# ---------------- COURTROOM MODE ----------------
if mode == "Courtroom Mode":
    with left_col:
        st.header("Courtroom Mode⚖️")

        # Case Description
        case_description = st.text_area(
            "Enter Case Description:",
            value=st.session_state.get("case_description_voice_input", ""),
            key="case_description"
        )
        st.session_state["case_description_voice_input"] = case_description
        if st.button("🎤 Speak Case Description"):
            speak_into_text_box("case_description")

        # Initialize session state
        st.session_state.setdefault("court_output", [])
        st.session_state.setdefault("current_plaintiff_arg", "")
        st.session_state.setdefault("final_verdict", "")
        st.session_state.setdefault("opponent_argument", "")

        # Start Case
        if st.button("Start Case"):
            if case_description.strip() == "":
                st.warning("Please enter a case description.")
            else:
                st.session_state["court_output"] = [f"📜 Case Registered:\n{st.session_state['case_description_voice_input']}"]
                plaintiff_response = ai_response(f"You are the lawyer for the plaintiff. Case: {st.session_state['case_description_voice_input']}")
                st.session_state["court_output"].append(f"⚖️ Plaintiff's Lawyer (Bot):\n{plaintiff_response}")
                st.session_state["current_plaintiff_arg"] = plaintiff_response
                text_to_speech(plaintiff_response)

        # Opponent Argument
        opponent_argument = st.text_area(
            "Opponent Lawyer Argument:",
            value=st.session_state.get("opponent_argument_voice_input", ""),
            key="opponent_argument"
        )
        st.session_state["opponent_argument_voice_input"] = opponent_argument
        if st.button("🎤 Speak Opponent Argument"):
            speak_into_text_box("opponent_argument")

        if st.button("Submit Opponent Argument"):
            opponent_argument = st.session_state.get("opponent_argument_voice_input", "")
            if opponent_argument.strip() == "":
                st.warning("Opponent argument cannot be empty.")
            else:
                st.session_state["court_output"].append(f"👨‍💼 Opponent Lawyer:\n{opponent_argument}")
                reply = ai_response(f"Opponent said: {opponent_argument}\nReply as the plaintiff's lawyer defending the case.")
                st.session_state["court_output"].append(f"⚖️ Plaintiff's Lawyer (Bot):\n{reply}")
                st.session_state["current_plaintiff_arg"] = reply
                text_to_speech(reply)

        # Generate Verdict
        if st.button("Generate Final Judgment"):
            verdict = judge_verdict(
                st.session_state.get("case_description_voice_input", ""),
                st.session_state.get("current_plaintiff_arg", ""),
                st.session_state.get("opponent_argument_voice_input", "")
            )
            if st.session_state.get("final_verdict"):
                st.session_state["final_verdict"] += " " + verdict
            else:
                st.session_state["final_verdict"] = verdict
            st.session_state["court_output"].append(f"👩‍⚖️ Final Judgment:\n{verdict}")
            text_to_speech(verdict)

        # Editable Final Judgment Box
        st.subheader("Final Judgment")
        st.session_state["final_verdict"] = st.text_area(
            "Final Judgment:",
            value=st.session_state.get("final_verdict", ""),
            height=200
        )

    with right_col:
        st.header("Client's Lawyer (Bot) Arguments 💻")
        if st.session_state["current_plaintiff_arg"]:
            st.text_area("Plaintiff's Lawyer Arguments", value=st.session_state["current_plaintiff_arg"], height=200)

        st.header("Courtroom Output")
        if st.session_state["court_output"]:
            st.text_area("📄 Full Courtroom Output", value="\n\n".join(st.session_state["court_output"]), height=400)

# ---------------- JUDGE MODE ----------------
elif mode == "Judge Mode":
    with left_col:
        st.header("👩‍⚖️ Judge Mode - AI Courtroom Judge 👩‍⚖️")

        # Case Description
        judge_case = st.text_area(
            "Enter Case Description:",
            value=st.session_state.get("judge_case_voice_input", ""),
            key="judge_case"
        )
        st.session_state["judge_case_voice_input"] = judge_case
        if st.button("🎤 Speak Case Description (Judge Mode)"):
            speak_into_text_box("judge_case")

        # Lawyer A Argument
        lawyer_a_arg = st.text_area(
            "Lawyer A Argument:",
            value=st.session_state.get("lawyer_a_arg_voice_input", ""),
            key="lawyer_a_arg"
        )
        st.session_state["lawyer_a_arg_voice_input"] = lawyer_a_arg
        if st.button("🎤 Speak Lawyer A Argument"):
            speak_into_text_box("lawyer_a_arg")

        if st.button("Submit Lawyer A Argument"):
            st.session_state["judge_output"].append(f"🧑‍💼 Lawyer A: {st.session_state['lawyer_a_arg_voice_input']}")
            
        # Lawyer B Argument
        lawyer_b_arg = st.text_area(
            "Lawyer B Argument:",
            value=st.session_state.get("lawyer_b_arg_voice_input", ""),
            key="lawyer_b_arg"
        )
        st.session_state["lawyer_b_arg_voice_input"] = lawyer_b_arg
        if st.button("🎤 Speak Lawyer B Argument"):
            speak_into_text_box("lawyer_b_arg")

        if st.button("Submit Lawyer B Argument"):
            st.session_state["judge_output"].append(f"🧑‍💼 Lawyer B: {st.session_state['lawyer_b_arg_voice_input']}")
            
        # Initialize session_state
        st.session_state.setdefault("judge_output", [])
        st.session_state.setdefault("judge_final_verdict", "")

        # Generate Verdict
        if st.button("Generate Final Judgment"):
            verdict = judge_verdict(
                st.session_state.get("judge_case_voice_input", ""),
                st.session_state.get("lawyer_a_arg_voice_input", ""),
                st.session_state.get("lawyer_b_arg_voice_input", "")
            )
            if st.session_state.get("judge_final_verdict"):
                st.session_state["judge_final_verdict"] += " " + verdict
            else:
                st.session_state["judge_final_verdict"] = verdict
            st.session_state["judge_output"].append(f"👩‍⚖️ Final Judgment:\n{verdict}")
            text_to_speech(verdict)

        # Editable Final Judgment

#pip install streamlit gtts speechrecognition pyaudio groq
#cd Desktop
#$env:GROQ_API_KEY="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"
#streamlit run streamlaw.py

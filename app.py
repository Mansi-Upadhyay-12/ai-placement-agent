import streamlit as st
import streamlit.components.v1 as components
import asyncio
import os
import queue
import threading
import sys
import json
from dotenv import load_dotenv
from google.antigravity import Agent, LocalAgentConfig, CapabilitiesConfig

def text_to_speech_component(text: str):
    # Escape backslashes, single quotes, and newlines for safe JS injection
    clean_text = text.replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ").replace("\r", " ")
    html_code = f"""
    <script>
        (function() {{
            const synth = window.parent.speechSynthesis || window.speechSynthesis;
            if (synth) {{
                synth.cancel(); // Stop any ongoing playback
                const SpeechUtterance = window.parent.SpeechSynthesisUtterance || window.parent.SpeechSynthesisUtterance;
                const utterance = new SpeechUtterance('{clean_text}');
                utterance.lang = 'en-US';
                
                // Select a standard English voice if available
                const voices = synth.getVoices();
                if (voices.length > 0) {{
                    const engVoice = voices.find(v => v.lang.startsWith('en') && (v.name.includes('Google') || v.name.includes('Natural')));
                    if (engVoice) {{
                        utterance.voice = engVoice;
                    }}
                }}
                
                synth.speak(utterance);
            }}
        }})();
    </script>
    """
    components.html(html_code, height=0, width=0)

def speech_recognition_injector(enabled: bool):
    if enabled:
        html_code = """
        <script>
            (function() {
                const doc = window.parent.document;
                
                // Polling loop to find stChatInputTextArea in parent window
                const pollInterval = setInterval(() => {
                    const textArea = doc.querySelector("textarea[data-testid='stChatInputTextArea']");
                    if (textArea) {
                        clearInterval(pollInterval);
                        const container = textArea.parentNode;
                        
                        // Check if mic button is already injected
                        if (!doc.getElementById("injected-mic-btn")) {
                            const micBtn = doc.createElement("button");
                            micBtn.id = "injected-mic-btn";
                            micBtn.innerHTML = "🎤";
                            micBtn.style.position = "absolute";
                            micBtn.style.right = "60px";
                            micBtn.style.top = "8px";
                            micBtn.style.zIndex = "1000";
                            micBtn.style.background = "none";
                            micBtn.style.border = "none";
                            micBtn.style.fontSize = "20px";
                            micBtn.style.cursor = "pointer";
                            micBtn.style.color = "#6366F1";
                            micBtn.title = "Click to speak";
                            
                            container.appendChild(micBtn);
                            
                            // Initialize Web Speech Recognition in parent context
                            const SpeechRecognition = window.parent.SpeechRecognition || window.parent.webkitSpeechRecognition || window.SpeechRecognition || window.webkitSpeechRecognition;
                            if (SpeechRecognition) {
                                const recognition = new SpeechRecognition();
                                recognition.continuous = false;
                                recognition.interimResults = false;
                                recognition.lang = 'en-US';
                                
                                let isListening = false;
                                
                                micBtn.addEventListener('click', (e) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    if (isListening) {
                                        recognition.stop();
                                    } else {
                                        recognition.start();
                                    }
                                });
                                
                                recognition.onstart = () => {
                                    isListening = true;
                                    micBtn.innerHTML = "🔴";
                                    micBtn.style.color = "#EF4444";
                                    textArea.placeholder = "Listening... Speak your answer now.";
                                };
                                
                                recognition.onend = () => {
                                    isListening = false;
                                    micBtn.innerHTML = "🎤";
                                    micBtn.style.color = "#6366F1";
                                    textArea.placeholder = "Type your response here...";
                                };
                                
                                recognition.onerror = (event) => {
                                    console.error("Speech Recognition Error:", event.error);
                                    textArea.placeholder = "Error: " + event.error;
                                };
                                
                                recognition.onresult = (event) => {
                                    const transcript = event.results[0][0].transcript;
                                    textArea.value = transcript;
                                    textArea.dispatchEvent(new Event('input', { bubbles: true }));
                                };
                            } else {
                                micBtn.style.opacity = "0.3";
                                micBtn.title = "Speech recognition is not supported in this browser. Please use Chrome or Edge.";
                                micBtn.addEventListener('click', (e) => {
                                    e.preventDefault();
                                    alert("Speech recognition is not supported in this browser. Please use Chrome or Edge.");
                                });
                            }
                        }
                    }
                }, 200);
            })();
        </script>
        """
        components.html(html_code, height=0, width=0)
    else:
        # Script to remove the mic button if voice mode is disabled or page changes
        html_code = """
        <script>
            (function() {
                const doc = window.parent.document;
                const existingMic = doc.getElementById("injected-mic-btn");
                if (existingMic) {
                    existingMic.remove();
                }
            })();
        </script>
        """
        components.html(html_code, height=0, width=0)

def generate_placement_playbook():
    import json
    
    student_name = "student"
    profile_summary = "Not completed yet - visit Profile Setup to generate this."
    
    if os.path.exists("student_profile.json"):
        try:
            with open("student_profile.json", "r") as f:
                profile = json.load(f)
            student_name = profile.get("name") or "student"
            profile_summary = (
                f"**Branch**: {profile.get('branch', 'N/A')}\n\n"
                f"**Year**: {profile.get('year', 'N/A')}\n\n"
                f"**Target Job Roles**: {', '.join(profile.get('target_job_roles', []))}\n\n"
                f"**Target Companies**: {', '.join(profile.get('target_companies', []))}\n\n"
                f"**Areas of Weakness/Focus**: {profile.get('weakness') or profile.get('weak_areas') or 'N/A'}"
            )
        except Exception:
            profile_summary = "Error reading student profile."

    resume_feedback = "Not completed yet - visit Resume Review to generate this."
    if os.path.exists("resume_feedback.md"):
        try:
            with open("resume_feedback.md", "r", encoding="utf-8") as f:
                resume_feedback = f.read()
        except Exception:
            resume_feedback = "Error reading resume feedback report."

    skill_gap = "Not completed yet - visit Skill Gap Analysis to generate this."
    if os.path.exists("skill_gap_report.md"):
        try:
            with open("skill_gap_report.md", "r", encoding="utf-8") as f:
                skill_gap = f.read()
        except Exception:
            skill_gap = "Error reading skill gap report."

    interview_report = "Not completed yet - visit Mock Interview to generate this."
    if os.path.exists("interview_report.md"):
        try:
            with open("interview_report.md", "r", encoding="utf-8") as f:
                interview_report = f.read()
        except Exception:
            interview_report = "Error reading interview report."

    playbook = f"""# 🏆 Personalized Placement Playbook for {student_name.capitalize()}

This document compiles your profile details, resume feedback, skill gaps, and interview performance reports into a single cohesive guide.

---

## 📋 1. Student Profile Summary

{profile_summary}

---

## 📄 2. Resume Feedback

{resume_feedback}

---

## 📈 3. Skill Gap Analysis

{skill_gap}

---

## 🎙️ 4. Interview Debrief & Coach Notes

{interview_report}

---
Generated by AI Placement Mentor Portal.
"""
    return playbook, f"placement_playbook_{student_name.lower().replace(' ', '_')}.md"

def render_interview_report(content: str):
    import re
    
    lines = content.split("\n")
    
    current_section = "intro"
    debrief_lines = []
    verdict_lines = []
    notes_lines = []
    intro_lines = []
    
    for line in lines:
        line_strip = line.strip()
        
        # Check for section headings
        if re.search(r"^[#\s]*Panel\s+Debrief", line, re.IGNORECASE):
            current_section = "debrief"
            continue
        elif re.search(r"^[#\s]*Final\s+Verdict", line, re.IGNORECASE):
            current_section = "verdict"
            continue
        elif re.search(r"^[#\s]*Coach\s+Notes", line, re.IGNORECASE):
            current_section = "notes"
            continue
            
        if current_section == "intro":
            intro_lines.append(line)
        elif current_section == "debrief":
            debrief_lines.append(line)
        elif current_section == "verdict":
            verdict_lines.append(line)
        elif current_section == "notes":
            notes_lines.append(line)
            
    # 1. Render Intro section
    intro_text = "\n".join(intro_lines).strip()
    if intro_text:
        st.markdown(intro_text)
        
    # 2. Render Panel Debrief section
    if debrief_lines:
        st.markdown("### 🎙️ Panel Debrief")
        
        speaker_turns = []
        current_speaker = None
        current_text = []
        
        # Pattern to match e.g. **Hiring Manager**: ... or Hiring Manager: ...
        pattern = r"^\s*\**(Hiring\s+Manager|Peer\s+Engineer|Exec)\**\s*:\s*(.*)$"
        
        for line in debrief_lines:
            match = re.match(pattern, line.strip(), re.IGNORECASE)
            if match:
                if current_speaker:
                    speaker_turns.append((current_speaker, "\n".join(current_text)))
                current_speaker = match.group(1).strip()
                current_text = [match.group(2).strip()]
            else:
                if current_speaker:
                    current_text.append(line)
                else:
                    if line.strip():
                        # Treat as general intro to debrief
                        st.markdown(line)
                        
        if current_speaker:
            speaker_turns.append((current_speaker, "\n".join(current_text)))
            
        avatars = {
            "Hiring Manager": "💼",
            "Peer Engineer": "🛠️",
            "Exec": "⭐"
        }
        
        for speaker, text in speaker_turns:
            # Normalize speaker name for avatars dict lookup
            norm_speaker = "Hiring Manager"
            if "peer" in speaker.lower():
                norm_speaker = "Peer Engineer"
            elif "exec" in speaker.lower():
                norm_speaker = "Exec"
                
            avatar = avatars.get(norm_speaker, "🤖")
            
            with st.chat_message(norm_speaker, avatar=avatar):
                st.markdown(f"**{norm_speaker}**\n\n{text.strip()}")
                
    # 3. Render Final Verdict inside a special card
    if verdict_lines:
        verdict_text = "\n".join(verdict_lines).strip()
        st.markdown("### 🏆 Final Verdict")
        st.markdown(f'<div class="verdict-card">{verdict_text}</div>', unsafe_allow_html=True)
        
    # 4. Render Coach Notes inside a special card
    if notes_lines:
        notes_text = "\n".join(notes_lines).strip()
        st.markdown("### 💡 Coach Notes")
        st.markdown(f'<div class="notes-card">{notes_text}</div>', unsafe_allow_html=True)

# Load environment variables
load_dotenv(os.path.expanduser("~/.env"))
load_dotenv()

# Verify API key
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    st.error("Error: GEMINI_API_KEY is not set. Please configure it in C:\\Users\\mansi\\.env or your environment variables.")
    st.stop()

# Helper bridge to handle the async Agent session in a background thread
class AsyncAgentBridge:
    def __init__(self, system_instructions, tools, primer_prompt):
        self.system_instructions = system_instructions
        self.tools = tools
        self.primer_prompt = primer_prompt
        self.input_queue = queue.Queue()
        self.output_queue = queue.Queue()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def _run_loop(self):
        asyncio.run(self._async_main())

    async def _async_main(self):
        try:
            config = LocalAgentConfig(
                system_instructions=self.system_instructions,
                tools=self.tools,
                capabilities=CapabilitiesConfig(enable_subagents=False, enabled_tools=[]),
                api_key=api_key,
                model="gemini-2.5-flash-lite"
            )
            async with Agent(config) as agent:
                # Send initial greeting primer
                response = await agent.chat(self.primer_prompt)
                response_text = ""
                async for token in response:
                    response_text += token
                self.output_queue.put(response_text)

                loop = asyncio.get_running_loop()
                while True:
                    user_msg = await loop.run_in_executor(None, self.input_queue.get)
                    if user_msg is None:
                        break
                    response = await agent.chat(user_msg)
                    response_text = ""
                    async for token in response:
                        response_text += token
                    self.output_queue.put(response_text)
        except Exception as e:
            import traceback
            err_msg = f"Agent Error: {str(e)}\n\n{traceback.format_exc()}"
            self.output_queue.put(err_msg)

# Define custom tools for the web app
def save_student_profile(branch: str, year: str, target_job_roles: list[str], target_companies: list[str], weakness: str) -> str:
    import json
    profile = {
        "branch": branch,
        "year": year,
        "target_job_roles": target_job_roles,
        "target_companies": target_companies,
        "weakness": weakness
    }
    with open("student_profile.json", "w") as f:
        json.dump(profile, f, indent=4)
    return "Profile saved successfully."

def save_resume_feedback(feedback: str) -> str:
    with open("resume_feedback.md", "w", encoding="utf-8") as f:
        f.write(feedback)
    return "Feedback saved successfully to resume_feedback.md."

def log_guardrail_violation(inappropriate_question: str, reason: str) -> str:
    with open("guardrail_log.txt", "a", encoding="utf-8") as f:
        f.write(f"Flagged Question: '{inappropriate_question}'\nReason: {reason}\n{'-'*40}\n")
    return "Guardrail violation logged."

# Web UI Setup
st.set_page_config(page_title="AI Placement Mentor Portal", layout="wide", page_icon="🎓")

# Dynamic modern styling with Outfit/Inter fonts, custom gradients, and shadows
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800&family=Inter:wght@300;400;500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3 {
        font-family: 'Outfit', sans-serif;
        background: linear-gradient(135deg, #6366F1, #10B981);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
    }
    
    .stButton>button {
        background-color: #6366F1;
        color: white;
        border-radius: 8px;
        font-family: 'Outfit', sans-serif;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #4F46E5;
        transform: translateY(-2px);
    }
    
    .approval-card {
        background-color: #1E293B;
        border-left: 5px solid #F59E0B;
        border-radius: 8px;
        padding: 20px;
        margin: 20px 0;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    
    .verdict-card {
        background-color: #0F172A;
        border-left: 5px solid #10B981;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        color: #E2E8F0;
    }

    .notes-card {
        background-color: #0F172A;
        border-left: 5px solid #6366F1;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        color: #E2E8F0;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎓 AI Placement Mentor Portal")

# Calculate offline recommendation
import json
recommendation = "Profile Setup"
rec_reason = "you have not set up your profile yet."
weakness = ""

if os.path.exists("student_profile.json"):
    try:
        with open("student_profile.json", "r") as f:
            profile = json.load(f)
        weakness = profile.get("weak_areas") or profile.get("weakness") or ""
        w_lower = weakness.lower()
        
        interview_keywords = ["interview", "nervous", "freeze", "technical rounds", "mock", "panel", "stage fright", "anxious"]
        resume_keywords = ["resume", "shortlist", "ats", "getting calls", "bullets", "cv", "projects"]
        skill_keywords = ["don't know what to learn", "skills", "not sure what to study", "study", "learn", "gap", "prepare", "lack", "what to study", "curriculum"]
        
        if any(kw in w_lower for kw in interview_keywords):
            recommendation = "Mock Interview"
            rec_reason = f"you mentioned: '{weakness}'"
        elif any(kw in w_lower for kw in resume_keywords):
            recommendation = "Resume Review"
            rec_reason = f"you mentioned: '{weakness}'"
        elif any(kw in w_lower for kw in skill_keywords):
            recommendation = "Skill Gap Analysis"
            rec_reason = f"you mentioned: '{weakness}'"
        else:
            # Default if unclear
            recommendation = "Skill Gap Analysis"
            rec_reason = f"you mentioned: '{weakness}'"
    except Exception:
        recommendation = "Profile Setup"
        rec_reason = "there was an error reading your profile."

# Render recommendation banner
if recommendation == "Profile Setup":
    banner_text = f"💡 **Recommended for you**: We suggest starting with **Profile Setup**, because {rec_reason}"
else:
    banner_text = f"💡 **Recommended for you**: Based on your profile, we suggest starting with **{recommendation}**, because you mentioned: '{weakness}'"

# Sidebar selection option
# We bind it to "service_option" key so we can programmatically set it.
current_service = st.session_state.get("service_option", "Profile Setup")

if current_service != recommendation:
    col_banner, col_btn = st.columns([4, 1])
    with col_banner:
        st.info(banner_text)
    with col_btn:
        st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
        if st.button("Go to recommended service", key="go_to_rec"):
            st.session_state.service_option = recommendation
            st.rerun()
else:
    st.success(f"💡 **Recommended service active**: You are on the suggested path (**{recommendation}**).")

# Sidebar navigation
option = st.sidebar.selectbox(
    "Choose Service:",
    ("Profile Setup", "Resume Review", "Mock Interview", "Skill Gap Analysis"),
    key="service_option"
)

voice_mode = False
if option == "Mock Interview":
    st.sidebar.markdown("---")
    st.sidebar.subheader("🎙️ Voice Settings")
    st.sidebar.caption("⚠️ Note: Speech recognition requires Chrome or Edge browser.")
    voice_mode = st.sidebar.toggle("🔊 Voice Mode", value=True)

st.sidebar.markdown("---")
st.sidebar.subheader("📥 Export Playbook")
playbook_content, filename = generate_placement_playbook()
st.sidebar.download_button(
    label="📥 Export My Placement Playbook",
    data=playbook_content,
    file_name=filename,
    mime="text/markdown"
)

# Reset session states if the option changes
if "current_option" not in st.session_state or st.session_state.current_option != option:
    st.session_state.current_option = option
    st.session_state.messages = []
    st.session_state.bridge = None
    st.session_state.pending_report = None
    st.session_state.request_queue = queue.Queue()
    st.session_state.approval_queue = queue.Queue()
    st.session_state.last_spoken_message_index = -1

# Setup system instructions, tools, and primers based on navigation selection
if option == "Profile Setup":
    instructions = (
        "You are ProfileAgent, a helpful AI placement mentor.\n"
        "Your task is to gather these five student profile details one by one:\n"
        "1. Branch of study\n"
        "2. Year of study\n"
        "3. Target job roles\n"
        "4. Target companies\n"
        "5. What they feel weak at (e.g. 'I freeze during interviews')\n\n"
        "Do NOT ask multiple questions at once. Ask them one by one. Acknowledge the student's input briefly and immediately ask the next question.\n"
        "Once you have gathered all five details, call the `save_student_profile` tool to save their answers to student_profile.json. "
        "After saving, inform the student that their profile has been saved successfully and end the conversation."
    )
    tools = [save_student_profile]
    primer = "Hello! Let's start building your placement profile. Please ask me the first question."

elif option == "Resume Review":
    instructions = (
        "You are ResumeAgent, a professional resume coach and placement mentor.\n"
        "Your task is to gather two pieces of information from the student:\n"
        "1. Their resume text\n"
        "2. The target job description (or a description of the role they want)\n\n"
        "Please gather these two items one by one. First, ask the student to paste their resume text directly into the chat.\n"
        "Once they provide it, acknowledge it and ask them to paste the target job description or describe the role they want.\n"
        "Once you have both, analyze the resume against the target role/job description and generate detailed feedback covering:\n"
        "- Which bullet points in their resume are weak.\n"
        "- Which bullet points need numbers, metrics, or impact added.\n"
        "- What key keywords/skills are missing from their resume compared to the job description.\n\n"
        "After generating the feedback, format it beautifully in Markdown, call the `save_resume_feedback` tool to save it, present the feedback to the student, and end the conversation."
    )
    tools = [save_resume_feedback]
    primer = "Hello! Let's review your resume. Please paste your current resume text directly into the chat."

elif option == "Mock Interview":
    instructions = (
        "You are InterviewPanelAgent, simulating a panel of three interviewers:\n"
        "1. Hiring Manager - focus on behavioral/ownership questions (1-2 questions).\n"
        "2. Peer Engineer - focus on technical questions relevant to the target role (1-2 questions), and push back with a skeptical follow-up on the candidate's initial answer.\n"
        "3. Exec - focus on company alignment and motivational questions.\n\n"
        "YOUR WORKFLOW:\n"
        "1. Start by asking the student for their target role and target company.\n"
        "2. Once provided, start the interview. Introduce each interviewer before they ask their question.\n"
        "3. The Hiring Manager asks behavioral questions first.\n"
        "4. Then, the Peer Engineer asks a technical question. Once the candidate answers, the Peer Engineer MUST push back skeptically before asking their next question.\n"
        "5. The Exec finishes the interview with a 'why this company/role' question.\n\n"
        "SAFETY GUARDRAIL:\n"
        "Before asking any question, perform a safety check. If the question involves personal, biased, or inappropriate subjects "
        "(e.g., age, marital/family status, gender, religion, politics, or disability), you MUST immediately call the `log_guardrail_violation` tool, "
        "skip that question, and formulate a fair professional alternative instead.\n\n"
        "AFTER THE INTERVIEW:\n"
        "Once all questions are answered, compile a detailed report including:\n"
        "- Full Interview Transcript\n"
        "- Panel Debrief\n"
        "- Final Verdict\n"
        "- Coach Notes\n\n"
        "Finally, call the `save_interview_report` tool to save the report to interview_report.md, summarize the outcome to the candidate, and exit."
    )

    def save_interview_report(report: str) -> str:
        harsh_words = ["weak", "poor", "failed", "not ready"]
        harsh_count = sum(report.lower().count(w) for w in harsh_words)
        if harsh_count >= 2:
            # Pass the report text to the Streamlit UI thread
            st.session_state.request_queue.put(report)
            # Wait until the user reacts to the Approve/Reject buttons in the UI
            choice = st.session_state.approval_queue.get()
            with open("human_review_log.txt", "a", encoding="utf-8") as f:
                f.write(f"Decision: {'approved' if choice == 'yes' else 'revised'}\n")
                f.write(f"Harsh Count: {harsh_count}\n{'-'*40}\n")
            if choice == 'yes':
                with open("interview_report.md", "w", encoding="utf-8") as f:
                    f.write(report)
                return "Interview report successfully saved to interview_report.md."
            else:
                return (
                    "Feedback rejected by developer due to harsh language. Please rewrite the feedback, "
                    "especially the 'Coach Notes' or 'Final Verdict' sections, to soften the language and make "
                    "it more constructive, encouraging, and supportive (avoiding words like 'weak', 'poor', 'failed', 'not ready')."
                )
        else:
            with open("interview_report.md", "w", encoding="utf-8") as f:
                f.write(report)
            return "Interview report successfully saved to interview_report.md."

    tools = [save_interview_report, log_guardrail_violation]
    primer = "Hello! Let's conduct your mock panel interview. To help us customize the panel questions, what is your target job role and company?"

elif option == "Skill Gap Analysis":
    profile_data = {}
    if os.path.exists("student_profile.json"):
        try:
            with open("student_profile.json", "r") as f:
                profile_data = json.load(f)
        except Exception:
            pass
    profile_str = json.dumps(profile_data, indent=2) if profile_data else "None"
    instructions = (
        "You are SkillGapAgent, a specialized career coach and placement mentor.\n"
        "Your task is to analyze the student's current technical skills and identify gaps "
        "relative to their target roles and target companies.\n\n"
        f"STUDENT PROFILE:\n{profile_str}\n\n"
        "YOUR WORKFLOW:\n"
        "1. Check the student profile. Confirm their targets, and ask them to list their current technical skills.\n"
        "2. Once they provide their skills, compare them against requirements for their target roles at their target companies. "
        "Use specific, deep company-specific requirements (e.g. for Google, focus on strong DSA depth, memory management, scale; for startups, focus on fast development, full-stack, specific frameworks like React/Node; for finance, focus on low latency, concurrent programming, databases).\n"
        "3. Output a prioritized 'what to learn next' list (top 3-5 specific topics) ranked by importance for their specific target companies. Do NOT give generic advice.\n"
        "4. Call the `save_skill_gap_report` tool to save the Markdown report to skill_gap_report.md.\n"
        "5. Inform the student that the report is saved and conclude the conversation."
    )
    
    def save_skill_gap_report(report: str) -> str:
        with open("skill_gap_report.md", "w", encoding="utf-8") as f:
            f.write(report)
        return "Skill gap report successfully saved to skill_gap_report.md."

    tools = [save_skill_gap_report]
    primer = "Hello! Let's analyze your skills against your target role. Please list your current technical skills."

# Initialize or start the bridge thread
if st.session_state.bridge is None:
    st.session_state.bridge = AsyncAgentBridge(instructions, tools, primer)
    # Wait for initial greeting response
    with st.spinner("Starting agent session..."):
        primer_resp = st.session_state.bridge.output_queue.get()
    st.session_state.messages.append({"role": "assistant", "content": primer_resp})

# Display Chat History
for msg in st.session_state.messages:
    if msg["role"] == "assistant" and msg["content"].startswith("Agent Error:"):
        st.error(msg["content"])
    elif msg["role"] == "assistant" and any(h in msg["content"] for h in ["Panel Debrief", "Final Verdict", "Coach Notes"]):
        render_interview_report(msg["content"])
    else:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# Trigger Text-to-Speech for new assistant messages (Mock Interview only)
if option == "Mock Interview" and voice_mode:
    assistant_msgs = [msg for msg in st.session_state.messages if msg["role"] == "assistant"]
    if assistant_msgs:
        latest_msg = assistant_msgs[-1]["content"]
        latest_index = len(assistant_msgs) - 1
        if "last_spoken_message_index" not in st.session_state:
            st.session_state.last_spoken_message_index = -1
        if latest_index > st.session_state.last_spoken_message_index:
            st.session_state.last_spoken_message_index = latest_index
            text_to_speech_component(latest_msg)

# Pull pending review reports if any
if not st.session_state.request_queue.empty() and st.session_state.pending_report is None:
    st.session_state.pending_report = st.session_state.request_queue.get()

# Render approval workflow overlay
if st.session_state.pending_report is not None:
    st.markdown("""
    <div class="approval-card">
        <h3>⚠️ [HUMAN REVIEW NEEDED]</h3>
        <p>The panel feedback draft generated by the agent contains harsh wording. As the developer, you must approve or request language softening before it is displayed to the student.</p>
    </div>
    """, unsafe_allow_html=True)
    st.text_area("Draft Report Preview:", st.session_state.pending_report, height=250)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Approve (Show as is)", key="app_yes"):
            st.session_state.approval_queue.put("yes")
            st.session_state.pending_report = None
            # Block until agent finishes write and prints completion message
            with st.spinner("Saving report..."):
                final_reply = st.session_state.bridge.output_queue.get()
            st.session_state.messages.append({"role": "assistant", "content": final_reply})
            st.rerun()
    with col2:
        if st.button("Reject (Request Softened Language)", key="app_no"):
            st.session_state.approval_queue.put("no")
            st.session_state.pending_report = None
            # Block until agent rewrites feedback and returns response
            with st.spinner("Requesting rewrite..."):
                final_reply = st.session_state.bridge.output_queue.get()
            st.session_state.messages.append({"role": "assistant", "content": final_reply})
            st.rerun()

# Normal Chat Input Workflow
else:
    if user_input := st.chat_input("Type your message..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Enqueue user message to the background bridge
        st.session_state.bridge.input_queue.put(user_input)

        # Non-deadlock polling loop to wait for response or handle incoming review events
        response_text = None
        with st.spinner("Mentor is typing..."):
            while response_text is None and st.session_state.pending_report is None:
                # Check for human review requests
                try:
                    st.session_state.pending_report = st.session_state.request_queue.get_nowait()
                    st.rerun()
                except queue.Empty:
                    pass

                # Check for normal agent response
                try:
                    response_text = st.session_state.bridge.output_queue.get(timeout=0.05)
                except queue.Empty:
                    pass
        
        if response_text is not None:
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            st.rerun()

# Inject speech recognition microphone button (only for Mock Interview if voice mode is active)
# If voice_mode is False or we are on other screens, it will remove the injected mic button if present
speech_recognition_injector(voice_mode)

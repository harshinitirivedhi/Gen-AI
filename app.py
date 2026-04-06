import streamlit as st
from groq import Groq
import json
import re
import random
import concurrent.futures

# ─── YOUR GROQ API KEY HERE ────────────────────────────────────────────────────
GROQ_API_KEY = "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"

# ─── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MCQ Distracter Generator",
    page_icon="🎯",
    layout="wide"
)

# ─── Session State ─────────────────────────────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True
if "saved_questions" not in st.session_state:
    st.session_state.saved_questions = []
if "last_results" not in st.session_state:
    st.session_state.last_results = []
if "num_questions" not in st.session_state:
    st.session_state.num_questions = 1
if "form_reset_key" not in st.session_state:
    st.session_state.form_reset_key = 0

# ─── CSS ───────────────────────────────────────────────────────────────────────
def inject_css(dark: bool):
    if dark:
        bg        = "#0d0d14"
        surface   = "#16161f"
        surface2  = "#1e1e2e"
        border    = "#2e2e45"
        text      = "#e8e8f4"
        muted     = "#6868a0"
        accent    = "#7c6ff7"
        opt_bg    = "#1a1a28"
        opt_hover = "#22223a"
        label_col = "#a0a0c8"
        save_bg   = "#1a2a1a"
        save_bdr  = "#2d4a2d"
        save_col  = "#4ade80"
        panel_bg  = "#13131c"
        num_bg    = "#1e1e2e"
        num_bdr   = "#3a3a60"
    else:
        bg        = "#f4f4fb"
        surface   = "#ffffff"
        surface2  = "#ededf8"
        border    = "#d0d0e8"
        text      = "#1a1a2e"
        muted     = "#6060a0"
        accent    = "#5b50d6"
        opt_bg    = "#fafaff"
        opt_hover = "#ededf8"
        label_col = "#5050a0"
        save_bg   = "#e8fdf0"
        save_bdr  = "#bbf7d0"
        save_col  = "#16a34a"
        panel_bg  = "#f0f0ff"
        num_bg    = "#ededf8"
        num_bdr   = "#c0c0e0"

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Mono:wght@400;500&display=swap');

    html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {{
        background-color: {bg} !important;
        color: {text} !important;
        font-family: 'DM Mono', monospace !important;
    }}
    [data-testid="stSidebar"] {{ display: none !important; }}
    header[data-testid="stHeader"] {{ background: transparent !important; }}
    [data-testid="stToolbar"] {{ display: none; }}
    .main .block-container {{ padding: 1.5rem 2rem 4rem !important; max-width: 100% !important; }}
    #MainMenu, footer {{ visibility: hidden; }}

    .mcq-header {{ text-align: center; margin-bottom: 2rem; }}
    .mcq-title {{
        font-family: 'Syne', sans-serif !important;
        font-size: clamp(1.8rem, 4vw, 2.8rem); font-weight: 800;
        background: linear-gradient(135deg, {text} 30%, {accent});
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        background-clip: text; line-height: 1.15; margin-bottom: 8px;
    }}
    .mcq-sub {{ color: {muted}; font-size: 15px; line-height: 1.6; }}

    label, .stTextInput label, .stTextArea label, .stNumberInput label {{
        font-size: 13px !important; letter-spacing: 1.5px !important;
        text-transform: uppercase !important; color: {label_col} !important;
        font-family: 'DM Mono', monospace !important;
    }}

    .stTextInput input, .stTextArea textarea, .stNumberInput input {{
        background: {surface2} !important; border: 1px solid {border} !important;
        border-radius: 10px !important; color: {text} !important;
        font-family: 'DM Mono', monospace !important; font-size: 16px !important;
    }}
    .stTextInput input:focus, .stTextArea textarea:focus, .stNumberInput input:focus {{
        border-color: {accent} !important; box-shadow: 0 0 0 3px {accent}28 !important;
    }}

    .stButton > button {{
        width: 100%; background: {accent} !important; color: white !important;
        border: none !important; border-radius: 10px !important;
        font-family: 'Syne', sans-serif !important; font-weight: 700 !important;
        font-size: 16px !important; padding: 12px 0 !important; transition: all 0.2s !important;
    }}
    .stButton > button:hover {{
        background: #6a5ee8 !important; box-shadow: 0 8px 24px {accent}44 !important;
        transform: translateY(-1px) !important;
    }}

    .q-block {{
        background: {surface}; border: 1px solid {border}; border-radius: 14px;
        padding: 18px 20px; margin-bottom: 18px;
    }}
    .q-block-header {{
        font-family: 'Syne', sans-serif; font-size: 13px; font-weight: 700;
        color: {accent}; text-transform: uppercase; letter-spacing: 1.5px;
        margin-bottom: 14px; padding-bottom: 10px; border-bottom: 1px solid {border};
    }}

    .opt-card {{
        background: {opt_bg}; border: 1px solid {border}; border-radius: 12px;
        padding: 16px 20px; display: flex; align-items: center; gap: 14px;
        margin-bottom: 10px; transition: all 0.2s;
    }}
    .opt-card:hover {{ background: {opt_hover}; border-color: {accent}66; }}
    .opt-card.correct {{ background: #1a2e1a; border-color: #4ade8066; }}
    .opt-letter {{
        min-width: 36px; height: 36px; border-radius: 8px;
        background: {surface2}; border: 1px solid {border};
        display: flex; align-items: center; justify-content: center;
        font-family: 'Syne', sans-serif; font-weight: 700; font-size: 15px;
        color: {accent}; flex-shrink: 0;
    }}
    .opt-letter.correct-letter {{ background: #16a34a22; border-color: #4ade80; color: #4ade80; }}
    .opt-text {{ font-size: 17px; color: {text}; line-height: 1.5; }}
    .correct-badge {{
        font-size: 10px; text-transform: uppercase; letter-spacing: 1px;
        color: #4ade80; margin-left: auto; white-space: nowrap;
    }}

    .result-title {{ font-family: 'Syne', sans-serif; font-size: 20px; font-weight: 700; color: {text}; margin-bottom: 6px; }}
    .result-sub {{ font-size: 13px; color: {muted}; margin-bottom: 16px; }}

    .q-box {{
        background: {surface2}; border: 1px solid {border}; border-radius: 12px;
        padding: 16px 20px; margin-bottom: 16px; font-size: 17px; color: {text}; line-height: 1.6;
    }}
    .q-box-label {{ font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; color: {muted}; margin-bottom: 6px; }}

    .exp-box {{ background: {accent}0e; border: 1px solid {accent}33; border-radius: 12px; padding: 16px 20px; margin-top: 14px; }}
    .exp-label {{ font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; color: {accent}; margin-bottom: 6px; }}
    .exp-text {{ font-size: 14px; color: {muted}; line-height: 1.7; }}

    .panel-title {{
        font-family: 'Syne', sans-serif;
        font-size: 16px; font-weight: 700; color: {text};
        margin-bottom: 16px;
    }}

    .saved-card {{
        background: {save_bg}; border: 1px solid {save_bdr}; border-radius: 10px;
        padding: 12px 14px; margin-bottom: 10px;
    }}
    .saved-num {{ font-size: 10px; text-transform: uppercase; letter-spacing: 1.5px; color: {save_col}; margin-bottom: 4px; }}
    .saved-q {{ font-size: 13px; font-weight: 500; margin-bottom: 6px; color: {text}; line-height: 1.4; }}
    .saved-opt {{ font-size: 12px; color: {muted}; margin-bottom: 2px; }}

    .empty-state {{
        text-align: center; padding: 2rem 1rem; opacity: 0.4;
        font-size: 13px; color: {muted};
    }}

    .gen-progress {{
        font-size: 12px; color: {muted}; text-align: center;
        padding: 8px; letter-spacing: 1px; text-transform: uppercase;
    }}

    .parallel-badge {{
        display: inline-block;
        background: {accent}22; border: 1px solid {accent}55;
        color: {accent}; font-size: 11px; border-radius: 6px;
        padding: 3px 10px; letter-spacing: 1px; text-transform: uppercase;
        margin-bottom: 12px;
    }}

    hr {{ border-color: {border} !important; margin: 16px 0 !important; }}
    </style>
    """, unsafe_allow_html=True)


# ─── Generate Distractors (single) ────────────────────────────────────────────
def generate_distractors(index: int, question: str, correct_answer: str, subject: str):
    """Returns (index, result_dict) for ordering after parallel execution."""
    client = Groq(api_key=GROQ_API_KEY)
    prompt = f"""You are an expert MCQ creator for educational assessments.

Subject: {subject}
Question: {question}
Correct Answer: {correct_answer}

Generate exactly 3 DISTRACTORS (wrong answer options).

Rules:
1. Plausible and logical — not obviously wrong
2. Similar length and style to the correct answer
3. Target common misconceptions
4. Must be CLEARLY WRONG (not partially correct)
5. Do NOT repeat or paraphrase the correct answer

Return ONLY a JSON object (no markdown, no extra text):
{{
  "distractors": ["First wrong option", "Second wrong option", "Third wrong option"],
  "explanation": "Brief explanation of why these distractors are pedagogically effective"
}}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000,
        temperature=0.7
    )
    text = response.choices[0].message.content.strip()
    text = re.sub(r'```json|```', '', text).strip()
    data = json.loads(text)

    distractors = data.get("distractors", [])
    all_options = distractors + [correct_answer.strip()]
    random.shuffle(all_options)

    return index, {
        "question": question.strip(),
        "correct_answer": correct_answer.strip(),
        "subject": subject,
        "options": all_options,
        "labels": ["A", "B", "C", "D"],
        "explanation": data.get("explanation", ""),
        "error": None
    }


def generate_all_parallel(questions_data, subject_val):
    """Run all API calls in parallel using ThreadPoolExecutor."""
    results = [None] * len(questions_data)
    errors = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(questions_data), 10)) as executor:
        futures = {
            executor.submit(generate_distractors, i, q, a, subject_val): i
            for i, (q, a) in enumerate(questions_data)
        }
        for future in concurrent.futures.as_completed(futures):
            i = futures[future]
            try:
                idx, result = future.result()
                results[idx] = result
            except Exception as e:
                errors[i] = str(e)
                results[i] = {
                    "question": questions_data[i][0],
                    "correct_answer": questions_data[i][1],
                    "subject": subject_val,
                    "options": [],
                    "labels": ["A", "B", "C", "D"],
                    "explanation": "",
                    "error": str(e)
                }

    return results, errors


# ─── Main App ──────────────────────────────────────────────────────────────────
def main():
    dark = st.session_state.dark_mode
    inject_css(dark)

    # Theme toggle
    t1, t2 = st.columns([10, 1])
    with t2:
        icon = "☀️" if dark else "🌙"
        if st.button(icon, key="theme_btn"):
            st.session_state.dark_mode = not dark
            st.rerun()

    left_col, right_col = st.columns([3, 2], gap="large")

    # ════════════════════════════
    # LEFT — Main Generator
    # ════════════════════════════
    with left_col:
        st.markdown("""
        <div class="mcq-header">
            <div class="mcq-title">MCQ Distracter<br/>Generator</div>
            <div class="mcq-sub">Enter questions + correct answers.<br/>All questions generated simultaneously — fast & parallel.</div>
        </div>
        """, unsafe_allow_html=True)

        # ── Number of Questions ──
        num_q = st.number_input(
            "🔢 How many questions?",
            min_value=1,
            max_value=20,
            value=st.session_state.num_questions,
            step=1,
            key="num_q_input"
        )
        st.session_state.num_questions = num_q

        # ── Dynamic Form ──
        with st.form(key=f"mcq_form_{st.session_state.form_reset_key}"):
            subject_global = st.text_input(
                "Subject (applies to all)",
                placeholder="e.g. Biology, History, Math...",
                key="subject_global"
            )
            st.markdown("---")

            questions_data = []
            for i in range(num_q):
                st.markdown(f'<div class="q-block-header">📝 Question {i+1}</div>', unsafe_allow_html=True)
                q = st.text_area(
                    f"Question {i+1}",
                    placeholder="e.g. What is the powerhouse of the cell?",
                    height=90,
                    key=f"question_{i}"
                )
                a = st.text_input(
                    f"Correct Answer {i+1}",
                    placeholder="e.g. Mitochondria",
                    key=f"answer_{i}"
                )
                questions_data.append((q, a))
                if i < num_q - 1:
                    st.markdown("---")

            generate_clicked = st.form_submit_button(
                f"⚡ Generate All {num_q} Question{'s' if num_q > 1 else ''} in Parallel",
                use_container_width=True
            )

        if generate_clicked:
            # Validate
            valid = True
            for i, (q, a) in enumerate(questions_data):
                if not q.strip() or not a.strip():
                    st.error(f"⚠️ Question {i+1}: Please fill in both Question and Correct Answer.")
                    valid = False
                    break

            if valid:
                subject_val = subject_global.strip() if subject_global.strip() else "General"

                # Clear previous results — fresh generate every time
                st.session_state.last_results = []

                with st.spinner(f"⚡ Generating all {num_q} question{'s' if num_q > 1 else ''} in parallel..."):
                    results, errors = generate_all_parallel(questions_data, subject_val)

                if errors:
                    for idx, err in errors.items():
                        st.error(f"⚠️ Question {idx+1} failed: {err}")

                st.session_state.last_results = [r for r in results if r is not None]

        # ── Show Results ──
        if st.session_state.last_results:
            results = st.session_state.last_results
            st.markdown("---")
            st.markdown(f'<div class="result-title">📋 Generated MCQs ({len(results)})</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="result-sub">Subject: {results[0]["subject"]} &nbsp;|&nbsp; '
                f'<span class="parallel-badge">⚡ Parallel Generated</span>'
                f'&nbsp;|&nbsp; ✅ = Correct Answer</div>',
                unsafe_allow_html=True
            )

            for idx, r in enumerate(results):
                if r.get("error"):
                    st.error(f"❌ Question {idx+1} failed: {r['error']}")
                    continue

                labels = r["labels"]
                all_options = r["options"]
                correct = r["correct_answer"]

                st.markdown(f"""
                <div class="q-block">
                    <div class="q-block-header">Question {idx+1}</div>
                    <div class="q-box">
                        <div class="q-box-label">Question</div>
                        {r['question']}
                    </div>
                """, unsafe_allow_html=True)

                options_html = ""
                for i, opt in enumerate(all_options):
                    is_correct = opt.strip().lower() == correct.strip().lower()
                    card_class = "opt-card correct" if is_correct else "opt-card"
                    letter_class = "opt-letter correct-letter" if is_correct else "opt-letter"
                    badge = '<span class="correct-badge">✅ Correct</span>' if is_correct else ""
                    options_html += f"""
                    <div class="{card_class}">
                        <div class="{letter_class}">{labels[i]}</div>
                        <div class="opt-text">{opt}</div>
                        {badge}
                    </div>"""
                st.markdown(options_html, unsafe_allow_html=True)

                if r["explanation"]:
                    st.markdown(f"""
                    <div class="exp-box">
                        <div class="exp-label">💡 Why these distractors work</div>
                        <div class="exp-text">{r['explanation']}</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("💾 Save All Questions", key="save_all_btn"):
                saved_count = 0
                for r in results:
                    if r.get("error"):
                        continue
                    already = any(s["question"] == r["question"] for s in st.session_state.saved_questions)
                    if not already:
                        labels = r["labels"]
                        all_options = r["options"]
                        st.session_state.saved_questions.append({
                            "question": r["question"],
                            "subject": r["subject"],
                            "correct_answer": r["correct_answer"],
                            "options": [f"{labels[i]}. {all_options[i]}" for i in range(4)]
                        })
                        saved_count += 1
                if saved_count:
                    st.success(f"✅ {saved_count} question(s) saved!")
                    st.session_state.last_results = []
                    st.session_state.num_questions = 1
                    st.session_state.form_reset_key += 1
                    st.rerun()
                else:
                    st.warning("⚠️ All already saved!")
                    st.session_state.last_results = []
                    st.session_state.num_questions = 1
                    st.session_state.form_reset_key += 1
                    st.rerun()

    # ════════════════════════════
    # RIGHT — Saved Questions Panel
    # ════════════════════════════
    with right_col:
        st.markdown(
            f'<div class="panel-title">💾 Saved Questions '
            f'<span style="opacity:0.5;font-size:13px;">({len(st.session_state.saved_questions)})</span></div>',
            unsafe_allow_html=True
        )

        if st.session_state.saved_questions:
            c1, c2 = st.columns(2)
            with c1:
                if st.button("🗑️ Clear All", key="clear_btn", use_container_width=True):
                    st.session_state.saved_questions = []
                    st.rerun()
            with c2:
                save_text = ""
                for i, entry in enumerate(st.session_state.saved_questions):
                    save_text += f"Q{i+1}. [{entry['subject']}] {entry['question']}\n"
                    for opt in entry["options"]:
                        is_correct = opt.split(". ", 1)[-1].strip().lower() == entry.get("correct_answer", "").strip().lower()
                        marker = " ✓" if is_correct else ""
                        save_text += f"   {opt}{marker}\n"
                    save_text += "\n"
                st.download_button(
                    label="📥 Download",
                    data=save_text,
                    file_name="saved_mcqs.txt",
                    mime="text/plain",
                    use_container_width=True
                )

            st.markdown("---")

            for i, entry in enumerate(st.session_state.saved_questions):
                opts_html = "".join([f'<div class="saved-opt">{opt}</div>' for opt in entry["options"]])
                st.markdown(f"""
                <div class="saved-card">
                    <div class="saved-num">#{i+1} — {entry['subject']}</div>
                    <div class="saved-q">{entry['question']}</div>
                    {opts_html}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="empty-state">
                <div style="font-size:2rem">💾</div>
                <div style="margin-top:8px">Save a question to see it here!</div>
            </div>
            """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
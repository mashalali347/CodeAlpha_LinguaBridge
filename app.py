import json
from datetime import datetime
from io import BytesIO

import requests
import speech_recognition as sr
import streamlit as st
import streamlit.components.v1 as components
from deep_translator import GoogleTranslator
from gtts import gTTS

st.set_page_config(page_title="LinguaBridge", page_icon="🌍", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    .stApp, .stApp p, .stApp label, .stApp button, .stApp textarea, .stApp input,
    .stApp h1, .stApp h2, .stApp h3 { font-family: 'Inter', 'Segoe UI', sans-serif; }

    #MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDeployButton"] { display: none !important; }
    [data-testid="stHeader"] { background: transparent; }

    .stApp::before { content: ""; position: fixed; top: 0; left: 0; right: 0; height: 14px;
        background: linear-gradient(90deg, #1f4e8c, #1f8a70); z-index: 999999; }
    [data-testid="stMainBlockContainer"], .block-container { padding-top: 2.5rem !important; }

    [data-testid="stSidebarUserContent"] { padding-top: 0rem !important; }
    [data-testid="stSidebarHeader"] { height: 1.5rem !important; padding-bottom: 0 !important; }
    [data-testid="stSidebar"] { background: #0a1424; border-right: 1px solid #1b2f4d; }
    [data-testid="stSidebar"] h1 { font-size: 2.1rem !important; font-weight: 700; color: #e8eef7; }

    /* cards */
    [data-testid="stVerticalBlockBorderWrapper"] { background: #16263d; border: 1px solid #22385a !important;
        border-radius: 18px; box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45); }

    /* inputs */
    [data-baseweb="select"] > div, [data-baseweb="textarea"], [data-baseweb="base-input"],
    textarea, input { background-color: #0e1a2b !important; color: #e8eef7 !important; }
    [data-testid="stAudioInput"] { background: #0e1a2b; border-radius: 12px; }

    /* buttons */
    .stButton > button { border-radius: 12px; border: 1px solid #2c4468; background: #1c3150;
        color: #e8eef7; transition: all .15s ease; }
    .stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 14px rgba(0,0,0,.5);
        border-color: #4da3ff; color: #4da3ff; }
    .stButton > button[kind="primary"], button[data-testid="stBaseButton-primary"] {
        background: linear-gradient(90deg, #1f4e8c, #1f8a70); color: #fff; border: 0;
        font-weight: 600; font-size: 1.05rem; padding: .65rem 1rem; }
    .stButton > button[kind="primary"]:hover, button[data-testid="stBaseButton-primary"]:hover { color: #fff; }

    /* round swap button */
    .st-key-swap { display: flex; justify-content: center; }
    .st-key-swap button { width: 56px; height: 56px; min-height: 56px; border-radius: 50%; padding: 0;
        background: linear-gradient(135deg, #1f4e8c, #1f8a70); border: 0;
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.5); }
    .st-key-swap button p { display: none; }
    .st-key-swap button span, .st-key-swap button [data-testid="stIconMaterial"] { color: #fff !important; font-size: 28px !important; }
    .st-key-swap button:hover { transform: rotate(180deg) scale(1.05); border: 0; }

    /* translated text */
    [data-testid="stCodeBlock"] code { font-family: 'Segoe UI', Tahoma, sans-serif !important; font-size: 1.3rem !important; }
    [data-testid="stCodeBlock"] button { opacity: 1 !important; }
    [data-testid="stVerticalBlockBorderWrapper"] h3 span { color: #cfe3ff !important; }
     .st-key-swap { margin-top: 170px; }
    </style>
    """,
    unsafe_allow_html=True,
)
 

LANGS = {
    "English": "en", "Urdu": "ur", "Pashto": "ps", "Hindi": "hi", "Arabic": "ar",
    "Persian": "fa", "Bengali": "bn", "Punjabi": "pa", "French": "fr", "German": "de",
    "Spanish": "es", "Italian": "it", "Portuguese": "pt", "Dutch": "nl", "Polish": "pl",
    "Swedish": "sv", "Greek": "el", "Russian": "ru", "Turkish": "tr", "Indonesian": "id",
    "Vietnamese": "vi", "Thai": "th", "Chinese (Simplified)": "zh-CN",
    "Japanese": "ja", "Korean": "ko",
}
SPEECH = {
    "English": "en-US", "Urdu": "ur-PK", "Pashto": "ps-AF", "Hindi": "hi-IN", "Arabic": "ar-SA",
    "Persian": "fa-IR", "Bengali": "bn-BD", "Punjabi": "pa-IN", "French": "fr-FR", "German": "de-DE",
    "Spanish": "es-ES", "Italian": "it-IT", "Portuguese": "pt-PT", "Dutch": "nl-NL", "Polish": "pl-PL",
    "Swedish": "sv-SE", "Greek": "el-GR", "Russian": "ru-RU", "Turkish": "tr-TR", "Indonesian": "id-ID",
    "Vietnamese": "vi-VN", "Thai": "th-TH", "Chinese (Simplified)": "zh-CN",
    "Japanese": "ja-JP", "Korean": "ko-KR",
}
DETECT = "Detect language"
NAMES = list(LANGS)

ss = st.session_state
ss.setdefault("history", [])
ss.setdefault("favs", [])
ss.setdefault("src_lang", "English")
ss.setdefault("tgt_lang", "Urdu")
ss.setdefault("text", "")
ss.setdefault("current", None)
ss.setdefault("audio_src", None)
ss.setdefault("audio_out", None)
ss.setdefault("view", "Translate")
ss.setdefault("search", "")


# ---------- helpers ----------
def now():
    return datetime.now().strftime("%d %b %Y, %I:%M %p")


def key_of(r):
    return (r["src"], r["tgt"], r["text"])


def warn(msg):
    st.toast(msg, icon="⚠️")


def reset_audio():
    ss.audio_src = None
    ss.audio_out = None


def call_translate(text, src, tgt):
    s = "Autodetect" if src == DETECT else LANGS[src]
    t = LANGS[tgt]
    try:
        r = requests.get(
            "https://api.mymemory.translated.net/get",
            params={"q": text, "langpair": f"{s}|{t}"},
            timeout=10,
        ).json()
        if int(r["responseStatus"]) != 200:
            raise ValueError(r.get("responseDetails", "error"))
        main = r["responseData"]["translatedText"]
        alts = []
        for m in r.get("matches", []):
            x = m.get("translation")
            if x and x != main and x not in alts:
                alts.append(x)
        return main, alts[:3]
    except Exception:
        out = GoogleTranslator(source="auto" if src == DETECT else s, target=t).translate(text)
        return out, []


def make_audio(text, lang_name):
    try:
        buf = BytesIO()
        gTTS(text, lang=LANGS[lang_name]).write_to_fp(buf)
        return buf.getvalue()
    except Exception:
        return None


def add_history(r):
    ss.history = [h for h in ss.history if key_of(h) != key_of(r)]
    ss.history.insert(0, {**r, "alts": list(r["alts"]), "time": now()})
    ss.history = ss.history[:50]


def is_saved():
    return ss.current is not None and any(key_of(f) == key_of(ss.current) for f in ss.favs)


# ---------- button actions ----------
def do_translate():
    text = ss.text.strip()
    if not text:
        warn("Enter some text first")
        return
    src, tgt = ss.src_lang, ss.tgt_lang
    try:
        out, alts = (text, []) if src == tgt else call_translate(text, src, tgt)
    except Exception:
        warn("Could not translate. Check your internet and try again.")
        return
    ss.current = {"src": src, "tgt": tgt, "text": text, "out": out, "alts": list(alts)}
    reset_audio()
    add_history(ss.current)


def on_mic():
    audio = ss.get("mic")
    if audio is None:
        return
    try:
        recognizer = sr.Recognizer()
        with sr.AudioFile(BytesIO(audio.getvalue())) as source:
            data = recognizer.record(source)
        lang = SPEECH.get(ss.src_lang, "en-US")
        ss.text = recognizer.recognize_google(data, language=lang)[:500]
        do_translate()
    except sr.UnknownValueError:
        warn("Could not understand the audio. Please try again.")
    except Exception:
        warn("Voice input failed. Check your internet and microphone.")


def do_swap():
    if ss.src_lang == DETECT:
        warn("Choose a source language to swap")
        return
    ss.src_lang, ss.tgt_lang = ss.tgt_lang, ss.src_lang
    if ss.current:
        ss.text = ss.current["out"]
    ss.current = None
    reset_audio()


def do_clear():
    ss.text = ""
    ss.current = None
    reset_audio()


def use_alt(i):
    cur = ss.current
    cur["out"], cur["alts"][i] = cur["alts"][i], cur["out"]
    reset_audio()


def toggle_save():
    if not ss.current:
        warn("Translate something first")
        return
    if is_saved():
        ss.favs = [f for f in ss.favs if key_of(f) != key_of(ss.current)]
        st.toast("Removed from saved")
    else:
        ss.favs.insert(0, {**ss.current, "alts": list(ss.current["alts"]), "time": now()})
        st.toast("Saved", icon="⭐")


def listen_src():
    text = ss.text.strip()
    if not text:
        warn("Nothing to read yet")
        return
    lang = "English" if ss.src_lang == DETECT else ss.src_lang
    ss.audio_src = make_audio(text, lang)
    if ss.audio_src is None:
        warn("Speech is not available for this language")


def listen_out():
    if not ss.current:
        warn("Translate something first")
        return
    ss.audio_out = make_audio(ss.current["out"], ss.current["tgt"])
    if ss.audio_out is None:
        warn("Speech is not available for this language")


def open_item(r):
    ss.src_lang, ss.tgt_lang, ss.text = r["src"], r["tgt"], r["text"]
    ss.current = {**r, "alts": list(r["alts"])}
    reset_audio()
    ss.view = "Translate"


def set_pair(s, t):
    ss.src_lang, ss.tgt_lang = s, t
    ss.view = "Translate"


def clear_history():
    ss.history = []


def on_search():
    ss.view = "Saved" if ss.view == "Saved" else "History"


def copy_button(text):
    safe = json.dumps(text).replace("</", "<\\/")
    components.html(
        f"""
       <style>
          body {{ margin: 0; }}
          #c {{ display:flex; align-items:center; justify-content:center; gap:7px; width:100%; height:40px;
                border-radius:12px; border:1px solid #2c4468; background:#1c3150; color:#e8eef7;
                font-family:'Inter','Segoe UI',sans-serif; font-size:14px; cursor:pointer;
                transition:all .15s ease; }}
          #c:hover {{ border-color:#4da3ff; color:#4da3ff; box-shadow:0 4px 14px rgba(0,0,0,.5); }}
          #c.done {{ border-color:#2fbf94; color:#2fbf94; }}
        </style>
        <button id="c">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor"
               stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V6a2 2 0 0 1 2-2h9"/>
          </svg>
          <span id="l">Copy</span>
        </button>
        <script>
        const t = {safe};
        const b = document.getElementById('c');
        const l = document.getElementById('l');
        b.onclick = () => {{
          const ta = document.createElement('textarea');
          ta.value = t; document.body.appendChild(ta); ta.select();
          document.execCommand('copy'); document.body.removeChild(ta);
          l.innerText = 'Copied!'; b.classList.add('done');
          setTimeout(() => {{ l.innerText = 'Copy'; b.classList.remove('done'); }}, 1500);
        }};
        </script>
        """,
        height=44,
    )


# ---------- sidebar ----------
with st.sidebar:
    try:
        with open("logo.svg") as f:
            st.image(f.read(), width=120)
    except Exception:
        st.write("🌍")
    st.title("LinguaBridge")
    st.radio("Menu", ["Translate", "History", "Saved"], key="view", label_visibility="collapsed")

    st.subheader("Recent pairs")
    pairs = []
    for h in ss.history:
        p = (h["src"], h["tgt"])
        if p not in pairs:
            pairs.append(p)
    for i, (s, t) in enumerate(pairs[:3]):
        st.button(f"{s} to {t}", key=f"pair{i}", on_click=set_pair, args=(s, t), use_container_width=True)
    if not pairs:
        st.caption("No translations yet")

# ---------- search bar ----------
st.text_input(
    "Search", key="search", on_change=on_search,
    placeholder="Search your history and saved translations",
    label_visibility="collapsed",
)


# ---------- views ----------
def translate_view():
    left, mid, right = st.columns([10, 2, 10], gap="small", vertical_alignment="top")

    with left:
        with st.container(border=True):
            st.markdown("### :blue[Source language]")
            st.selectbox("Source", [DETECT] + NAMES, key="src_lang", label_visibility="collapsed")
            st.text_area(
                "Text", key="text", height=170, max_chars=500,
                placeholder="Type, or tap the mic below and speak",
                label_visibility="collapsed",
            )
            st.caption(f"{len(ss.text)}/500")
            st.audio_input("Voice input: tap the mic and speak", key="mic", on_change=on_mic)
            b1, b2 = st.columns(2)
            b1.button("Listen", key="listen_src", icon=":material/volume_up:",
                      on_click=listen_src, use_container_width=True)
            b2.button("Clear", icon=":material/close:", on_click=do_clear, use_container_width=True)
            if ss.audio_src:
                st.audio(ss.audio_src, format="audio/mp3", autoplay=True)
                ss.audio_src = None

    with mid:
        st.button("Swap", key="swap", icon=":material/swap_horiz:", help="Swap languages", on_click=do_swap)

    with right:
        with st.container(border=True):
            st.markdown("### :green[Target language]")
            st.selectbox("Target", NAMES, key="tgt_lang", label_visibility="collapsed")
            cur = ss.current
            if cur:
                st.code(cur["out"], language=None, wrap_lines=True)
                if cur["alts"]:
                    st.caption("Other translations")
                    for i, a in enumerate(cur["alts"]):
                        st.button(a, key=f"alt{i}", on_click=use_alt, args=(i,), use_container_width=True)
                t0, t1, t2 = st.columns(3)
                with t0:
                    copy_button(cur["out"])
                t1.button("Listen", key="listen_out", icon=":material/volume_up:",
                          on_click=listen_out, use_container_width=True)
                t2.button("Saved" if is_saved() else "Save",
                          icon=":material/star:" if is_saved() else ":material/star_border:",
                          on_click=toggle_save, use_container_width=True)
                if ss.audio_out:
                    st.audio(ss.audio_out, format="audio/mp3", autoplay=True)
                    ss.audio_out = None
            else:
                st.info("Your translation will appear here.")

    st.button("Translate", type="primary", icon=":material/translate:",
              on_click=do_translate, use_container_width=True)


def list_view(items, empty_msg, prefix):
    q = ss.search.lower().strip()
    rows = [r for r in items if not q or q in r["text"].lower() or q in r["out"].lower()]
    if not rows:
        st.info("No results match your search." if q else empty_msg)
        return
    for i, r in enumerate(rows):
        with st.container(border=True):
            st.caption(f'{r["src"]} to {r["tgt"]} - {r["time"]}')
            st.text(r["text"])
            st.text(r["out"])
            st.button("Open", key=f"{prefix}{i}", icon=":material/arrow_forward:", on_click=open_item, args=(r,))


if ss.view == "Translate":
    translate_view()
elif ss.view == "History":
    st.header("History")
    st.button("Clear history", on_click=clear_history)
    list_view(ss.history, "Your translations will show up here.", "h")
else:
    st.header("Saved translations")
    list_view(ss.favs, "Tap Save on a translation to keep it here.", "f")

import streamlit as st
import os
import json
import subprocess
import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv
import anthropic
import tempfile
import time

load_dotenv()

# ── page config ──────────────────────────────────────
st.set_page_config(
    page_title="ViralForge",
    page_icon="🎬",
    layout="wide"
)

# ── constants ────────────────────────────────────────
WIDTH, HEIGHT, FPS = 1920, 1080, 30

TEMPLATES = {
    "tech": {
        "bg": (10, 10, 10),
        "text": (0, 255, 136),
        "accent": (0, 102, 255),
        "font_size": 72,
        "search": "technology abstract dark"
    },
    "finance": {
        "bg": (10, 15, 30),
        "text": (255, 215, 0),
        "accent": (0, 204, 102),
        "font_size": 68,
        "search": "city skyline night"
    },
    "productivity": {
        "bg": (26, 26, 46),
        "text": (255, 255, 255),
        "accent": (233, 69, 96),
        "font_size": 70,
        "search": "minimal desk workspace"
    },
    "health": {
        "bg": (10, 30, 20),
        "text": (100, 255, 150),
        "accent": (0, 200, 100),
        "font_size": 70,
        "search": "nature green wellness"
    },
    "gaming": {
        "bg": (15, 10, 30),
        "text": (180, 100, 255),
        "accent": (255, 50, 100),
        "font_size": 70,
        "search": "gaming setup neon"
    },
    "education": {
        "bg": (20, 20, 35),
        "text": (255, 255, 255),
        "accent": (100, 150, 255),
        "font_size": 68,
        "search": "library books study"
    }
}

VOICE_MAP = {
    "Rachel (F, calm)":    "21m00Tcm4TlvDq8ikWAM",
    "Adam (M, confident)": "pNInz6obpgDQGcFmaJgB",
    "Domi (F, energetic)": "AZnzlk1XvdvUeBnXmlld",
    "Bella (F, warm)":     "EXAVITQu4vr4xnSDxMaL"
}

# ── sidebar ──────────────────────────────────────────
with st.sidebar:
    st.title("🎬 ViralForge")
    st.caption("Script → Voice → Video → Done")
    st.divider()

    st.subheader("API Keys")
    anthropic_key = st.text_input(
        "Anthropic Key",
        value=os.getenv("ANTHROPIC_API_KEY", ""),
        type="password"
    )
    elevenlabs_key = st.text_input(
        "ElevenLabs Key",
        value=os.getenv("ELEVENLABS_API_KEY", ""),
        type="password"
    )
    pexels_key = st.text_input(
        "Pexels Key",
        value=os.getenv("PEXELS_API_KEY", ""),
        type="password"
    )

    st.divider()
    st.subheader("Settings")

    niche = st.selectbox(
        "Niche",
        ["tech", "finance", "productivity",
         "health", "gaming", "education"]
    )
    voice = st.selectbox(
        "Voice",
        list(VOICE_MAP.keys())
    )
    bg_style = st.selectbox(
        "Background",
        ["Stock footage", "Pure black", "Dark gradient"]
    )

    keys_ready = all([anthropic_key, elevenlabs_key, pexels_key])

    st.divider()
    if keys_ready:
        st.success("✅ Ready")
    else:
        st.warning("⚠️ Add API keys")

# ── tabs ─────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "✍️ Script Mode",
    "🤖 Topic Mode",
    "📂 History"
])

# ════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════

def safe_filename(title: str) -> str:
    return "".join(
        c for c in title if c.isalnum() or c in " -_"
    )[:50].strip().replace(" ", "_")


def fetch_background(search: str, output_path: str):
    try:
        r = requests.get(
            "https://api.pexels.com/videos/search",
            headers={"Authorization": pexels_key},
            params={"query": search, "per_page": 3,
                    "orientation": "landscape"},
            timeout=15
        )
        videos = r.json().get("videos", [])
        if not videos:
            return None

        files = videos[0]["video_files"]
        hd = next(
            (f for f in files if f["quality"] == "hd"),
            files[0]
        )

        video_data = requests.get(hd["link"], stream=True, timeout=30)
        with open(output_path, "wb") as f:
            for chunk in video_data.iter_content(8192):
                f.write(chunk)
        return output_path
    except Exception as e:
        st.warning(f"Background fetch failed: {e}")
        return None


def make_slide(
    text: str,
    template: dict,
    slide_num: int,
    total: int,
    emphasis: bool,
    output_path: str
) -> str:
    img = Image.new("RGB", (WIDTH, HEIGHT), template["bg"])
    draw = ImageDraw.Draw(img)

    font_size = template["font_size"] + (20 if emphasis else 0)

    try:
        font = ImageFont.truetype(
            "/System/Library/Fonts/Helvetica.ttc", font_size
        )
        small_font = ImageFont.truetype(
            "/System/Library/Fonts/Helvetica.ttc", 28
        )
    except Exception:
        font = ImageFont.load_default()
        small_font = font

    accent = template["accent"]
    text_color = template["text"]

    # Top bar
    draw.rectangle([(0, 0), (WIDTH, 8)], fill=accent)

    # Progress bar
    progress = (slide_num + 1) / total
    draw.rectangle([(0, HEIGHT - 8), (WIDTH, HEIGHT)],
                   fill=(40, 40, 40))
    draw.rectangle(
        [(0, HEIGHT - 8), (int(WIDTH * progress), HEIGHT)],
        fill=accent
    )

    # Word wrap
    words = text.split()
    lines, line = [], []
    for word in words:
        line.append(word)
        bbox = draw.textbbox((0, 0), " ".join(line), font=font)
        if bbox[2] > WIDTH - 160:
            line.pop()
            if line:
                lines.append(" ".join(line))
            line = [word]
    if line:
        lines.append(" ".join(line))

    # Center text
    line_h = font_size + 16
    total_h = len(lines) * line_h
    y = (HEIGHT - total_h) // 2

    for ln in lines:
        bbox = draw.textbbox((0, 0), ln, font=font)
        x = (WIDTH - (bbox[2] - bbox[0])) // 2
        draw.text((x + 3, y + 3), ln, font=font,
                  fill=(0, 0, 0))
        draw.text((x, y), ln, font=font, fill=text_color)
        y += line_h

    img.save(output_path, "PNG")
    return output_path


def generate_voice(text: str, voice_id: str,
                   output_path: str) -> str:
    response = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        headers={
            "xi-api-key": elevenlabs_key,
            "Content-Type": "application/json"
        },
        json={
            "text": text,
            "model_id": "eleven_turbo_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        },
        timeout=30
    )

    if response.status_code != 200:
        raise Exception(f"ElevenLabs error: {response.text}")

    with open(output_path, "wb") as f:
        f.write(response.content)
    return output_path


def build_video(
    slides: list,
    audio_path: str,
    bg_path,
    template: dict,
    output_path: str,
    work_dir: str
) -> str:
    slide_files = []

    for i, slide in enumerate(slides):
        slide_path = os.path.join(work_dir, f"slide_{i:03d}.png")
        make_slide(
            text=slide["text"],
            template=template,
            slide_num=i,
            total=len(slides),
            emphasis=slide.get("emphasis", False),
            output_path=slide_path
        )
        slide_files.append((slide_path, slide.get("duration", 4)))

    # Concat file
    concat_path = os.path.join(work_dir, "concat.txt")
    with open(concat_path, "w") as f:
        for path, dur in slide_files:
            f.write(f"file '{path}'\n")
            f.write(f"duration {dur}\n")

    # Slides → video
    slides_mp4 = os.path.join(work_dir, "slides.mp4")
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_path,
        "-vf", f"scale={WIDTH}:{HEIGHT},format=yuv420p",
        "-r", str(FPS),
        slides_mp4
    ], check=True, capture_output=True)

    # Final assembly
    if bg_path and os.path.exists(bg_path):
        subprocess.run([
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-i", bg_path,
            "-i", slides_mp4,
            "-i", audio_path,
            "-filter_complex",
            "[0:v]scale=1920:1080[bg];"
            "[1:v]format=rgba,colorchannelmixer=aa=0.85[ov];"
            "[bg][ov]overlay=0:0[v]",
            "-map", "[v]", "-map", "2:a",
            "-shortest",
            "-c:v", "libx264", "-c:a", "aac",
            "-crf", "23", output_path
        ], check=True, capture_output=True)
    else:
        subprocess.run([
            "ffmpeg", "-y",
            "-i", slides_mp4,
            "-i", audio_path,
            "-c:v", "libx264", "-c:a", "aac",
            "-shortest", output_path
        ], check=True, capture_output=True)

    return output_path


def call_claude(prompt: str) -> str:
    client = anthropic.Anthropic(api_key=anthropic_key)
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text


def parse_claude_json(raw: str) -> dict:
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0]
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0]
    return json.loads(raw.strip())


def script_from_topic(topic: str, style: str,
                      niche: str) -> dict:
    prompt = f"""Write a 60-second YouTube script about: "{topic}"
Niche: {niche}
{f'Creator style: {style}' if style else ''}

Return ONLY valid JSON:
{{
    "title": "compelling title under 60 chars",
    "description": "150 word YouTube description",
    "tags": ["tag1","tag2","tag3","tag4","tag5"],
    "hook_angle": "what makes this surprising or different",
    "slides": [
        {{"text": "hook 6 words max", "duration": 3, "emphasis": true}},
        {{"text": "point one 8 words max", "duration": 5, "emphasis": false}},
        {{"text": "point two 8 words max", "duration": 5, "emphasis": false}},
        {{"text": "point three 8 words max", "duration": 5, "emphasis": false}},
        {{"text": "surprising stat or fact", "duration": 4, "emphasis": true}},
        {{"text": "subscribe for more", "duration": 3, "emphasis": false}}
    ],
    "full_voiceover": "complete natural spoken script 120 words"
}}"""
    return parse_claude_json(call_claude(prompt))


def script_from_user(script_text: str, visual_text: str,
                     title: str, niche: str) -> dict:
    prompt = f"""Structure this into a YouTube video script.

USER'S SCRIPT:
{script_text}

USER'S VISUAL NOTES:
{visual_text if visual_text else "Use good judgment based on the script"}

TITLE: {title if title else "Generate a good title"}
NICHE: {niche}

Return ONLY valid JSON:
{{
    "title": "{title if title else 'generated title'}",
    "description": "150 word YouTube description",
    "tags": ["tag1","tag2","tag3","tag4","tag5"],
    "hook_angle": "the core angle of this video",
    "slides": [
        {{"text": "short screen text max 8 words", "duration": 4, "emphasis": true}},
        {{"text": "next slide text", "duration": 5, "emphasis": false}}
    ],
    "full_voiceover": "the complete spoken script using the user's exact words and style"
}}

Use the user's actual words and voice in the voiceover.
Keep slide text short - it appears on screen.
Create as many slides as needed to cover the full script."""
    return parse_claude_json(call_claude(prompt))

# ════════════════════════════════════════════════════
# MAIN PIPELINE
# ════════════════════════════════════════════════════

def run_pipeline(script_data: dict, label: str):
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    progress = st.progress(0)
    status = st.empty()
    template = TEMPLATES[niche]
    voice_id = VOICE_MAP[voice]
    fname = safe_filename(script_data["title"])

    with tempfile.TemporaryDirectory() as work_dir:

        # Step 1: Voice
        status.info("🎙️ Generating voiceover...")
        progress.progress(20)
        audio_path = os.path.join(work_dir, "voice.mp3")
        try:
            generate_voice(
                script_data["full_voiceover"],
                voice_id,
                audio_path
            )
        except Exception as e:
            st.error(f"Voice failed: {e}")
            return

        # Step 2: Background
        status.info("🎬 Fetching background...")
        progress.progress(40)
        bg_path = None
        if bg_style == "Stock footage":
            bg_path = os.path.join(work_dir, "bg.mp4")
            bg_path = fetch_background(
                template["search"], bg_path
            )

        # Step 3: Build video
        status.info("🎞️ Assembling video...")
        progress.progress(60)
        output_path = str(output_dir / f"{fname}.mp4")
        try:
            build_video(
                slides=script_data["slides"],
                audio_path=audio_path,
                bg_path=bg_path,
                template=template,
                output_path=output_path,
                work_dir=work_dir
            )
        except Exception as e:
            st.error(f"Video build failed: {e}")
            return

        # Step 4: Done
        progress.progress(100)
        status.success(f"✅ Done: {script_data['title']}")

        with st.expander("📄 Script Details"):
            st.write(f"**Title:** {script_data['title']}")
            st.write(f"**Hook:** {script_data.get('hook_angle','')}")
            st.write(f"**Description:** {script_data['description']}")
            st.write(f"**Tags:** {', '.join(script_data['tags'])}")

        with open(output_path, "rb") as f:
            st.download_button(
                "⬇️ Download Video",
                f,
                file_name=f"{fname}.mp4",
                mime="video/mp4"
            )


# ════════════════════════════════════════════════════
# TAB 1: SCRIPT MODE
# ════════════════════════════════════════════════════
with tab1:
    st.header("Your Script → Your Video")
    st.caption("You write it. The pipeline builds it.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📝 Your Script")
        script_input = st.text_area(
            "script",
            height=350,
            placeholder="""[HOOK]
Everyone says to use AI for productivity.
They're wrong about how.
duration: 3s
emphasis: high

[POINT 1]
Most people use ChatGPT like Google.
That's the worst way to use it.
duration: 8s

[STAT]
I cut my writing time by 70%.
Not by asking AI to write for me.
duration: 5s
emphasis: high

[CTA]
Try it on your next piece of work.
Tell me what breaks.
duration: 4s""",
            label_visibility="collapsed"
        )
        video_title = st.text_input(
            "Video title",
            placeholder="Why I stopped using AI the way everyone says to"
        )

    with col2:
        st.subheader("🎨 Visual Brief (optional)")
        visual_input = st.text_area(
            "visual",
            height=350,
            placeholder="""[HOOK]
visual: black screen, single word "Wrong."
feel: stark, confident

[POINT 1]
visual: split screen, wrong way vs right way
feel: clear contrast

[STAT]
visual: big number 70% center screen
feel: let it breathe

[CTA]
visual: just text, no clutter
feel: direct, like a text message""",
            label_visibility="collapsed"
        )

    st.divider()

    if st.button(
        "🎬 Generate Video",
        type="primary",
        disabled=not keys_ready,
        use_container_width=True
    ):
        if not script_input.strip():
            st.error("Add your script first")
        else:
            with st.spinner("Working..."):
                try:
                    script_data = script_from_user(
                        script_input,
                        visual_input,
                        video_title,
                        niche
                    )
                    run_pipeline(script_data, "Script Mode")
                except Exception as e:
                    st.error(f"Failed: {e}")


# ════════════════════════════════════════════════════
# TAB 2: TOPIC MODE
# ════════════════════════════════════════════════════
with tab2:
    st.header("Topic → Automated Video")
    st.caption("Type a topic. Get a video.")

    col1, col2 = st.columns([2, 1])

    with col1:
        topics_input = st.text_area(
            "Topics (one per line)",
            height=200,
            placeholder="""Why most people use AI wrong
The productivity system nobody talks about
5 tools that replaced my entire workflow"""
        )

    with col2:
        st.subheader("Settings")
        videos_per_run = st.slider(
            "Videos to generate", 1, 10, 1
        )
        your_style = st.text_area(
            "Your style (optional)",
            height=100,
            placeholder="""Direct, skip the fluff.
Specific examples not vague claims.
Skeptical of hype."""
        )
        cost = videos_per_run * 0.22
        st.info(f"Est. cost: ${cost:.2f}")

    st.divider()

    if st.button(
        "🤖 Generate Videos",
        type="primary",
        disabled=not keys_ready,
        use_container_width=True
    ):
        topics = [
            t.strip() for t in topics_input.split("\n")
            if t.strip()
        ]
        if not topics:
            st.error("Add at least one topic")
        else:
            for topic in topics[:videos_per_run]:
                st.subheader(f"📹 {topic}")
                try:
                    script_data = script_from_topic(
                        topic, your_style, niche
                    )
                    run_pipeline(script_data, topic)
                except Exception as e:
                    st.error(f"Failed on '{topic}': {e}")


# ════════════════════════════════════════════════════
# TAB 3: HISTORY
# ════════════════════════════════════════════════════
with tab3:
    st.header("Generated Videos")

    output_dir = Path("output")
    if output_dir.exists():
        videos = sorted(
            output_dir.glob("*.mp4"),
            key=os.path.getmtime,
            reverse=True
        )

        if videos:
            for video_path in videos[:20]:
                col1, col2 = st.columns([4, 1])
                with col1:
                    size = video_path.stat().st_size
                    st.write(f"🎬 {video_path.stem}")
                    st.caption(f"{size/1024/1024:.1f} MB")
                with col2:
                    with open(video_path, "rb") as f:
                        st.download_button(
                            "⬇️ Download",
                            f,
                            file_name=video_path.name,
                            mime="video/mp4",
                            key=str(video_path)
                        )
        else:
            st.info("No videos yet.")
    else:
        st.info("No videos yet.")

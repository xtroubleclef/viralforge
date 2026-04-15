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


def fetch_background(search: str, output_path: str) -> str | None:
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
    bg_path: str | None,
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

    with tempfile.TemporaryDirectory

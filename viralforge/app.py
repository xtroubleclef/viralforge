import streamlit as st
import os
import json
import tempfile
import shutil
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── page config ──────────────────────────────────────
st.set_page_config(
    page_title="ViralForge",
    page_icon="🎬",
    layout="wide"
)

# ── sidebar: api keys ────────────────────────────────
with st.sidebar:
    st.title("🎬 ViralForge")
    st.caption("Script → Voice → Video → Done")
    
    st.divider()
    st.subheader("API Keys")
    
    anthropic_key = st.text_input(
        "Anthropic Key",
        value=os.getenv("ANTHROPIC_API_KEY", ""),
        type="password",
        help="anthropic.com → API Keys"
    )
    elevenlabs_key = st.text_input(
        "ElevenLabs Key",
        value=os.getenv("ELEVENLABS_API_KEY", ""),
        type="password",
        help="elevenlabs.io → Profile → API Key"
    )
    pexels_key = st.text_input(
        "Pexels Key",
        value=os.getenv("PEXELS_API_KEY", ""),
        type="password",
        help="pexels.com/api → free"
    )
    
    st.divider()
    st.subheader("Video Settings")
    
    niche = st.selectbox(
        "Niche",
        ["tech", "finance", "productivity", 
         "health", "gaming", "education"]
    )
    
    voice = st.selectbox(
        "Voice",
        ["Rachel (F, calm)", 
         "Adam (M, confident)",
         "Domi (F, energetic)",
         "Bella (F, warm)"]
    )
    
    resolution = st.selectbox(
        "Resolution",
        ["1920x1080 (YouTube)", 
         "1080x1920 (Shorts/TikTok)"]
    )
    
    keys_ready = all([anthropic_key, 
                      elevenlabs_key, 
                      pexels_key])
    
    if keys_ready:
        st.success("✅ Ready to generate")
    else:
        st.warning("⚠️ Add API keys to start")

# ── main tabs ────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "✍️  Script Mode", 
    "🤖 Topic Mode",
    "📊 History"
])

# ════════════════════════════════════════════════════
# TAB 1: SCRIPT MODE
# ════════════════════════════════════════════════════
with tab1:
    st.header("Your Script → Your Video")
    st.caption("You write it. The pipeline builds it.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📝 Your Script")
        st.caption("Write exactly how you'd say it")
        
        script_input = st.text_area(
            "Script",
            height=400,
            placeholder="""[HOOK]
Everyone says to use AI for productivity.
They're wrong about how.
duration: 3s
emphasis: high

[POINT 1]
Most people use ChatGPT like Google.
They ask it questions and take the answer.
That's the worst way to use it.
duration: 8s
emphasis: low

[STAT]
I cut my writing time by 70%.
Not by asking AI to write for me.
duration: 5s
emphasis: high

[CTA]
Try it on your next piece of work.
Tell me what breaks.
duration: 4s
emphasis: medium""",
            label_visibility="collapsed"
        )
        
        video_title = st.text_input(
            "Video Title",
            placeholder="Why I stopped using AI the way everyone says to"
        )
    
    with col2:
        st.subheader("🎨 Visual Brief")
        st.caption("Describe what you want people to see")
        
        visual_input = st.text_area(
            "Visual Brief",
            height=400,
            placeholder="""[HOOK]
visual: black screen, single word "Wrong."
feel: stark, confident, not trying hard

[POINT 1]
visual: split screen, left side normal 
ChatGPT use, right side red X
feel: this is what not to do

[STAT]
visual: big number "70%" center screen
below: smaller text "less time writing"
feel: let the number breathe

[CTA]
visual: just text, no background noise
feel: direct, like a friend texting you""",
            label_visibility="collapsed"
        )
        
        st.subheader("🎯 Style")
        
        col_a, col_b = st.columns(2)
        with col_a:
            bg_style = st.selectbox(
                "Background",
                ["Dark minimal", 
                 "Stock footage",
                 "Pure black",
                 "Pure white",
                 "Gradient"]
            )
        with col_b:
            caption_style = st.selectbox(
                "Captions",
                ["Synced word-by-word",
                 "Slide text only",
                 "None"]
            )
    
    st.divider()
    
    generate_script_btn = st.button(
        "🎬 Generate Video From My Script",
        type="primary",
        disabled=not keys_ready,
        use_container_width=True
    )
    
    if generate_script_btn:
        if not script_input:
            st.error("Add your script first")
        else:
            run_pipeline(
                mode="script",
                script_text=script_input,
                visual_text=visual_input,
                title=video_title,
                niche=niche,
                voice=voice,
                resolution=resolution,
                bg_style=bg_style,
                caption_style=caption_style,
                anthropic_key=anthropic_key,
                elevenlabs_key=elevenlabs_key,
                pexels_key=pexels_key
            )

# ════════════════════════════════════════════════════
# TAB 2: TOPIC MODE
# ════════════════════════════════════════════════════
with tab2:
    st.header("Topic → Automated Video")
    st.caption("Fully automated. Good for volume.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        topics_input = st.text_area(
            "Topics (one per line)",
            height=200,
            placeholder="""Why most people use AI wrong
The productivity system nobody talks about
5 tools that replaced my entire workflow
Why expensive keyboards are a scam
The morning routine that actually works"""
        )
    
    with col2:
        st.subheader("Batch Settings")
        
        videos_per_run = st.slider(
            "Videos to generate",
            min_value=1,
            max_value=20,
            value=3
        )
        
        your_style = st.text_area(
            "Your style (optional but recommended)",
            height=120,
            placeholder="""Direct, skip the fluff.
Use specific examples not vague claims.
Skeptical of hype, call things out.
Swear occasionally (mild)."""
        )
        
        cost_estimate = videos_per_run * 0.22
        st.info(f"Est. cost: ${cost_estimate:.2f}")
    
    generate_topic_btn = st.button(
        "🤖 Generate Videos",
        type="primary",
        disabled=not keys_ready,
        use_container_width=True
    )
    
    if generate_topic_btn:
        topics = [t.strip() for t in 
                  topics_input.split("\n") 
                  if t.strip()]
        
        if not topics:
            st.error("Add at least one topic")
        else:
            topics_to_run = topics[:videos_per_run]
            
            for i, topic in enumerate(topics_to_run):
                st.subheader(f"Video {i+1}: {topic}")
                run_pipeline(
                    mode="topic",
                    topic=topic,
                    your_style=your_style,
                    niche=niche,
                    voice=voice,
                    resolution=resolution,
                    anthropic_key=anthropic_key,
                    elevenlabs_key=elevenlabs_key,
                    pexels_key=pexels_key
                )

# ════════════════════════════════════════════════════
# TAB 3: HISTORY
# ════════════════════════════════════════════════════
with tab3:
    st.header("Generated Videos")
    
    output_dir = Path("output")
    if output_dir.exists():
        videos = list(output_dir.glob("*.mp4"))
        
        if videos:
            for video_path in sorted(
                videos, 
                key=os.path.getmtime, 
                reverse=True
            )[:10]:
                col1, col2, col3 = st.columns([3,1,1])
                
                with col1:
                    st.write(f"🎬 {video_path.stem}")
                    size = video_path.stat().st_size
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
                
                with col3:
                    st.button(
                        "📤 Upload to YT",
                        key=f"upload_{video_path}",
                        disabled=True,
                        help="Coming soon"
                    )
        else:
            st.info("No videos yet. Generate some first.")
    else:
        st.info("No videos yet. Generate some first.")


# ════════════════════════════════════════════════════
# PIPELINE RUNNER
# ════════════════════════════════════════════════════
def run_pipeline(mode: str, **kwargs):
    """Runs the full pipeline with progress UI"""
    
    import anthropic
    import requests
    from PIL import Image, ImageDraw, ImageFont
    import subprocess
    
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Progress UI
    progress = st.progress(0)
    status = st.empty()
    
    try:
        # ── STEP 1: Script ───────────────────────────
        status.info("✍️  Step 1/4: Preparing script...")
        progress.progress(10)
        
        if mode == "script":
            script_data = parse_user_script(
                kwargs["script_text"],
                kwargs.get("visual_text", ""),
                kwargs["title"],
                kwargs["anthropic_key"]
            )
        else:
            script_data = generate_topic_script(
                kwargs["topic"],
                kwargs.get("your_style", ""),
                kwargs["niche"],
                kwargs["anthropic_key"]
            )
        
        progress.progress(25)
        
        # Show script preview
        with st.expander("📄 Script Preview"):
            st.write(f"**Title:** {script_data['title']}")
            st.write(f"**Hook angle:** {script_data.get('hook_angle', 'N/A')}")
            for i, slide in enumerate(script_data['slides']):
                st.write(f"Slide {i+1}: {slide['text']}")
        
        # ── STEP 2: Voice ────────────────────────────
        status.info("🎙️  Step 2/4: Generating voiceover...")
        progress.progress(35)
        
        voice_map = {
            "Rachel (F, calm)":      "21m00Tcm4TlvDq8ikWAM",
            "Adam (M, confident)":   "pNInz6obpgDQGcFmaJgB",
            "Domi (F, energetic)":   "AZnzlk1XvdvUeBnXmlld",
            "Bella (F, warm)":       "EXAVITQu4vr4xnSDxMaL"
        }
        
        voice_id = voice_map.get(
            kwargs.get("voice", "Rachel (F, calm)"),
            "21m00Tcm4TlvDq8ikWAM"
        )
        
        safe_title = "".join(
            c for c in script_data["title"] 
            if c.isalnum() or c in " -_"
        )[:50]
        
        audio_path = str(output_dir / f"{safe_title}.mp3")
        
        voice_response = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={
                "xi-api-key": kwargs["elevenlabs_key"],
                "Content-Type": "application/json"
            },
            json={
                "text": script_data["full_voiceover"],
                "model_id": "eleven_turbo_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }
        )
        
        if voice_response.status_code != 200:
            st.error(f"Voice failed: {voice_response.text}")
            return
        
        with open(audio_path, "wb") as f:
            f.write(voice_response.content)
        
        progress.progress(50)
        
        # ── STEP 3: Visuals ──────────────────────────
        status.info("🎨  Step 3/4: Building visuals...")
        progress.progress(55)
        
        # Get background if stock footage selected
        bg_path = None
        if kwargs.get("bg_style") == "Stock footage":
            bg_path = str(output_dir / f"{safe_title}_bg.mp4")
            bg_path = fetch_background(
                script_data.get("bg_search", "abstract dark"),
                bg_path,
                kwargs["pex

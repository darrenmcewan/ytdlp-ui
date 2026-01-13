import streamlit as st
import yt_dlp
import os
import shutil
from pathlib import Path

st.set_page_config(page_title="yt-dlp Downloader", page_icon="🎥", layout="wide")

st.title("🎥 Video Downloader")
st.markdown("Download videos using yt-dlp with customizable options")

# Check for ffmpeg
ffmpeg_available = shutil.which('ffmpeg') is not None
if not ffmpeg_available:
    st.warning("⚠️ **ffmpeg not found!** Audio conversion and format merging will not work. Please install ffmpeg or provide the path below.")
    ffmpeg_path = st.text_input("FFmpeg Location (optional)", placeholder="/path/to/ffmpeg/bin")
else:
    ffmpeg_path = None

# Create output directory
OUTPUT_DIR = Path("downloads")
OUTPUT_DIR.mkdir(exist_ok=True)

# URL input
url = st.text_input("Enter video URL:", placeholder="https://www.youtube.com/watch?v=...")

if url:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Download Options")
        
        # Format selection
        if ffmpeg_available or ffmpeg_path:
            format_options = ["Best Quality (Video + Audio)", "Video (MP4)", "Audio Only (MP3)", "Audio Only (M4A)", 
                            "Video Only (No Audio)", "Best Single File", "Custom Format"]
        else:
            format_options = ["Best Single File (No ffmpeg required)", "Video (MP4 - No Audio Merge)", 
                            "Video Only (No Audio)", "Custom Format"]
            st.info("ℹ️ Limited formats available without ffmpeg. Install ffmpeg for more options.")
        
        format_option = st.selectbox("Format", format_options)
        
        # Resolution for video
        if "Audio Only" not in format_option:
            resolution = st.selectbox(
                "Max Resolution",
                ["Best Available", "2160p (4K)", "1440p", "1080p", "720p", "480p", "360p"]
            )
        
        # Custom format code
        if format_option == "Custom Format":
            custom_format = st.text_input(
                "Format Code", 
                placeholder="e.g., bestvideo+bestaudio",
                help="See yt-dlp format documentation"
            )
    
    with col2:
        st.subheader("Additional Options")
        
        # Filename template
        output_template = st.text_input(
            "Filename Template",
            value="%(title)s.%(ext)s",
            help="Use yt-dlp output template syntax"
        )
        
        # Speed control
        if ffmpeg_available or ffmpeg_path:
            enable_speed = st.checkbox("Adjust Playback Speed", help="Change video/audio speed without affecting pitch")
            if enable_speed:
                speed_factor = st.slider(
                    "Speed Factor",
                    min_value=0.25,
                    max_value=4.0,
                    value=1.0,
                    step=0.25,
                    help="1.0 = normal speed, 2.0 = 2x faster, 0.5 = half speed"
                )
                st.caption(f"Playback speed: {speed_factor}x")
        else:
            enable_speed = False
        
        # Subtitles
        download_subs = st.checkbox("Download Subtitles")
        if download_subs:
            sub_lang = st.text_input("Subtitle Language", value="en", help="e.g., en, es, fr")
        
        # Thumbnail
        embed_thumbnail = st.checkbox("Embed Thumbnail")
        
        # Metadata
        embed_metadata = st.checkbox("Embed Metadata", value=True)
    
    # Download button
    if st.button("📥 Download", type="primary", use_container_width=True):
        try:
            with st.spinner("Downloading..."):
                # Build yt-dlp options
                ydl_opts = {
                    'outtmpl': str(OUTPUT_DIR / output_template),
                    'progress_hooks': [],
                }
                
                # Add ffmpeg location if provided
                if ffmpeg_path:
                    ydl_opts['ffmpeg_location'] = ffmpeg_path
                
                # Format selection
                if format_option == "Best Quality (Video + Audio)":
                    ydl_opts['format'] = 'bestvideo+bestaudio/best'
                    ydl_opts['merge_output_format'] = 'mp4'
                elif format_option == "Video (MP4)" or format_option == "Video (MP4 - No Audio Merge)":
                    ydl_opts['format'] = 'best[ext=mp4]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best'
                    ydl_opts['merge_output_format'] = 'mp4'
                elif format_option == "Best Single File" or format_option == "Best Single File (No ffmpeg required)":
                    ydl_opts['format'] = 'best'
                elif format_option == "Audio Only (MP3)":
                    ydl_opts['format'] = 'bestaudio/best'
                    ydl_opts['postprocessors'] = [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }]
                elif format_option == "Audio Only (M4A)":
                    ydl_opts['format'] = 'bestaudio/best'
                    ydl_opts['postprocessors'] = [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'm4a',
                    }]
                elif format_option == "Video Only (No Audio)":
                    ydl_opts['format'] = 'bestvideo'
                elif format_option == "Custom Format":
                    ydl_opts['format'] = custom_format if custom_format else 'best'
                
                # Resolution limit
                if "Audio Only" not in format_option and resolution != "Best Available":
                    height = resolution.replace('p', '').replace(' (4K)', '')
                    ydl_opts['format'] = f'bestvideo[height<={height}]+bestaudio/best[height<={height}]'
                
                # Speed adjustment using FFmpeg filters
                if enable_speed and speed_factor != 1.0:
                    ydl_opts['postprocessors'] = ydl_opts.get('postprocessors', [])
                    
                    # Build atempo chain for audio (atempo is limited to 0.5-100.0 per filter)
                    atempo_filters = []
                    remaining_speed = speed_factor
                    
                    # Handle speeds outside single atempo range
                    while remaining_speed > 2.0:
                        atempo_filters.append("atempo=2.0")
                        remaining_speed /= 2.0
                    while remaining_speed < 0.5:
                        atempo_filters.append("atempo=0.5")
                        remaining_speed /= 0.5
                    
                    # Add final atempo filter for remaining speed adjustment
                    if remaining_speed != 1.0:
                        atempo_filters.append(f"atempo={remaining_speed}")
                    
                    audio_filter = ",".join(atempo_filters)
                    
                    # Video filter: setpts (inverse of speed factor)
                    video_filter = f"setpts={1/speed_factor}*PTS"
                    
                    # Build FFmpeg arguments for speed adjustment
                    speed_args = []
                    if format_option == "Audio Only (MP3)" or format_option == "Audio Only (M4A)":
                        # Audio only - just apply atempo
                        speed_args = ['-af', audio_filter]
                    elif format_option == "Video Only (No Audio)":
                        # Video only - just apply setpts
                        speed_args = ['-vf', video_filter]
                    else:
                        # Both video and audio
                        speed_args = ['-vf', video_filter, '-af', audio_filter]
                    
                    # Insert speed adjustment postprocessor
                    ydl_opts['postprocessors'].insert(0, {
                        'key': 'FFmpegVideoConvertor',
                        'preferedformat': 'mp4',
                    })
                    ydl_opts['postprocessor_args'] = {
                        'FFmpegVideoConvertor': speed_args
                    }
                
                # Subtitles
                if download_subs:
                    ydl_opts['writesubtitles'] = True
                    ydl_opts['subtitleslangs'] = [sub_lang]
                
                # Thumbnail
                if embed_thumbnail:
                    ydl_opts['writethumbnail'] = True
                    ydl_opts['postprocessors'] = ydl_opts.get('postprocessors', [])
                    ydl_opts['postprocessors'].append({
                        'key': 'EmbedThumbnail',
                    })
                
                # Metadata
                if embed_metadata:
                    ydl_opts['postprocessors'] = ydl_opts.get('postprocessors', [])
                    ydl_opts['postprocessors'].append({
                        'key': 'FFmpegMetadata',
                    })
                
                # Download
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info)
                    
                    # Handle audio conversion filename change
                    if format_option in ["Audio Only (MP3)", "Audio Only (M4A)"]:
                        base = os.path.splitext(filename)[0]
                        ext = 'mp3' if 'MP3' in format_option else 'm4a'
                        filename = f"{base}.{ext}"
                
                st.success("✅ Download completed!")
                
                # Provide download link
                if os.path.exists(filename):
                    with open(filename, 'rb') as f:
                        st.download_button(
                            label="💾 Download File",
                            data=f,
                            file_name=os.path.basename(filename),
                            mime="application/octet-stream"
                        )
                    
                    # Display info
                    speed_info = f"\n\n**Speed:** {speed_factor}x" if enable_speed and speed_factor != 1.0 else ""
                    st.info(f"**Title:** {info.get('title', 'N/A')}\n\n"
                           f"**Duration:** {info.get('duration', 0) // 60}m {info.get('duration', 0) % 60}s"
                           f"{speed_info}\n\n"
                           f"**Uploader:** {info.get('uploader', 'N/A')}")
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# Info section
with st.expander("ℹ️ How to use"):
    st.markdown("""
    1. **Paste a video URL** from supported sites (YouTube, Vimeo, etc.)
    2. **Select your preferred format** and quality settings
    3. **Customize options** like subtitles, metadata, and playback speed
    4. **Click Download** and wait for processing
    5. **Download the file** using the download button
    
    **Speed Control:**
    - Adjust playback speed from 0.25x (slower) to 4x (faster)
    - Audio pitch is preserved using the `atempo` filter
    - Video frames are adjusted using the `setpts` filter
    - Speed adjustment requires FFmpeg
    
    **Installation Requirements:**
    
    ```bash
    pip install yt-dlp streamlit
    ```
    
    **FFmpeg Installation (Required for audio conversion and merging formats):**
    
    - **Windows:** 
      - Download from https://ffmpeg.org/download.html
      - Or use: `choco install ffmpeg` (with Chocolatey)
      - Or use: `winget install ffmpeg` (Windows 10/11)
    
    - **Mac:** 
      ```bash
      brew install ffmpeg
      ```
    
    - **Linux (Ubuntu/Debian):** 
      ```bash
      sudo apt update && sudo apt install ffmpeg
      ```
    
    - **Linux (Fedora):** 
      ```bash
      sudo dnf install ffmpeg
      ```
    
    After installing, restart the Streamlit app.
    
    **Without ffmpeg:** You can still download videos using "Best Single File" format.
    """)

# Footer
st.markdown("---")
st.markdown("Powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp)")
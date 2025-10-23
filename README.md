## Prerequisites

To run this application, you need Python and the required libraries. For full functionality (merging video/audio streams, speed control, audio conversion), you must also install FFmpeg.

1. Python Requirements

Install the Python libraries using pip and the generated requirements.txt:


pip install -r requirements.txt



2. Install FFmpeg (Highly Recommended)

FFmpeg is required for:

- Merging separate video and audio streams (for "Best Quality").

- Converting to MP3 or M4A (for "Audio Only").

- Adjusting Playback Speed.

If FFmpeg is not found in your system's PATH, the app will offer limited functionality, or you will need to manually provide the FFmpeg location in the app interface.


## Usage

1. Paste the URL of the video you wish to download into the text box.

2. Select your desired Format and Max Resolution.

3. Adjust Additional Options (Filename Template, Playback Speed, Subtitles, Metadata).

Note: If you enable Adjust Playback Speed, the app uses complex FFmpeg filters (setpts for video and atempo for audio) to ensure the audio pitch remains normal while the playback speed changes.

4. Click the 📥 Download button.

5. Once the process is complete, a success message and a 💾 Download File button will appear. The downloaded files are saved locally in a directory named downloads/.

## Speed Change
In the downloads folder is a shell script named speed_change.sh.

Run this to change the speed of the files in your downloads folder. Great for audiobooks/podcasts
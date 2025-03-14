#!/usr/bin/env python3
import subprocess
import sys
import shutil

def download_audio(video_url):
    # Check if yt-dlp is installed
    if not shutil.which("yt-dlp"):
        print("Error: yt-dlp is not installed or not in PATH")
        sys.exit(1)
    
    # Check if ffmpeg is installed
    if not shutil.which("ffmpeg"):
        print("Error: ffmpeg is not installed or not in PATH")
        sys.exit(1)
    
    # Verify URL is provided
    if not video_url:
        print("Error: Please provide a YouTube URL in the script")
        sys.exit(1)
    
    # Construct the yt-dlp command to download audio as MP3
    command = ["yt-dlp", "-x", "--audio-format", "mp3", "--no-playlist", video_url]
    
    # Run the command and let yt-dlp output progress to the console
    result = subprocess.run(command)
    
    # Check if the download was successful
    if result.returncode == 0:
        print("Download completed successfully")
    else:
        print("Download failed")

def main():
    # Set your YouTube URL here directly in the code
    video_url = "https://youtu.be/2cpd1fsUQ1I?si=typw8zoYZS5dIcRb"
    
    # Call the download function with the URL
    download_audio(video_url)

if __name__ == "__main__":
    main()
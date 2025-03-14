#!/bin/bash

# Combine video and audio files with high quality output
# Usage: ./combine_media.sh video_file audio_file output_file

# Check if ffmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "Error: ffmpeg is not installed. Please install it first."
    echo "Ubuntu/Debian: sudo apt install ffmpeg"
    echo "macOS: brew install ffmpeg"
    echo "Windows: download from https://ffmpeg.org/download.html"
    exit 1
fi

# Check if correct number of arguments
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 video_file audio_file output_file"
    echo "Example: $0 input.mp4 input.mp3 output.mp4"
    exit 1
fi

VIDEO_FILE="$1"
AUDIO_FILE="$2"
OUTPUT_FILE="$3"

# Check if input files exist
if [ ! -f "$VIDEO_FILE" ]; then
    echo "Error: Video file '$VIDEO_FILE' does not exist."
    exit 1
fi

if [ ! -f "$AUDIO_FILE" ]; then
    echo "Error: Audio file '$AUDIO_FILE' does not exist."
    exit 1
fi

# Get file extension for output
OUTPUT_EXT="${OUTPUT_FILE##*.}"

# Optimized ffmpeg command for high quality output
echo "Combining video '$VIDEO_FILE' with audio '$AUDIO_FILE'..."
ffmpeg -i "$VIDEO_FILE" -i "$AUDIO_FILE" -c:v copy -c:a aac -b:a 320k -map 0:v:0 -map 1:a:0 -shortest "$OUTPUT_FILE"

# Check if the command was successful
if [ $? -eq 0 ]; then
    echo "Success! Combined file saved as '$OUTPUT_FILE'"
    echo "Command used: ffmpeg -i $VIDEO_FILE -i $AUDIO_FILE -c:v copy -c:a aac -b:a 320k -map 0:v:0 -map 1:a:0 -shortest $OUTPUT_FILE"
else
    echo "Error: Failed to combine files."
    exit 1
fi


# ./combine_media.sh heyy.mp4 @dep-daily-english-podcast.mp3 output_file.mp4
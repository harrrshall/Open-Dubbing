import subprocess
import sys
import os
import re
import threading
import queue
import time
import transcribe_audio
import video_dub


# Utility Functions
def get_unique_filename(base_name, extension):
    """
    Ensure the output filename is unique by appending a counter if the file already exists.
    
    Args:
        base_name (str): Base name for the file.
        extension (str): File extension (e.g., 'mp4').
    
    Returns:
        str: A unique filename.
    """
    counter = 1
    unique_name = f"{base_name}.{extension}"
    while os.path.exists(unique_name):
        unique_name = f"{base_name}_{counter}.{extension}"
        counter += 1
    return unique_name


def sanitize_filename(name):
    """
    Sanitize a string to be safe for filenames.
    
    Args:
        name (str): The string to sanitize.
    
    Returns:
        str: A sanitized string with only alphanumeric characters, underscores, and hyphens.
    """
    name = name.replace(' ', '_')  # Replace spaces with underscores
    name = re.sub(r'[^\w\-]', '', name)  # Keep alphanumeric, underscores, and hyphens
    return name


def get_sanitized_channel(url):
    """
    Fetch and sanitize the YouTube channel name for a given video URL.
    
    Args:
        url (str): The YouTube video URL.
    
    Returns:
        str or None: Sanitized channel name, or None if retrieval fails.
    """
    command = ["yt-dlp", "--print", "channel", url]
    result = subprocess.run(command, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error getting channel for {url}: {result.stderr.strip()}")
        return None
    
    channel = result.stdout.strip()
    if not channel:
        print(f"No channel name retrieved for {url}")
        return None
    
    return sanitize_filename(channel)


def cleanup_temp_files(temp_files):
    """
    Delete temporary files created during processing.
    
    Args:
        temp_files (list): List of file paths to delete.
    """
    print("Cleaning up temporary files...")
    for file_path in temp_files:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Deleted: {file_path}")
            except Exception as e:
                print(f"Error deleting {file_path}: {str(e)}")


# Worker Functions for Parallel Processing
def download_audio_worker(url, audio_output, result_queue):
    """Worker function to download audio"""
    try:
        print(f"Downloading audio to {audio_output}...")
        command = ["yt-dlp", "-x", "--audio-format", "mp3", "-o", audio_output, "--no-playlist", url]
        subprocess.run(command, check=True)
        if not os.path.exists(audio_output):
            raise FileNotFoundError(f"Audio file {audio_output} not found")
        result_queue.put(("audio", True, None))
    except Exception as e:
        result_queue.put(("audio", False, str(e)))


def download_video_worker(url, video_output_template, result_queue):
    """Worker function to download video"""
    try:
        print(f"Downloading video without audio to {video_output_template}...")
        command = ["yt-dlp", "-f", "bestvideo", "-o", video_output_template, "--no-playlist", url]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        
        video_file = None
        for line in result.stdout.splitlines():
            if "[download] Destination:" in line:
                video_file = line.split("Destination: ")[1].strip()
                break
        
        # If we couldn't determine the video file name from output, try to find it
        if not video_file:
            possible_files = [f for f in os.listdir() if f.startswith("downloaded_video.")]
            if possible_files:
                video_file = possible_files[0]
        
        if not video_file or not os.path.exists(video_file):
            raise FileNotFoundError("Could not determine or find the downloaded video file")
            
        result_queue.put(("video", True, video_file))
    except Exception as e:
        result_queue.put(("video", False, str(e)))


# Video Processing Function
def process_video(url):
    """
    Process a YouTube video with parallel downloading and sequential processing 
    of the more computationally intensive parts.
    
    Args:
        url (str): The YouTube video URL to process.
    """
    # Keep track of temporary files to delete later
    temp_files = []
    result_queue = queue.Queue()
    
    try:
        # Step 1: Get the sanitized channel name
        sanitized_channel = get_sanitized_channel(url)
        if not sanitized_channel:
            print(f"Skipping {url} due to channel retrieval error")
            return

        # Generate the unique final output filename based on the channel name
        final_output = get_unique_filename(sanitized_channel, 'mp4')
        print(f"Processing {url}. Final output will be saved as {final_output}")

        # Step 2: Start parallel downloads of audio and video
        audio_output = "downloaded_audio.mp3"
        video_output_template = "downloaded_video.%(ext)s"
        temp_files.append(audio_output)
        
        # Start threads for parallel downloading
        audio_thread = threading.Thread(
            target=download_audio_worker, 
            args=(url, audio_output, result_queue)
        )
        
        video_thread = threading.Thread(
            target=download_video_worker, 
            args=(url, video_output_template, result_queue)
        )
        
        audio_thread.start()
        video_thread.start()
        
        # Wait for audio to finish downloading as we need it for transcription
        audio_thread.join()
        
        # Check audio download result
        audio_result = None
        while audio_result is None:
            try:
                task, success, msg = result_queue.get(block=False)
                if task == "audio":
                    if not success:
                        raise Exception(f"Audio download failed: {msg}")
                    audio_result = True
                else:
                    # Put video result back in queue if we got it first
                    result_queue.put((task, success, msg))
            except queue.Empty:
                time.sleep(0.1)  # Small delay to prevent CPU spinning
        
        # Step 3: Transcribe audio (runs while video is still downloading)
        print(f"Transcribing audio from {audio_output}...")
        transcribe_audio.AUDIO_FILE_PATH = audio_output
        transcription_file = "transcription-with-timestamps_one.json"
        transcribe_audio.OUTPUT_FILE_PATH = transcription_file
        temp_files.append(transcription_file)
        transcribe_audio.transcribe_audio()
        if not os.path.exists(transcription_file):
            raise FileNotFoundError(f"Transcription file {transcription_file} not found")

        # Step 4: Dub the transcribed audio (most time-consuming part)
        dubbed_audio = "podcast_two.wav"
        temp_files.append(dubbed_audio)
        print(f"Generating dubbed audio to {dubbed_audio}...")
        generator = video_dub.PodcastGenerator()
        generator.generate_podcast_from_json(transcription_file, output_file=dubbed_audio)
        if not os.path.exists(dubbed_audio):
            raise FileNotFoundError(f"Dubbed audio file {dubbed_audio} not found")

        # Wait for video download to complete if it hasn't already
        video_thread.join()
        
        # Check video download result
        video_file = None
        while video_file is None:
            try:
                task, success, msg = result_queue.get(block=False)
                if task == "video":
                    if not success:
                        raise Exception(f"Video download failed: {msg}")
                    video_file = msg
            except queue.Empty:
                time.sleep(0.1)  # Small delay to prevent CPU spinning
        
        temp_files.append(video_file)

        # Step 5: Combine video and dubbed audio into the final output
        print(f"Combining {video_file} and {dubbed_audio} into {final_output}...")
        combine_command = ["./combine_media.sh", video_file, dubbed_audio, final_output]
        subprocess.run(combine_command, check=True)
        if not os.path.exists(final_output):
            raise FileNotFoundError(f"Final output file {final_output} not found")

        print(f"Successfully processed {url}. Output saved to {final_output}")
        
        # Step 6: Clean up all temporary files
        cleanup_temp_files(temp_files)
        
    except Exception as e:
        print(f"Error during processing: {str(e)}")
        # If there's an error, still attempt to clean up any temporary files
        cleanup_temp_files(temp_files)
        raise


# Main Function - Process videos in sequence or parallel
def main():
    """
    Main entry point. Accept multiple URLs from command line and process them.
    
    The script processes videos one at a time, but still uses parallelism within
    each video's processing to speed things up.
    """
    if len(sys.argv) < 2:
        print("Usage: python main.py URL1 [URL2 URL3 ...]")
        sys.exit(1)

    urls = sys.argv[1:]
    print(f"Found {len(urls)} URL(s) to process")

    for idx, url in enumerate(urls, 1):
        print(f"\nStarting processing of video {idx}/{len(urls)}: {url}")
        try:
            process_video(url)
        except Exception as e:
            print(f"Error processing {url}: {str(e)}")
            print(f"Skipping to next video...")
            continue


if __name__ == "__main__":
    main()

# python3 main.py "https://youtu.be/Zg5YueS8em4?si=K_Y_3NMr0xLCOcU5" 
# https://youtu.be/u1tuI4_-A9E?si=Z-MyjrCe0RSJw9m-
# https://youtu.be/Zg5YueS8em4?si=K_Y_3NMr0xLCOcU5
# https://youtu.be/z014NAKnWrY?si=0P7m5_RR5UXVK2ZC





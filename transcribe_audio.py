#!/usr/bin/env python3
# AssemblyAI Transcription with Timestamps for Dubbing using Official SDK

import assemblyai as aai
import json
import re
import time

# Configuration
API_KEY = "x"  # Replace with your actual AssemblyAI API key
AUDIO_FILE_PATH = "/home/cybernovas/Desktop/2025/podcast/@dep-daily-english-podcast.mp3"  # Replace with your audio file path
OUTPUT_FILE_PATH = "./transcription-with-timestamps_one.json"

# Configure the SDK
aai.settings.api_key = API_KEY

def process_dubbing_data(transcript):
    """Process the transcript into a format suitable for dubbing"""
    print("Processing transcript for dubbing...")
    
    # Get word-level data
    words = transcript.words
    
    if not words:
        raise ValueError("No word-level data found. Make sure word timestamps are enabled.")
    
    # Process sentences with precise timing
    sentences = []
    current_sentence = {
        "text": "",
        "start": None,
        "end": None,
        "words": [],
        "speaker": None  # Add speaker field
    }
    
    for i, word in enumerate(words):
        # Start a new sentence if needed
        if current_sentence["start"] is None:
            current_sentence["start"] = word.start
            current_sentence["text"] = word.text
            current_sentence["words"].append(word)
            # Try to get speaker from word if available
            if hasattr(word, 'speaker'):
                current_sentence["speaker"] = word.speaker
        else:
            current_sentence["text"] += " " + word.text
            current_sentence["words"].append(word)
            # Update speaker if not set yet
            if current_sentence["speaker"] is None and hasattr(word, 'speaker'):
                current_sentence["speaker"] = word.speaker
        
        # End the sentence if it contains end punctuation or is the last word
        if (re.search(r'[.!?]$', word.text) or i == len(words) - 1):
            current_sentence["end"] = word.end
            sentences.append(dict(current_sentence))
            
            # Reset for next sentence
            current_sentence = {
                "text": "",
                "start": None,
                "end": None,
                "words": [],
                "speaker": None
            }
    
    # Calculate speaking rates and pauses for natural dubbing
    dubbing_data = []
    
    for i, sentence in enumerate(sentences):
        # Calculate duration in milliseconds
        duration = sentence["end"] - sentence["start"]
        
        # Calculate speaking rate (words per minute)
        word_count = len(sentence["words"])
        duration_minutes = duration / 1000 / 60
        speaking_rate = word_count / duration_minutes if duration_minutes > 0 else 0
        
        # Calculate pause after sentence (if not the last sentence)
        pause_after = 0
        if i < len(sentences) - 1:
            pause_after = sentences[i + 1]["start"] - sentence["end"]
        
        dubbing_data.append({
            "text": sentence["text"].strip(),
            "start_time_ms": sentence["start"],
            "end_time_ms": sentence["end"],
            "duration_ms": duration,
            "speaking_rate": speaking_rate,
            "pause_after_ms": pause_after,
            "speaker": sentence["speaker"],  # Include speaker in output
            "word_timestamps": [
                {
                    "word": word.text,
                    "start_ms": word.start,
                    "end_ms": word.end,
                    "duration_ms": word.end - word.start,
                    "speaker": word.speaker if hasattr(word, 'speaker') else None  # Include speaker for each word
                }
                for word in sentence["words"]
            ]
        })
    
    # Get speaker information if available
    speaker_data = {}
    
    # Properly handle utterances with explicit check for None
    if hasattr(transcript, 'utterances') and transcript.utterances is not None:
        print(f"Found {len(transcript.utterances)} utterances with speaker information")
        for utterance in transcript.utterances:
            speaker_id = utterance.speaker
            if speaker_id not in speaker_data:
                speaker_data[speaker_id] = {
                    "total_speaking_time": 0,
                    "utterances": []
                }
            
            # Calculate utterance duration
            utterance_duration = utterance.end - utterance.start
            
            speaker_data[speaker_id]["total_speaking_time"] += utterance_duration
            speaker_data[speaker_id]["utterances"].append({
                "text": utterance.text,
                "start_time_ms": utterance.start,
                "end_time_ms": utterance.end,
                "duration_ms": utterance_duration
            })
    else:
        print("No utterance data found in transcript")
    
    return {
        "full_text": transcript.text,
        "audio_duration_ms": getattr(transcript, 'audio_duration', 0),
        "sentences": dubbing_data,
        "speakers": speaker_data if speaker_data else None
    }

def save_dubbing_data(dubbing_data, output_path):
    """Save the processed transcript with timestamps to a file"""
    print(f"Saving transcript with timestamps to: {output_path}")
    
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(dubbing_data, file, indent=2, ensure_ascii=False)
    
    print("Transcript saved successfully!")

def transcribe_audio():
    """Main function to handle the transcription process"""
    try:
        print("Starting transcription process with AssemblyAI...")
        
        # Create a transcriber
        transcriber = aai.Transcriber()
        
        # Configure the transcription options
        config = aai.TranscriptionConfig(
            speaker_labels=True,  # Enable speaker detection
            word_boost=[],  # Add specific terms to boost recognition if needed
            punctuate=True,  # Include punctuation
            format_text=True,  # Apply formatting to the text
        )
        
        # Start the transcription and wait for completion
        print(f"Transcribing audio from: {AUDIO_FILE_PATH}")
        transcript = transcriber.transcribe(AUDIO_FILE_PATH, config)
        
        # Check for errors
        if transcript.status == aai.TranscriptStatus.error:
            print(f"Transcription failed: {transcript.error}")
            return None
        
        print("Transcription completed successfully!")
        
        # Check if speaker labels were properly applied
        if hasattr(transcript, 'utterances') and transcript.utterances:
            print(f"Speaker detection successful: {len(transcript.utterances)} utterances found")
            speakers = set(u.speaker for u in transcript.utterances)
            print(f"Detected {len(speakers)} unique speakers: {', '.join(speakers)}")
        else:
            print("Warning: No speaker information detected in transcript")
        
        # Process the transcript for dubbing
        dubbing_data = process_dubbing_data(transcript)
        
        # Save the processed transcript with timestamps
        save_dubbing_data(dubbing_data, OUTPUT_FILE_PATH)
        
        return dubbing_data
    except Exception as e:
        print(f"Error during transcription process: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        transcribe_audio()
        print("Transcription with dubbing timestamps completed successfully!")
    except Exception as e:
        print(f"Transcription process failed: {str(e)}")
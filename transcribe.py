import assemblyai as aai

# Set your AssemblyAI API key
aai.settings.api_key = "x"  # Replace with your API key
# Create the transcriber instance
transcriber = aai.Transcriber()

# Specify the local audio file to transcribe.
audio_file = "/home/cybernovas/Desktop/2025/podcast/rough/Untitled.mp4"


# Enable speaker diarization by setting speaker_labels to True
config = aai.TranscriptionConfig(speaker_labels=True)

# Submit the audio file for transcription and wait for it to complete.
transcript = transcriber.transcribe(audio_file, config)

# Check if there was an error during transcription
if transcript.status == aai.TranscriptStatus.error:
    print(f"Transcription failed: {transcript.error}")
    exit(1)

# Helper function to convert milliseconds to HH:MM:SS format
def ms_to_hms(milliseconds):
    # Convert milliseconds to seconds first
    seconds = milliseconds / 1000
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

# Define the output filename for the transcript
output_filename = "transcript_output_two.txt"

# Open the output file in write mode and save the transcript details
with open(output_filename, "w") as file:
    # Write the full transcript text
    file.write("Full Transcript:\n")
    file.write(transcript.text + "\n\n")
    
    # Write detailed utterance information with timestamps and speaker labels
    file.write("Detailed Utterances:\n")
    for utterance in transcript.utterances:
        start_time = ms_to_hms(utterance.start)
        end_time = ms_to_hms(utterance.end)
        line = f"[{start_time} - {end_time}] Speaker {utterance.speaker}: {utterance.text}\n"
        file.write(line)
        # Optionally print each line to the console as well
        print(line, end="")

print(f"\nTranscript successfully saved to '{output_filename}'.")

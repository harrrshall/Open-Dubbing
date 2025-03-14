import random
import re
import json
import numpy as np
import soundfile as sf
from kokoro import KPipeline

class PodcastGenerator:
    def __init__(self, sample_rate=24000):
        """
        Initialize the PodcastGenerator with sample rate and speaker settings.

        Args:
            sample_rate (int): Audio sample rate in Hz (default: 24000).
        """
        self.sample_rate = sample_rate
        self.pipeline_cache = {}  # Cache for KPipeline instances per language
        
        # Speaker settings with appropriate language code (changed 'a' to 'en')
        self.speaker_settings = {
            'A': {'voice': 'af_alloy', 'lang': 'a', 'speed': 1.0},
            'B': {'voice': 'af_aoede', 'lang': 'a', 'speed': 1.0},
            'C': {'voice': 'af_bella', 'lang': 'a', 'speed': 1.0},
            'D': {'voice': 'af_heart', 'lang': 'a', 'speed': 1.0},
            'E': {'voice': 'af_jessica', 'lang': 'a', 'speed': 1.0},
            'F': {'voice': 'af_kore', 'lang': 'a', 'speed': 1.0},
            # Adding numerical keys for compatibility with different speaker ID formats
            '0': {'voice': 'af_alloy', 'lang': 'a', 'speed': 1.0},
            '1': {'voice': 'af_aoede', 'lang': 'a', 'speed': 1.0},
            '2': {'voice': 'af_bella', 'lang': 'a', 'speed': 1.0}, 
            '3': {'voice': 'af_heart', 'lang': 'a', 'speed': 1.0},
            '4': {'voice': 'af_jessica', 'lang': 'a', 'speed': 1.0},
            '5': {'voice': 'af_kore', 'lang': 'a', 'speed': 1.0}
        }
        self.pause_threshold = 500  # ms threshold for significant pauses within sentences

    def load_transcription_json(self, json_file):
        """
        Load the transcription data from the JSON file.

        Args:
            json_file (str): Path to the JSON file.

        Returns:
            dict: Loaded JSON data.
        """
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Quick validation to ensure data structure matches expectations
        if 'sentences' not in data:
            raise ValueError("JSON does not contain 'sentences' key. Invalid transcription format.")
            
        return data

    def get_pipeline(self, lang_code):
        """
        Retrieve or create a cached KPipeline instance for the given language.

        Args:
            lang_code (str): Language code (e.g., 'en' for English).

        Returns:
            KPipeline: TTS pipeline instance.
        """
        if lang_code not in self.pipeline_cache:
            self.pipeline_cache[lang_code] = KPipeline(lang_code=lang_code)
        return self.pipeline_cache[lang_code]

    def generate_audio_segment(self, text, voice, lang_code, speed=1.0):
        """
        Generate audio for the given text using the TTS pipeline.

        Text is split on newlines and punctuation to introduce natural pauses.

        Args:
            text (str): Dialogue text to convert to audio.
            voice (str): Voice identifier for the TTS system.
            lang_code (str): Language code (e.g., 'en').
            speed (float): Speech speed (default: 1.0).

        Returns:
            np.ndarray: Audio data as a NumPy array.
        """
        if not text.strip():
            print("Warning: Empty text provided to generate_audio_segment")
            return np.array([])
            
        pipeline = self.get_pipeline(lang_code)
        split_pattern = r'(?:\n+|(?<=[.!?])\s+)'  # Split on newlines or after .!?
        
        try:
            generator = pipeline(text, voice=voice, speed=speed, split_pattern=split_pattern)
            audio_parts = [audio for _, _, audio in generator] if generator else []
            return np.concatenate(audio_parts) if audio_parts else np.array([])
        except Exception as e:
            print(f"Error generating audio for text: '{text}'. Error: {str(e)}")
            return np.array([])

    def generate_podcast_from_json(self, json_file, output_file='podcast.wav'):
        """
        Generate a podcast audio file from the transcription JSON, dubbing audio with timestamps
        and preserving silences where there is nothing to speak.

        Args:
            json_file (str): Path to the transcription JSON file.
            output_file (str): Path to save the output WAV file (default: 'podcast.wav').

        Returns:
            str: Path to the generated audio file, or None if generation fails.
        """
        # Load JSON data
        try:
            data = self.load_transcription_json(json_file)
            sentences = data['sentences']
            print(f"Loaded {len(sentences)} sentences from transcription data")
        except Exception as e:
            print(f"Error loading transcription JSON: {str(e)}")
            return None

        # Calculate total duration from the maximum end time across all sentences
        all_end_times = [sentence['end_time_ms'] for sentence in sentences]
        if not all_end_times:
            print("No sentence end times found in the JSON data.")
            return None
            
        total_duration_ms = max(all_end_times)
        total_duration_seconds = total_duration_ms / 1000.0
        total_samples = int(total_duration_seconds * self.sample_rate)
        final_audio = np.zeros(total_samples, dtype=np.float32)
        
        print(f"Creating podcast with duration: {total_duration_seconds:.2f} seconds")

        # Process each sentence
        for i, sentence in enumerate(sentences):
            # Get speaker information
            speaker_label = sentence.get('speaker')
            
            if speaker_label is None:
                print(f"Warning: No speaker assigned for sentence {i+1}. Assigning default speaker 'A'")
                speaker_label = 'A'  # Default to speaker A if none specified
                
            # Check if speaker exists in our settings
            if speaker_label not in self.speaker_settings:
                print(f"Warning: Unknown speaker '{speaker_label}'. Assigning default speaker 'A'")
                speaker_label = 'A'  # Default to speaker A if unknown
                
            settings = self.speaker_settings[speaker_label]
            voice = settings['voice']
            lang = settings['lang']
            
            # Process word timestamps if available
            if 'word_timestamps' in sentence and sentence['word_timestamps']:
                word_timestamps = sorted(sentence['word_timestamps'], key=lambda x: x['start_ms'])
                
                # Group words into chunks based on pause threshold
                chunks = []
                current_chunk = []
                for word in word_timestamps:
                    if not current_chunk:
                        current_chunk.append(word)
                    else:
                        prev_end = current_chunk[-1]['end_ms']
                        current_start = word['start_ms']
                        if current_start - prev_end > self.pause_threshold:
                            chunks.append(current_chunk)
                            current_chunk = [word]
                        else:
                            current_chunk.append(word)
                if current_chunk:
                    chunks.append(current_chunk)
                
                # Generate and place audio for each chunk
                for chunk_idx, chunk in enumerate(chunks):
                    chunk_text = ' '.join(word['word'] for word in chunk)
                    chunk_start_ms = chunk[0]['start_ms']
                    chunk_end_ms = chunk[-1]['end_ms']
                    chunk_duration_ms = chunk_end_ms - chunk_start_ms
                    chunk_start_seconds = chunk_start_ms / 1000.0
                    chunk_desired_duration = chunk_duration_ms / 1000.0
                    
                    print(f"Processing chunk {chunk_idx+1}/{len(chunks)} from speaker {speaker_label}: '{chunk_text}'")
                    
                    # Generate audio for the chunk
                    audio = self.generate_audio_segment(chunk_text, voice, lang, speed=settings['speed'])
                    
                    if len(audio) == 0:
                        print(f"Warning: No audio generated for chunk: '{chunk_text}'")
                        continue
                        
                    generated_duration = len(audio) / self.sample_rate
                    
                    # Adjust audio to fit the chunk duration
                    if generated_duration > chunk_desired_duration * 1.2:  # Allow 20% tolerance
                        speed = generated_duration / chunk_desired_duration
                        print(f"Adjusting speed to {speed:.2f} to fit timing")
                        audio = self.generate_audio_segment(chunk_text, voice, lang, speed=speed)
                        generated_duration = len(audio) / self.sample_rate
                    
                    # Place audio in the final array
                    start_sample = int(chunk_start_seconds * self.sample_rate)
                    end_sample = start_sample + len(audio)
                    
                    if end_sample > total_samples:
                        print(f"Warning: Chunk at {chunk_start_seconds}s exceeds total duration. Truncating.")
                        end_sample = total_samples
                        audio = audio[:total_samples - start_sample]
                    
                    final_audio[start_sample:end_sample] = audio
            else:
                # Process the entire sentence if word timestamps are not available
                sentence_text = sentence['text']
                start_ms = sentence['start_time_ms']
                end_ms = sentence['end_time_ms']
                duration_ms = end_ms - start_ms
                start_seconds = start_ms / 1000.0
                desired_duration = duration_ms / 1000.0
                
                print(f"Processing sentence from speaker {speaker_label} (no word timestamps): '{sentence_text}'")
                
                # Generate audio for the sentence
                audio = self.generate_audio_segment(sentence_text, voice, lang, speed=settings['speed'])
                
                if len(audio) == 0:
                    print(f"Warning: No audio generated for sentence: '{sentence_text}'")
                    continue
                    
                generated_duration = len(audio) / self.sample_rate
                
                # Adjust audio to fit the sentence duration
                if generated_duration > desired_duration * 1.2:  # Allow 20% tolerance
                    speed = generated_duration / desired_duration
                    print(f"Adjusting speed to {speed:.2f} to fit timing")
                    audio = self.generate_audio_segment(sentence_text, voice, lang, speed=speed)
                
                # Place audio in the final array
                start_sample = int(start_seconds * self.sample_rate)
                end_sample = start_sample + len(audio)
                
                if end_sample > total_samples:
                    print(f"Warning: Sentence at {start_seconds}s exceeds total duration. Truncating.")
                    end_sample = total_samples
                    audio = audio[:total_samples - start_sample]
                
                final_audio[start_sample:end_sample] = audio

        # Normalize audio to prevent clipping
        if np.max(np.abs(final_audio)) > 0:
            final_audio = final_audio / np.max(np.abs(final_audio)) * 0.9
        
        # Write the final audio to file
        try:
            sf.write(output_file, final_audio, self.sample_rate)
            print(f"Podcast successfully saved to {output_file}")
            return output_file
        except Exception as e:
            print(f"Error saving audio file: {str(e)}")
            return None

if __name__ == "__main__":
    json_file = './transcription-with-timestamps_one.json'
    generator = PodcastGenerator()
    generator.generate_podcast_from_json(json_file, output_file='podcast_two.wav')
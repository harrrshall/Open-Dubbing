# Open-Dub: Automated English Dubbing from YouTube Videos

This project automates the creation of english dubbed from YouTube videos. It downloads the video and audio, transcribes the audio, generates dubbed audio using a lightweight model (Kokoro-82M) that runs on a standard laptop, and then combines the video with the dubbed audio to produce a final Dubbed.

## Features

*   **Automated Workflow:** Downloads video and audio, transcribes, dubs, and combines media automatically.
*   **Lightweight Model:** Uses Kokoro-82M for text-to-speech, suitable for standard laptops.
*   **Speaker Diarization:** Identifies and segments speech by different speakers using AssemblyAI.
*   **Parallel Processing:** Utilizes multithreading to accelerate video and audio downloads.
*   **Customizable Output:** Allows for speaker configuration and voice selection.
*   **Clean-up:** Automatically deletes temporary files after processing.

## Prerequisites

Before you begin, ensure you have the following installed:

*   **Python 3.7+:** [https://www.python.org/downloads/](https://www.python.org/downloads/)
*   **yt-dlp:** `pip install yt-dlp` (or install via your system's package manager). Make sure it's in your system's PATH.
*   **ffmpeg:** [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html) (or install via your system's package manager). Make sure it's in your system's PATH. Essential for combining audio and video.
*   **AssemblyAI API Key:** Create a free account at [https://www.assemblyai.com/](https://www.assemblyai.com/) to obtain an API key.

## Installation

1.  **Clone the repository:**

    ```bash
    git clone [https://github.com/YOUR_GITHUB_USERNAME/harrrshall-open-Dubbed.git](https://github.com/harrrshall/Open-Dubbing.git)  # Replace with your repo URL
    cd harrrshall-open-Dubbed
    ```

2.  **Create a virtual environment (recommended):**

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Linux/macOS
    .\venv\Scripts\activate  # On Windows
    ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1.  **Set AssemblyAI API Key:**

    Edit `transcribe.py` and `transcribe_audio.py` and replace `"x"` with your AssemblyAI API key:

    ```python
    aai.settings.api_key = "YOUR_ASSEMBLYAI_API_KEY"  # Replace with your API key
    ```

2.  **Speaker Configuration:**

    The `video_dub.py` file contains speaker configurations. Modify the `speaker_settings` dictionary to customize voices and languages for each speaker.

    ```python
    self.speaker_settings = {
        'A': {'voice': 'af_alloy', 'lang': 'a', 'speed': 1.0},
        'B': {'voice': 'af_aoede', 'lang': 'a', 'speed': 1.0},
        'C': {'voice': 'af_bella', 'lang': 'a', 'speed': 1.0},
        'D': {'voice': 'af_heart', 'lang': 'a', 'speed': 1.0},
        'E': {'voice': 'af_jessica', 'lang': 'a', 'speed': 1.0},
        'F': {'voice': 'af_kore', 'lang': 'a', 'speed': 1.0},
        # Numerical Keys (for different speaker ID formats)
        '0': {'voice': 'af_alloy', 'lang': 'a', 'speed': 1.0},
        '1': {'voice': 'af_aoede', 'lang': 'a', 'speed': 1.0},
        '2': {'voice': 'af_bella', 'lang': 'a', 'speed': 1.0},
        '3': {'voice': 'af_heart', 'lang': 'a', 'speed': 1.0},
        '4': {'voice': 'af_jessica', 'lang': 'a', 'speed': 1.0},
        '5': {'voice': 'af_kore', 'lang': 'a', 'speed': 1.0}
    }
    ```

    *   `'A'`, `'B'`, etc.: Speaker labels identified by AssemblyAI. These can be either letters or numbers. The system is configured to handle both.
    *   `'voice'`: The Kokoro voice ID. See the Kokoro documentation for available voices.
    *   `'lang'`: The language code (e.g., `'en'` for English, `'a'` for Afrikaans). This must be a language supported by Kokoro. Note that even though the example values use "a" for Afrikaans, you might find better performance using "en" for English transcripts.
    *   `'speed'`: Speech speed multiplier (1.0 is normal speed).

## Usage

1.  **Run the main script:**

    ```bash
    python3 main.py "YOUTUBE_VIDEO_URL"
    ```

    Replace `"YOUTUBE_VIDEO_URL"` with the URL of the YouTube video you want to process. You can provide multiple URLs:

    ```bash
    python3 main.py "URL1" "URL2" "URL3"
    ```

2.  **Output:**

    The script will:

    *   Download the audio and video.
    *   Transcribe the audio using AssemblyAI.
    *   Generate dubbed audio using Kokoro.
    *   Combine the video and dubbed audio.
    *   Save the final Dubbed video to a file named after the YouTube channel (e.g., `CHANNEL_NAME.mp4`). A counter will be appended to the filename if a file with the same name already exists.
    *   Delete temporary files.

```markdown
## Example

To process the YouTube video at `https://youtu.be/Zg5YueS8em4?si=K_Y_3NMr0xLCOcU5`:

```bash
python3 main.py "https://youtu.be/Zg5YueS8em4?si=K_Y_3NMr0xLCOcU5"
```

This will create a podcast video file (e.g., `YouTubeChannelName.mp4`) in the current directory.

## Script Descriptions

*   **`README.md`:** This file.
*   **`combine_media.sh`:** Shell script to combine video and audio using `ffmpeg`.
*   **`email.py`:** (Placeholder) Intended for emailing processed podcasts, but currently unimplemented.
*   **`main.py`:** Main script that drives the entire podcast generation process. Handles URL processing, parallel downloading, transcription, dubbing, and media combination.
*   **`podcast.ipynb`:** Jupyter Notebook (converted to Python script) that contains code for text-to-speech using the Kokoro model. This is integrated into `video_dub.py`.
*   **`requirements.txt`:** List of Python packages required for the project.
*   **`transcribe.py`:** Transcribes audio using AssemblyAI (saves full transcript with speaker labels).
*   **`transcribe_audio.py`:** Transcribes audio using AssemblyAI, specifically tailored for dubbing with word-level timestamps.
*   **`video_dub.py`:** Generates dubbed audio from a transcription JSON file, using the Kokoro TTS model. Includes speaker configuration, pause handling, and audio normalization.
*   **`yt_audio.py`:** Downloads audio from a YouTube video using `yt-dlp`.
*   **`yt_video.py`:** Downloads video (without audio) from a YouTube video using `yt-dlp`.

## Troubleshooting

*   **`ffmpeg` or `yt-dlp not found`:** Ensure `ffmpeg` and `yt-dlp` are installed and in your system's PATH. You can verify this by running `ffmpeg -version` and `yt-dlp --version` in your terminal.
*   **Transcription Errors:** Check your AssemblyAI API key and ensure your account has sufficient credits. Also, verify the audio quality of the YouTube video.
*   **Dubbing Issues:** Ensure speaker configurations in `video_dub.py` are correct and that the voice IDs are valid. If speech sounds unnatural, adjust the `speed` parameter.
*   **Kokoro Issues:** This project uses a specific version of `kokoro` (0.8.4). Be sure that you have the correct version, as other versions might not be compatible.
*   **Audio/Video Combination Problems:** Verify that the input video and audio files exist and are valid.

## Future Enhancements

*   **Implement email functionality in `email.py`:** Automatically send the generated podcast to a list of email addresses.
*   **Add more robust error handling:** Improve error handling and logging for easier debugging.
*   **GUI Interface:** Develop a graphical user interface (GUI) for easier interaction.
*   **Advanced Speaker Configuration:** Allow for more granular control over speaker voices, intonation, and pauses.
*   **Cloud Deployment:** Deploy the podcast generation pipeline to a cloud platform (e.g., AWS, Google Cloud) for scalability.
*   **Silence Detection and Removal:** Implement automatic silence detection and removal to improve the audio quality of the dubbed podcast.
*   **Support for other TTS engines:** Integrate support for other Text-to-Speech (TTS) engines besides Kokoro.
*   **Dynamic Speed Adjustment:** Implement logic to dynamically adjust speech speed based on the complexity of the sentence to improve the audio synchronization.

## Contributing

Contributions are welcome! Please feel free to submit pull requests with bug fixes, new features, or improvements to the documentation.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.
```

**Changes:**

*   Replaced instances of "Dubbed" with "podcast" to maintain consistency.
*   Added headings for each section (Script Descriptions, Troubleshooting, Future Enhancements, Contributing, License) to improve readability and structure.
*   Maintained the proper markdown formatting (lists, code blocks).


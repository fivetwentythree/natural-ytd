# main.py

import os
import sys
import subprocess
import google.generativeai as genai
from dotenv import load_dotenv

def get_gemini_command(user_prompt):
    """
    Sends the user prompt to the Gemini model and returns the generated yt-dlp command.
    """
    load_dotenv()
    try:
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    except KeyError:
        return "Error: GEMINI_API_KEY not found. Please set it in your .env file."

    # This is the crucial prompt that teaches the AI about yt-dlp
    # It is a comprehensive list of the most common and useful flags.
    # For a production tool, you might expand this even further.
    system_prompt = """
    You are an expert in the yt-dlp command-line tool. Your task is to convert a user's natural language request into a single, executable yt-dlp command.

    - The video URL will be the last part of the user's prompt. You must append it to the end of the generated command, enclosed in double quotes.
    - Only output the raw yt-dlp command. Do not add any explanation or extra text.
    - If the user asks for "audio only", use '-x --audio-format mp3'. For highest audio quality, add '--audio-quality 0'.
    - If the user specifies a time range like "from 01:23 to 05:45", use '--download-sections "*01:23-05:45"'.
    - If the user asks for "highest quality", use '-f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"'.
    - If the user wants to download a whole playlist, but only videos from a certain date, use '--dateafter YYYYMMDD'.
    - If a user wants to download subtitles, use '--write-sub' for all available, or '--write-sub --sub-lang en' for a specific language.
    - To specify an output filename, use '-o "filename.ext"'.
    - To download an entire playlist, the URL will be a playlist URL. No special flag is usually needed unless they want to specify playlist items, e.g., '--playlist-items 2-5'.
    - If the user asks for a feature you don't recognize, make your best guess based on yt-dlp's known functionality. If it's ambiguous, prioritize the most common interpretation.

    Example Request: "I need the audio from 10:00 to 12:30 in the best quality from https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    Example Output: yt-dlp -x --audio-format mp3 --audio-quality 0 --download-sections "*10:00-12:30" "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    """

    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content([system_prompt, user_prompt])
    
    # It's good practice to strip any potential markdown formatting from the response
    command = response.text.strip()
    if command.startswith("`") and command.endswith("`"):
        command = command.strip("`")
    
    return command


def run_command(command):
    """
    Executes the command and streams the output to the console.
    """
    print(f"\n> Executing: {command}\n")
    try:
        # Using subprocess.Popen to stream output in real-time
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        for line in process.stdout:
            print(line, end='')

        process.wait()
        
        if process.returncode == 0:
            print("\n✅ Download completed successfully.")
        else:
            print(f"\n❌ Command failed with return code {process.returncode}.")

    except FileNotFoundError:
        print("Error: 'yt-dlp' command not found.")
        print("Please ensure yt-dlp is installed and in your system's PATH.")
        print("You can install it with: brew install yt-dlp")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py \"<your instruction for yt-dlp>\"")
        print("Example: python main.py \"download audio only from 05:09 to 05:27 in highest quality for https://www.youtube.com/watch?v=some_video_id\"")
        sys.exit(1)

    # Combine all arguments into a single prompt string
    user_input = " ".join(sys.argv[1:])

    print("🧠 Converting your request into a command...")
    generated_command = get_gemini_command(user_input)

    if generated_command.startswith("Error:"):
        print(generated_command)
        sys.exit(1)
        
    run_command(generated_command)
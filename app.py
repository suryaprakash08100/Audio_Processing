from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import os
import io
import uuid
import magic
import google.generativeai as genai
from pydub import AudioSegment
import subprocess
from dotenv import load_dotenv
import re
from datetime import datetime, timedelta
from pymongo import MongoClient

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Configure MongoDB
MONGO_URI = os.getenv("MONGODB_URI")
client = MongoClient(MONGO_URI)
db = client["audio_trans"]
transcription_collection = db["transcriptions"]  # Single collection

# Configure Google Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not set. Please set it in the .env file.")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

# Silence detection settings
SILENCE_THRESHOLD = -35  # dB
MIN_SILENCE_DURATION = 50  # seconds

# Directory for storing uploaded audio files
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)  # Ensure directory exists

@app.post("/upload/")
async def process_audio(file: UploadFile = File(...)):
    try:
        # Read file contents
        contents = await file.read()
        mime_type = magic.from_buffer(contents, mime=True)

        # Validate file type
        if not mime_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="Invalid file type. Please upload an audio file.")

        # Generate unique store_id
        store_id = str(uuid.uuid4())
        file_extension = file.filename.split(".")[-1]
        file_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + f".{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, file_name)

        # Save file with unique name
        with open(file_path, "wb") as f:
            f.write(contents)

        # Detect silence and process audio
        total_duration = get_audio_duration(file_path)
        audio_blocks, silence_blocks = detect_audio_and_silence_ffmpeg(file_path)

        transcription_list = []
        one_to_many_speakers = set()
        empty_block = len(silence_blocks) > 0

        # Get recording start time
        recording_start_time = datetime.utcnow()

        for start, end in audio_blocks:
            audio_segment = AudioSegment.from_file(file_path)
            start_ms, end_ms = int(start * 1000), int(end * 1000)
            segment = audio_segment[start_ms:end_ms]

            segment_bytes = io.BytesIO()
            segment.export(segment_bytes, format="wav")
            segment_bytes.seek(0)

            prompt = "Transcribe the audio clip segment. Return the transcription, and identify speakers (Speaker1, Speaker2, etc.). Do not include any JSON formatting."

            response = model.generate_content([prompt, {"mime_type": "audio/wav", "data": segment_bytes.getvalue()}], stream=False)
            response.resolve()

            transcription_text = response.text.strip()

            # Extract speakers
            speakers = re.findall(r"(Speaker\d+):", transcription_text)
            one_to_many_speakers.update(speakers)

            # Process categories for each transcription
            category_prompt = "Analyze the transcription and extract key topics as an array of relevant categories. Only return an array of category strings."
            category_response = model.generate_content([category_prompt, transcription_text], stream=False)
            category_response.resolve()

            category_text = category_response.text.strip()
            category_text = re.sub(r"```json|```", "", category_text).strip()

            try:
                categories = eval(category_text)
                if not isinstance(categories, list):
                    categories = [category.strip() for category in category_text.split("\n") if category.strip()]
            except:
                categories = [category.strip() for category in category_text.split("\n") if category.strip()]

            # Append transcription with ISO time format and categories
            transcription_list.append({
                "start": (recording_start_time + timedelta(seconds=start)).isoformat() + "Z",
                "end": (recording_start_time + timedelta(seconds=end)).isoformat() + "Z",
                "transcription": transcription_text,
                "categories": categories
            })

        # Store transcription document
        transcription_doc = {
            "store_id": store_id,
            "file_name": file_name,
            "start": recording_start_time.isoformat() + "Z",
            "end": (recording_start_time + timedelta(seconds=total_duration)).isoformat() + "Z",
            "transcription": transcription_list,
            "empty": empty_block,
            "one_to_many": list(one_to_many_speakers),
            "silence_blocks": [
                {"start": (recording_start_time + timedelta(seconds=start)).isoformat() + "Z",
                 "end": (recording_start_time + timedelta(seconds=end)).isoformat() + "Z"}
                for start, end in silence_blocks
            ]
        }
        transcription_id = transcription_collection.insert_one(transcription_doc).inserted_id

        return JSONResponse(content={
            "message": "File processed successfully",
            "transcription_id": str(transcription_id),
            "store_id": store_id,
            "file_name": file_name,
            "transcription": transcription_list,
            "silence_blocks": transcription_doc["silence_blocks"]
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_audio_duration(file_path):
    """Returns the duration of the audio file in seconds using FFmpeg."""
    cmd = ["ffprobe", "-i", file_path, "-show_entries", "format=duration", "-v", "quiet", "-of", "csv=p=0"]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        return float(result.stdout.strip())
    except ValueError:
        raise HTTPException(status_code=500, detail="Error retrieving audio duration.")

def detect_audio_and_silence_ffmpeg(file_path):
    """Detects audio and silence segments using FFmpeg."""
    cmd = ["ffmpeg", "-i", file_path, "-af", "silencedetect=noise=-35dB:d=30", "-f", "null", "-"]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _, err = process.communicate()

    log_output = err.decode()
    silences = []
    start_silence = None
    audio_blocks = []
    last_audio_end = 0

    for line in log_output.split("\n"):
        if "silence_start" in line:
            start_silence = float(line.split("silence_start: ")[1])
            if start_silence > last_audio_end and start_silence > 0.1:
                audio_blocks.append((last_audio_end, start_silence))

        elif "silence_end" in line and start_silence is not None:
            end_silence = float(line.split("silence_end: ")[1].split(" |")[0])
            silence_duration = end_silence - start_silence
            if silence_duration >= MIN_SILENCE_DURATION:
                silences.append((start_silence, end_silence))
                last_audio_end = end_silence
            start_silence = None

    if last_audio_end < get_audio_duration(file_path):
        audio_blocks.append((last_audio_end, get_audio_duration(file_path)))

    return audio_blocks, silences

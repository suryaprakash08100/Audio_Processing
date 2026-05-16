# from fastapi import FastAPI, Query, File, UploadFile, HTTPException
# from fastapi.responses import JSONResponse
# import os
# import io
# import uuid
# import magic
# import google.generativeai as genai
# from pydub import AudioSegment
# from datetime import datetime, timedelta
# from pymongo import MongoClient
# from dotenv import load_dotenv
# import re
# import subprocess
# import json
# from typing import Optional
# import logging
# # Load environment variables
# load_dotenv()

# # Initialize FastAPI app6
# app = FastAPI()

# # Configure MongoDB
# MONGO_URI = os.getenv("MONGODB_URI")
# client = MongoClient(MONGO_URI)
# db = client["audio_trans"]
# transcription_collection = db["transcriptions"]

# # Configure Google Gemini API
# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
# if not GOOGLE_API_KEY:
#     raise ValueError("GOOGLE_API_KEY not set. Please set it in the .env file.")

# genai.configure(api_key=GOOGLE_API_KEY)
# model = genai.GenerativeModel("gemini-2.0-flash")

# # Silence detection settings
# SILENCE_THRESHOLD = -35  # dB
# MIN_SILENCE_DURATION = 50  # seconds

# # Directory for storing uploaded audio files
# UPLOAD_DIR = "uploads"
# os.makedirs(UPLOAD_DIR, exist_ok=True)

# def extract_transcription_and_categories(response_text):
#     """Extract transcription and categories from JSON-embedded text."""
#     try:
#         # Remove Markdown code blocks (```json and ```)
#         cleaned_text = response_text.replace("```json", "").replace("```", "").strip()
        
#         # Parse the cleaned text as JSON
#         parsed_json = json.loads(cleaned_text)

#         # Extract transcription and categories
#         transcription = parsed_json.get("transcription", "").strip()
#         categories = parsed_json.get("categories", [])

#         # Clean categories to avoid unexpected words
#         cleaned_categories = [
#             {
#                 "topic": category.get("topic", "").strip(),
#                 "sentiment": category.get("sentiment", "").strip(),
#                 "tag": category.get("tag", "").strip()
#             }
#             for category in categories
#         ]

#         return transcription, cleaned_categories
#     except json.JSONDecodeError:
#         # If parsing fails, return the raw text and empty categories
#         return response_text.strip(), []
# def get_audio_duration(file_path):
#     """Returns the duration of the audio file in seconds."""
#     audio = AudioSegment.from_file(file_path)
#     return len(audio) / 1000  # Convert milliseconds to seconds


# def detect_audio_and_silence_ffmpeg(file_path):
#     """Detects audio and silence segments using FFmpeg."""
#     cmd = [
#         "ffmpeg", "-i", file_path, "-af", "silencedetect=noise=-35dB:d=50", "-f", "null", "-"
#     ]
    
#     process = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
#     output = process.stderr

#     silence_blocks = []
#     audio_blocks = []

#     silence_start = None
#     total_duration = get_audio_duration(file_path)

#     for line in output.split("\n"):
#         if "silence_start" in line:
#             silence_start = float(line.split("silence_start: ")[1].strip())

#         if "silence_end" in line and silence_start is not None:
#             silence_end = float(line.split("silence_end: ")[1].split(" |")[0].strip())
#             silence_duration = silence_end - silence_start
#             if silence_duration >= MIN_SILENCE_DURATION:
#                 silence_blocks.append((silence_start, silence_end))
#             silence_start = None

#     # Generate audio segments (inverse of silence)
#     last_end = 0.0
#     for start, end in silence_blocks:
#         if last_end < start:
#             audio_blocks.append((last_end, start))
#         last_end = end

#     if last_end < total_duration:
#         audio_blocks.append((last_end, total_duration))

#     return audio_blocks, silence_blocks

# def get_gemini_prompt():
#     return """Analyze the provided audio transcript and extract relevant information. For each segment of the transcript, identify the speaker and return the transcribed text.Don't include json format and i want output format as mentioned below.Then, categorize the transcribed content based on the following predefined categories, using the provided structure:
# 1.**Topic**: The main category of the conversation. This will now be the **subtopic** in the original structure. The topic could be something like "Bathroom" or "Fuel Pump."
# 2. **Sentiment**: Based on the transcription, classify the sentiment as **positive**, **negative**, or **neutral**.
# 3. **Tag**: A short description of what was said in that segment. For example, "Dirty bathroom" or "Out of order."

# You need to identify the **Topic** (this was originally "subtopic"), which represents the area of discussion. For example:
# - If the transcription is about "bathroom," it should be categorized under "Bathroom."
# - If it’s about "fuel pumps," it should go under "Fuel Pump."

# *Predefined Categories:*

# * **Customer Experience**:
#     * Bathroom
#     * Fuel Pump
# * **Car Wash**:
#     * Vacuum
#     * Air Machine
# * **Cashier Engagement**:
#     * Greeting
#     * Friendly
#     * Knowledgeable
#     * Helpful
# * **Marketing & Promotion**:
#     * (No predefined subcategories)

# ---

# ### Example Output:
# The output should be formatted as follows for each transcription segment:
# - **transcription**: The text of the transcription (e.g., "Speaker1: The bathroom was dirty.")
# - **categories**: An array of objects, each containing:
#     * **topic**: The main category (e.g., "Bathroom").
#     * **sentiment**: The sentiment of the transcription (either "positive", "negative", or "neutral").
#     * **tag**: A brief description of the transcribed segment (e.g., "Dirty bathroom").

# Here’s the expected structure for the response:

# {
#   "transcription": "Speaker1: The bathroom was dirty.",
#   "categories": [
#     {
#       "topic": "Bathroom",
#       "sentiment": "negative",
#       "tag": "Dirty bathroom"
#     }
#   ]
# }

# ### Important Notes:
# - Make sure the sentiment is based on the overall tone of the transcription segment. For example, phrases like "could be better" would imply a negative sentiment, while "good experience" would be positive.
# - If no specific sentiment or category applies, return an empty array for **categories**.
# """

# @app.post("/upload/")
# async def process_audio(file: UploadFile = File(...), store_id: str = None):
#     try:
#         contents = await file.read()
#         mime_type = magic.from_buffer(contents, mime=True)
#         if not mime_type.startswith("audio/"):
#             raise HTTPException(status_code=400, detail="Invalid file type. Please upload an audio file.")

#         if store_id is None:
#             store_id = str(uuid.uuid4())

#         file_extension = file.filename.split(".")[-1]
#         file_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + f".{file_extension}"
#         file_path = os.path.join(UPLOAD_DIR, file_name)
#         with open(file_path, "wb") as f:
#             f.write(contents)

#         total_duration = get_audio_duration(file_path)
#         audio_blocks, silence_blocks = detect_audio_and_silence_ffmpeg(file_path)
#         transcription_list = []
#         one_to_many_speakers = set()
#         empty_block = len(silence_blocks) > 0
#         recording_start_time = datetime.utcnow()
#         gemini_prompt = get_gemini_prompt()

#         for start, end in audio_blocks:
#             audio_segment = AudioSegment.from_file(file_path)
#             start_ms, end_ms = int(start * 1000), int(end * 1000)
#             segment = audio_segment[start_ms:end_ms]

#             segment_bytes = io.BytesIO()
#             segment.export(segment_bytes, format="wav")
#             segment_bytes.seek(0)

#             response = model.generate_content([gemini_prompt, {"mime_type": "audio/wav", "data": segment_bytes.getvalue()}], stream=False)
#             response.resolve()
#             transcription_text = response.text.strip()

#             # Extract transcription and categories
#             transcription, categories = extract_transcription_and_categories(transcription_text)

#             # Extract speakers
#             speakers = re.findall(r"(Speaker\d+):", transcription)
#             one_to_many_speakers.update(speakers)

#             # Append to transcription list
#             transcription_list.append({
#                 "start": (recording_start_time + timedelta(seconds=start)).isoformat() + "Z",
#                 "end": (recording_start_time + timedelta(seconds=end)).isoformat() + "Z",
#                 "transcription": transcription,
#             })

#         # Insert into MongoDB
#         transcription_collection.insert_one({
#             "store_id": store_id,
#             "file_name": file_name,
#             "start": recording_start_time.isoformat() + "Z",
#             "end": (recording_start_time + timedelta(seconds=total_duration)).isoformat() + "Z",
#             "transcription": transcription_list,
#             "empty": empty_block,
#             "one_to_many": list(one_to_many_speakers),
#             "silence_blocks": [
#                 {"start": (recording_start_time + timedelta(seconds=start)).isoformat() + "Z",
#                  "end": (recording_start_time + timedelta(seconds=end)).isoformat() + "Z"}
#                 for start, end in silence_blocks
#             ]
#         })

#         return JSONResponse(content={
#             "message": "File processed successfully",
#             "store_id": store_id,
#             "file_name": file_name,
#             "transcription": transcription_list,
#             "empty": empty_block,
#             "one_to_many": list(one_to_many_speakers),
#             "silence_blocks": [
#                 {"start": (recording_start_time + timedelta(seconds=start)).isoformat() + "Z",
#                  "end": (recording_start_time + timedelta(seconds=end)).isoformat() + "Z"}
#                 for start, end in silence_blocks
#             ]
#         })
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.get("/get-transcriptions")
# async def get_transcriptions(
#     store_id: str,
#     file_name: str,
#     start: str,
#     end: str,
#     topic: Optional[str] = None
# ):
#     logging.info(f"Received request with store_id: {store_id}, file_name: {file_name}, start: {start}, end: {end}, topic: {topic}")

#     pipeline = [
#     {
#         "$match": {
#             "store_id": store_id,
#             "file_name": file_name
#         }
#     },
#     {
#         "$unwind": "$transcription"
#     },
#     {
#         "$match": {
#             "transcription.start": start,
#             "transcription.end": end
#         }
#     },
#     {
#         "$project": {
#             "_id": 0,
#             "start": "$transcription.start",
#             "end": "$transcription.end",
#             "transcription": "$transcription.transcription",
#             "categories": "$transcription.categories"
#         }
#     }
# ]


#     # Apply topic filter right after unwinding to correctly match per transcription
#     if topic:
#         pipeline.append({
#             "$match": {
#                 "transcription.categories.topic": topic
#             }
#         })

#     # Project the required fields after filtering
#     pipeline.extend([
#         {
#             "$project": {
#                 "_id": 0,
#                 "start": 1,
#                 "end": 1,
#                 "transcription": "$transcription.transcription",
#                 "categories": "$transcription.categories"
#             }
#         }
#     ])

#     # Run the aggregation pipeline
#     result = list(transcription_collection.aggregate(pipeline))

#     # Clean up transcription field if needed
#     # Clean up transcription field if needed
#     cleaned_result = []
#     for item in result:
#         # Check if 'transcription' exists in the item
#         if "transcription" in item and isinstance(item["transcription"], str):
#             # Remove the Markdown code blocks
#             cleaned_transcription = item["transcription"].replace("```json", "").replace("```", "").strip()
#             # Parse the cleaned transcription as JSON
#             try:
#                 parsed_transcription = json.loads(cleaned_transcription)
#                 item["transcription"] = parsed_transcription.get("transcription", "")
#                 item["categories"] = parsed_transcription.get("categories", [])
#             except json.JSONDecodeError:
#                 logging.warning(f"Failed to parse transcription: {cleaned_transcription}")
#                 item["transcription"] = cleaned_transcription  # Fallback to raw text if parsing fails
#         else:
#             logging.warning("Missing 'transcription' field in item: %s", item)
        
#         cleaned_result.append(item)

#     # Add metadata
#     response = {
#         "count": len(cleaned_result),
#         "transcriptions": cleaned_result
#     }

#     return response
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import io
import uuid
import magic
import google.generativeai as genai
from pydub import AudioSegment
from datetime import datetime, timedelta
from pymongo import MongoClient
from dotenv import load_dotenv
import re
import subprocess
import json
import logging
import noisereduce as nr
from dateutil.parser import parse
from typing import Optional
import librosa
import soundfile as sf

import pkg_resources
from noisereduce import reduce_noise as nr_reduce
# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure MongoDB
MONGO_URI = os.getenv("MONGODB_URI")
client = MongoClient(MONGO_URI)
db = client["audio_trans"]
transcription_collection = db["transcriptions"]

# Configure Google Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not set. Please set it in the .env file.")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

# Silence detection settings
SILENCE_THRESHOLD = -35  # dB
MIN_SILENCE_DURATION = 50  # seconds

# Directory for storing uploaded audio files
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def denoise_file(input_path, output_path=None):
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"File not found: {input_path}")
    y, sr = librosa.load(input_path, sr=None)
    reduced_noise = nr_reduce(y=y, sr=sr)
    if not output_path:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_denoised{ext}"
    sf.write(output_path, reduced_noise, sr)
    return output_path


def extract_transcription_and_categories(response_text):
    """Extract transcription and categories from JSON-embedded text."""
    try:
        cleaned_text = response_text.replace("```json", "").replace("```", "").strip()
        parsed_json = json.loads(cleaned_text)
        if isinstance(parsed_json, list):
            transcriptions = []
            for item in parsed_json:
                transcription = item.get("transcription", "").strip()
                categories = item.get("categories", [])
                cleaned_categories = [
                    {
                        "topic": category.get("topic", "").strip(),
                        "sentiment": category.get("sentiment", "").strip(),
                        "tag": category.get("tag", "").strip()
                    }
                    for category in categories
                ]
                transcriptions.append({"text": transcription, "categories": cleaned_categories})
            return transcriptions
        else:
            transcription = parsed_json.get("transcription", "").strip()
            categories = parsed_json.get("categories", [])
            cleaned_categories = [
                {
                    "topic": category.get("topic", "").strip(),
                    "sentiment": category.get("sentiment", "").strip(),
                    "tag": category.get("tag", "").strip()
                }
                for category in categories
            ]
            return [{"text": transcription, "categories": cleaned_categories}]
    except json.JSONDecodeError:
        return [{"text": response_text.strip(), "categories": []}]

def get_audio_duration(file_path):
    """Returns the duration of the audio file in seconds."""
    audio = AudioSegment.from_file(file_path)
    return len(audio) / 1000

def detect_audio_and_silence_ffmpeg(file_path):
    """Detects audio and silence segments using FFmpeg."""
    cmd = [
        "ffmpeg", "-i", file_path, "-af", f"silencedetect=noise={SILENCE_THRESHOLD}dB:d={MIN_SILENCE_DURATION}", "-f", "null", "-"
    ]
    process = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    output = process.stderr

    silence_blocks = []
    audio_blocks = []
    silence_start = None
    total_duration = get_audio_duration(file_path)

    for line in output.split("\n"):
        if "silence_start" in line:
            silence_start = float(line.split("silence_start: ")[1].strip())
        if "silence_end" in line and silence_start is not None:
            silence_end = float(line.split("silence_end: ")[1].split(" |")[0].strip())
            silence_duration = silence_end - silence_start
            if silence_duration >= MIN_SILENCE_DURATION:
                silence_blocks.append((silence_start, silence_end))
            silence_start = None

    last_end = 0.0
    for start, end in silence_blocks:
        if last_end < start:
            audio_blocks.append((last_end, start))
        last_end = end
    if last_end < total_duration:
        audio_blocks.append((last_end, total_duration))

    return audio_blocks, silence_blocks

def get_gemini_prompt():
    return """Analyze the provided audio transcript and extract relevant information. For each segment of the transcript, identify the speaker and return the transcribed text. Then, categorize the transcribed content based on the following predefined categories, using the provided structure:
1.**Topic**: The main category of the conversation (e.g., "Bathroom" or "Fuel Pump").
2. **Sentiment**: Based on the transcription, classify the sentiment as **positive**, **negative**, or **neutral**.
3. **Tag**: A short description of what was said in that segment (e.g., "Dirty bathroom" or "Out of order").

*Predefined Categories:*
* **Customer Experience**: Bathroom, Fuel Pump
* **Car Wash**: Vacuum, Air Machine
* **Cashier Engagement**: Greeting, Friendly, Knowledgeable, Helpful
* **Marketing & Promotion**: (No predefined subcategories)

---

### Expected Output:
Return a JSON object for each segment:
{
  "transcription": "Speaker1: The bathroom was dirty.",
  "categories": [
    {
      "topic": "Bathroom",
      "sentiment": "negative",
      "tag": "Dirty bathroom"
    }
  ]
}

### Notes:
- Sentiment should reflect the tone (e.g., "could be better" is negative, "good experience" is positive).
- If no category applies, return an empty array for **categories**.
"""

@app.post("/upload/")
async def process_audio(file: UploadFile = File(...), store_id: str = None):
    try:
        contents = await file.read()
        mime_type = magic.from_buffer(contents, mime=True)
        if not mime_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="Invalid file type. Please upload an audio file.")

        if store_id is None:
            store_id = str(uuid.uuid4())

        file_extension = file.filename.split(".")[-1]
        file_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + f".{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, file_name)
        with open(file_path, "wb") as f:
            f.write(contents)
        print(f"Saved file: {file_path}")

        # Apply noise reduction
        try:
            processed_file_path = denoise_file(file_path)
            print(f"Noise reduction completed: {processed_file_path}")
            denoised_file_name= os.path.basename(processed_file_path)
        except Exception as e:
            print(f"Noise reduction failed: {str(e)}. Using original file.")
            processed_file_path = file_path
            denoised_file_name = None

        total_duration = get_audio_duration(processed_file_path)
        logging.info(f"Duration: {total_duration}s")
        audio_blocks, silence_blocks = detect_audio_and_silence_ffmpeg(processed_file_path)
        logging.info(f"Audio blocks: {audio_blocks}, Silence blocks: {silence_blocks}")
        transcription_list = []
        one_to_many_speakers = set()
        empty_block = len(silence_blocks) > 0
        recording_start_time = datetime.utcnow()
        gemini_prompt = get_gemini_prompt()

        for start, end in audio_blocks:
            audio_segment = AudioSegment.from_file(processed_file_path)
            start_ms, end_ms = int(start * 1000), int(end * 1000)
            segment = audio_segment[start_ms:end_ms]

            segment_bytes = io.BytesIO()
            segment.export(segment_bytes, format="wav")
            segment_bytes.seek(0)

            response = model.generate_content([gemini_prompt, {"mime_type": "audio/wav", "data": segment_bytes.getvalue()}], stream=False)
            response.resolve()
            transcription_text = response.text.strip()
            logging.info(f"Gemini transcription: {transcription_text}")

            transcription_entries = extract_transcription_and_categories(transcription_text)
            for entry in transcription_entries:
                transcription = entry["text"]
                categories = entry["categories"]
                speakers = re.findall(r"(Speaker\d+):", transcription)
                one_to_many_speakers.update(speakers)
                transcription_list.append({
                    "start": (recording_start_time + timedelta(seconds=start)).isoformat() + "Z",
                    "end": (recording_start_time + timedelta(seconds=end)).isoformat() + "Z",
                    "transcription": transcription,
                    "categories": categories
                })

        client.server_info()
        transcription_collection.insert_one({
            "store_id": store_id,
            "file_name": file_name,
            "denoised_file": denoised_file_name if denoised_file_name else None,
            "start": recording_start_time.isoformat() + "Z",
            "end": (recording_start_time + timedelta(seconds=total_duration)).isoformat() + "Z",
            "transcriptions": transcription_list,
            "empty": empty_block,
            "one_to_many": list(one_to_many_speakers),
            "silence_blocks": [
                {"start": (recording_start_time + timedelta(seconds=start)).isoformat() + "Z",
                 "end": (recording_start_time + timedelta(seconds=end)).isoformat() + "Z"}
                for start, end in silence_blocks
            ]
        })
       
        response_content={
            "message": "File processed successfully",
            "store_id": store_id,
            "file_name": file_name,
            "denoised_file": denoised_file_name if denoised_file_name else None,
            "transcriptions": transcription_list,
            "empty": empty_block,
            "one_to_many": list(one_to_many_speakers),
            "silence_blocks": [
                {"start": (recording_start_time + timedelta(seconds=start)).isoformat() + "Z",
                 "end": (recording_start_time + timedelta(seconds=end)).isoformat() + "Z"}
                for start, end in silence_blocks
            ]
        }
        return JSONResponse(content=response_content)
    except Exception as e:
        logging.error(f"Error in process_audio: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
@app.get("/get-transcriptions")
async def get_transcriptions(
    start: str = Query(..., description="Start timestamp in ISO format"),
    end: str = Query(..., description="End timestamp in ISO format"),
    store_id: Optional[str] = None,
    file_name: Optional[str] = None,
    topic: Optional[str] = None
):
    logging.info(f"Received request with store_id: {store_id}, file_name: {file_name}, start: {start}, end: {end}, topic: {topic}")

    pipeline = []
    
    match_stage = {}
    if store_id:
        match_stage["store_id"] = store_id
    if file_name:
        match_stage["file_name"] = file_name
        
    if match_stage:
        pipeline.append({"$match": match_stage})

    pipeline.extend([
        {
            "$unwind": "$transcriptions"
        },
        {
            "$match": {
                "transcriptions.start": {"$gte": start, "$lte": end}
            }
        }
    ])

    # Apply topic filter if provided
    if topic:
        pipeline.append({
            "$match": {
                "transcriptions.categories.topic": topic
            }
        })

    # Project the required fields and apply limits
    pipeline.extend([
        {
            "$project": {
                "_id": 0,
                "store_id": 1,
                "file_name": 1,
                "start": "$transcriptions.start",
                "end": "$transcriptions.end",
                "transcription": "$transcriptions.transcription",
                "categories": "$transcriptions.categories"
            }
        },
        {
            "$sort": {"start": -1}
        },
        {
            "$limit": 500
        }
    ])

    # Run the aggregation pipeline
    result = list(transcription_collection.aggregate(pipeline))

    # Add metadata
    response = {
        "count": len(result),
        "transcriptions": result
    }

    return response
@app.get("/search")
async def search_sentiment(
    start: str = Query(..., description="Start timestamp in ISO format"),
    end: str = Query(..., description="End timestamp in ISO format"),
    store_id: Optional[str] = None,
    category: Optional[str] = None
):
    logging.info(f"Received search request: start={start}, end={end}, store_id={store_id}, category={category}")
    try:
        start_dt = parse(start)
        end_dt = parse(end)
        time_diff = (end_dt - start_dt).days
        logging.info(f"Time difference: {time_diff} days")

        if time_diff > 15:
            date_format = {"$dateToString": {"format": "%Y-%m-%dT00:00:00Z", "date": {"$dateFromString": {"dateString": "$transcriptions.start"}}}}
        else:
            date_format = {"$dateToString": {"format": "%Y-%m-%dT%H:00:00Z", "date": {"$dateFromString": {"dateString": "$transcriptions.start"}}}}

        pipeline = [
            {
                "$match": {
                    "transcriptions": {
                        "$elemMatch": {
                            "start": {"$gte": start, "$lte": end}
                        }
                    }
                }
            },
            *([{"$match": {"store_id": store_id}}] if store_id else []),
            {"$unwind": "$transcriptions"},
            {
                "$match": {
                    "transcriptions.start": {"$gte": start, "$lte": end}
                }
            },
            {"$unwind": "$transcriptions.categories"},
            *([{"$match": {"transcriptions.categories.topic": category}}] if category else []),
            {
                "$group": {
                    "_id": {
                        "date": date_format,
                        "sentiment": "$transcriptions.categories.sentiment"
                    },
                    "count": {"$sum": 1}
                }
            },
            {
                "$group": {
                    "_id": "$_id.date",
                    "sentiments": {
                        "$push": {
                            "sentiment": "$_id.sentiment",
                            "count": "$count"
                        }
                    }
                }
            },
            {"$sort": {"_id": 1}},
            {
                "$project": {
                    "_id": 0,
                    "date": "$_id",
                    "positive": {
                        "$sum": {
                            "$map": {
                                "input": "$sentiments",
                                "as": "s",
                                "in": {
                                    "$cond": [
                                        {"$eq": ["$$s.sentiment", "positive"]},
                                        "$$s.count",
                                        0
                                    ]
                                }
                            }
                        }
                    },
                    "negative": {
                        "$sum": {
                            "$map": {
                                "input": "$sentiments",
                                "as": "s",
                                "in": {
                                    "$cond": [
                                        {"$eq": ["$$s.sentiment", "negative"]},
                                        "$$s.count",
                                        0
                                    ]
                                }
                            }
                        }
                    },
                    "neutral": {
                        "$sum": {
                            "$map": {
                                "input": "$sentiments",
                                "as": "s",
                                "in":    {
                                    "$cond": [
                                        {"$eq": ["$$s.sentiment", "neutral"]},
                                        "$$s.count",
                                        0
                                    ]
                                }
                            }
                        }
                    }
                }
            }
        ]

        result = list(transcription_collection.aggregate(pipeline))
        logging.info(f"Pipeline result: {result}")
        return result

    except Exception as e:
        logging.error(f"Error in search_sentiment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
# Audio Transcription App

Audio Transcription App is a FastAPI-based backend with a React/Vite frontend for uploading audio, processing it into transcript segments, and viewing the results.

## Project Structure

- `main.py`: FastAPI backend and transcription API
- `frontend/`: React + Vite frontend
- `uploads/`, `temp_audio/`, `temp_files/`, `tmp_audio/`: local audio and processing files

## Requirements

- Python 3.10+
- Node.js 18+
- FFmpeg
- MongoDB
- A Google Gemini API key

## Backend Setup

1. Create and activate a Python virtual environment.
2. Install Python dependencies:

```bash
pip install -r requrements.txt
```

3. Add a `.env` file in the project root with:

```env
MONGODB_URI=your_mongodb_connection_string
GOOGLE_API_KEY=your_gemini_api_key
```

4. Start the API server:

```bash
uvicorn main:app --reload
```

## Frontend Setup

1. Go to the frontend folder:

```bash
cd frontend
```

2. Install frontend dependencies:

```bash
npm install
```

3. Run the development server:

```bash
npm run dev
```

## API Endpoints

- `POST /upload/`: upload and process an audio file
- `GET /get-transcriptions`: fetch transcription segments

## Notes

- Uploaded and processed files are written to local folders in the repo.
- The backend enables CORS so the frontend can call the API during development.

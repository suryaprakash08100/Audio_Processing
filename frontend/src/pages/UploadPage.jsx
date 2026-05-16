import React, { useState, useRef } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import { UploadCloud, FileAudio, CheckCircle, Clock } from 'lucide-react';

const API_URL = 'http://localhost:8000';

export default function UploadPage() {
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [result, setResult] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      if (selectedFile.type.startsWith('audio/')) {
        setFile(selectedFile);
        setResult(null); // Clear previous results
      } else {
        toast.error('Please select a valid audio file.');
      }
    }
  };

  const handleUpload = async () => {
    if (!file) {
      toast.error('No file selected');
      return;
    }

    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      // Create a toast that stays until processing is done
      const toastId = toast.loading('Uploading and analyzing audio... This may take a minute.');
      
      const response = await axios.post(`${API_URL}/upload/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      toast.success('Analysis complete!', { id: toastId });
      setResult(response.data);
    } catch (error) {
      console.error('Upload failed:', error);
      toast.error(error.response?.data?.detail || 'An error occurred during upload.');
    } finally {
      setIsUploading(false);
    }
  };

  const formatTime = (isoString) => {
    const date = new Date(isoString);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  return (
    <div className="animate-fade-in">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1>Upload Audio</h1>
          <p>Upload a conversation to transcribe and analyze sentiments.</p>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Upload Card */}
        <div className="glass glass-card flex flex-col items-center justify-center p-8 text-center" style={{ minHeight: '300px' }}>
          <div 
            className="UploadZone w-full h-full border-2 border-dashed rounded-lg flex flex-col items-center justify-center cursor-pointer transition"
            style={{ 
              borderColor: 'var(--surface-border)', 
              background: 'rgba(255,255,255,0.02)',
              padding: '2rem'
            }}
            onClick={() => fileInputRef.current?.click()}
          >
            <input 
              type="file" 
              ref={fileInputRef} 
              onChange={handleFileChange} 
              accept="audio/*" 
              className="hidden" 
              style={{ display: 'none' }}
            />
            
            {file ? (
              <div className="flex flex-col items-center gap-4">
                <div style={{ background: 'rgba(59, 130, 246, 0.2)', padding: '1rem', borderRadius: '50%' }}>
                  <FileAudio size={48} color="var(--accent-color)" />
                </div>
                <div>
                  <h3 style={{ marginBottom: '0.25rem' }}>{file.name}</h3>
                  <p>{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-4">
                 <div style={{ background: 'rgba(255, 255, 255, 0.05)', padding: '1rem', borderRadius: '50%' }}>
                  <UploadCloud size={48} color="var(--text-secondary)" />
                </div>
                <div>
                  <h3>Click or drag to upload</h3>
                  <p>Supports WAV, MP3, etc.</p>
                </div>
              </div>
            )}
          </div>

          {file && (
            <button 
              className="btn btn-primary mt-6 w-full" 
              onClick={handleUpload}
              disabled={isUploading}
            >
              {isUploading ? 'Processing...' : 'Analyze Audio'}
            </button>
          )}
        </div>

        {/* Results Card */}
        {result && (
          <div className="glass glass-card animate-fade-in">
            <div className="flex items-center gap-2 mb-4">
              <CheckCircle color="var(--success-color)" size={24} />
              <h2 style={{ marginBottom: 0 }}>Analysis Results</h2>
            </div>
            
            <div className="mb-6">
              <p><strong>Store ID:</strong> {result.store_id}</p>
              <p><strong>File Name:</strong> {result.file_name}</p>
            </div>

            <h3 className="mb-4">Transcriptions</h3>
            <div className="flex flex-col gap-4 max-h-[400px] overflow-y-auto pr-2">
              {result.transcriptions?.map((item, index) => (
                <div key={index} className="glass" style={{ padding: '1rem', background: 'rgba(0,0,0,0.2)' }}>
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex items-center gap-2 text-xs text-[var(--text-secondary)]">
                      <Clock size={14} />
                      {formatTime(item.start)} - {formatTime(item.end)}
                    </div>
                  </div>
                  <p className="mb-3" style={{ color: 'var(--text-primary)' }}>{item.transcription}</p>
                  
                  <div className="flex flex-wrap gap-2">
                    {item.categories?.map((cat, i) => (
                      <span key={i} className={`badge badge-${cat.sentiment}`}>
                        {cat.topic}: {cat.tag}
                      </span>
                    ))}
                  </div>
                </div>
              ))}

              {(!result.transcriptions || result.transcriptions.length === 0) && (
                <p className="text-center italic" style={{ color: 'var(--text-secondary)' }}>
                  No active conversations detected in this audio.
                </p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

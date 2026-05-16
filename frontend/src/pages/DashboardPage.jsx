import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Chart from 'react-apexcharts';
import { format, subDays } from 'date-fns';
import { Filter, RefreshCcw, Activity } from 'lucide-react';
import toast from 'react-hot-toast';

const API_URL = 'http://localhost:8000';

const TOPIC_OPTIONS = [
  { label: 'All Topics', value: '' },
  { label: 'Cashier Engagement', value: 'Cashier Engagement' },
  { label: 'Bathroom', value: 'Bathroom' },
  { label: 'Fuel Pump', value: 'Fuel Pump' },
  { label: 'Vacuum', value: 'Vacuum' },
  { label: 'Air Machine', value: 'Air Machine' },
  { label: 'Greeting', value: 'Greeting' },
  { label: 'Friendly', value: 'Friendly' },
  { label: 'Knowledgeable', value: 'Knowledgeable' },
  { label: 'Helpful', value: 'Helpful' },
];

export default function DashboardPage() {
  const [dateRange, setDateRange] = useState({
    start: format(subDays(new Date(), 365), "yyyy-MM-dd'T'HH:mm"),
    end: format(new Date(), "yyyy-MM-dd'T'HH:mm")
  });
  const [storeId, setStoreId] = useState('');
  const [topic, setTopic] = useState('');
  
  const [sentimentData, setSentimentData] = useState([]);
  const [transcriptions, setTranscriptions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      // Fetch Sentiment Aggregations
      // Send exact typed dates without shifting them across timezones
      const searchParams = new URLSearchParams({
        start: dateRange.start + ':00.000Z',
        end: dateRange.end + ':59.999Z',
      });
      if (storeId) searchParams.append('store_id', storeId);
      if (topic) searchParams.append('category', topic); // Backend uses category param for topic

      const searchRes = await axios.get(`${API_URL}/search?${searchParams.toString()}`);
      setSentimentData(searchRes.data);

      // Fetch Recent Transcriptions
      try {
        const transRes = await axios.get(`${API_URL}/get-transcriptions?${searchParams.toString()}`);
        setTranscriptions(transRes.data.transcriptions || []);
      } catch (err) {
        console.warn("Could not fetch transcriptions", err);
      }

    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      toast.error('Failed to load dashboard data.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [dateRange, storeId, topic]);

  // Transform sentiment data for ApexCharts
  const chartOptions = {
    chart: { type: 'bar', stacked: true, toolbar: { show: false }, background: 'transparent' },
    colors: ['#10b981', '#ef4444', '#94a3b8'], // Positive, Negative, Neutral
    plotOptions: { bar: { horizontal: false, borderRadius: 4, columnWidth: '40%' } },
    dataLabels: { enabled: false },
    stroke: { width: 1, colors: ['transparent'] },
    xaxis: {
      type: 'datetime',
      categories: sentimentData.map(item => item.date),
      labels: { style: { colors: '#94a3b8' } },
      axisBorder: { show: false },
      axisTicks: { show: false },
    },
    yaxis: {
      labels: { style: { colors: '#94a3b8' } },
    },
    legend: { position: 'top', horizontalAlign: 'right', labels: { colors: '#f8fafc' } },
    fill: { opacity: 1 },
    theme: { mode: 'dark' },
    grid: { borderColor: 'rgba(255,255,255,0.1)', strokeDashArray: 4 }
  };

  const chartSeries = [
    { name: 'Positive', data: sentimentData.map(item => item.positive) },
    { name: 'Negative', data: sentimentData.map(item => item.negative) },
    { name: 'Neutral', data: sentimentData.map(item => item.neutral) },
  ];

  return (
    <div className="animate-fade-in">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1>Sentiment Dashboard</h1>
          <p>Analyze trends and customer sentiment over time.</p>
        </div>
        <button className="btn btn-primary" onClick={fetchData} disabled={isLoading}>
          <RefreshCcw size={18} className={isLoading ? "animate-spin" : ""} />
          Refresh
        </button>
      </div>

      {/* Filter Controls */}
      <div className="glass glass-card mb-8">
        <div className="flex items-center gap-2 mb-4">
          <Filter size={20} color="var(--accent-color)" />
          <h3>Filters</h3>
        </div>
        <div className="grid md:grid-cols-4 gap-4">
          <div className="form-group mb-0">
            <label>Start Date</label>
            <input 
              type="datetime-local" 
              value={dateRange.start} 
              onChange={e => setDateRange({...dateRange, start: e.target.value})}
            />
          </div>
          <div className="form-group mb-0">
            <label>End Date</label>
            <input 
              type="datetime-local" 
              value={dateRange.end} 
              onChange={e => setDateRange({...dateRange, end: e.target.value})}
            />
          </div>
          <div className="form-group mb-0">
            <label>Store ID (Optional)</label>
            <input 
              type="text" 
              placeholder="e.g., store-123" 
              value={storeId} 
              onChange={e => setStoreId(e.target.value)}
            />
          </div>
          <div className="form-group mb-0">
            <label>Topic / Category</label>
            <select value={topic} onChange={e => setTopic(e.target.value)}>
              {TOPIC_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Chart Section */}
      <div className="glass glass-card mb-8">
        <div className="flex items-center justify-between mb-4">
          <div className="flex flex-col">
            <h3>Sentiment Trends</h3>
            <p style={{ fontSize: '0.875rem' }}>Aggregated interaction sentiment over the selected period</p>
          </div>
          <div style={{ background: 'rgba(59, 130, 246, 0.1)', padding: '0.5rem', borderRadius: '8px' }}>
             <Activity size={24} color="var(--accent-color)" />
          </div>
        </div>
        
        {sentimentData.length > 0 ? (
          <div style={{ height: '400px' }}>
            <Chart options={chartOptions} series={chartSeries} type="bar" height="100%" />
          </div>
        ) : (
          <div className="flex items-center justify-center p-8 text-center" style={{ height: '400px', border: '1px dashed var(--surface-border)', borderRadius: '8px' }}>
            <p>No data available for the selected filters. Try uploading an audio file or expanding the date range.</p>
          </div>
        )}
      </div>

      {/* Transcriptions Viewer Section */}
      <div className="glass glass-card mt-8">
        <div className="flex items-center justify-between mb-4">
          <div className="flex flex-col">
            <h3>Recent Conversations</h3>
            <p style={{ fontSize: '0.875rem' }}>Raw transcripts automatically matching your filters</p>
          </div>
        </div>
        
        <div className="flex flex-col gap-4 max-h-[600px] overflow-y-auto pr-2">
          {transcriptions.length > 0 ? (
            transcriptions.map((item, index) => (
              <div key={index} className="glass" style={{ padding: '1.25rem', background: 'rgba(0,0,0,0.2)' }}>
                <div className="flex justify-between items-start mb-2">
                  <div className="flex flex-col">
                    <span className="text-xs text-secondary mb-1" style={{ color: 'var(--text-secondary)' }}>
                      {new Date(item.start).toLocaleString()} &nbsp; | &nbsp; 
                      {item.store_id ? `Store: ${item.store_id}` : 'General'}
                    </span>
                  </div>
                </div>
                
                <p className="mb-3" style={{ color: 'var(--text-primary)', fontSize: '1.1rem' }}>
                  "{item.transcription}"
                </p>
                
                <div className="flex flex-wrap gap-2">
                  {item.categories?.map((cat, i) => (
                    <span key={i} className={`badge badge-${cat.sentiment}`}>
                      {cat.topic}: {cat.tag}
                    </span>
                  ))}
                  {(!item.categories || item.categories.length === 0) && (
                     <span className="badge badge-neutral">Uncategorized</span>
                  )}
                </div>
              </div>
            ))
          ) : (
            <div className="flex items-center justify-center p-8 text-center" style={{ border: '1px dashed var(--surface-border)', borderRadius: '8px' }}>
              <p>No typed transcriptions found for this date range. Try clearing specific filters or widening the range.</p>
            </div>
          )}
        </div>
      </div>

    </div>
  );
}

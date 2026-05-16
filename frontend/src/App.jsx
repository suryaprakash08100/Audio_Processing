import React from 'react';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { Headphones, LayoutDashboard, UploadCloud } from 'lucide-react';
import UploadPage from './pages/UploadPage';
import DashboardPage from './pages/DashboardPage';

function App() {
  return (
    <BrowserRouter>
      <Toaster position="top-right" toastOptions={{
        style: {
          background: 'var(--surface-color)',
          color: 'var(--text-primary)',
          border: '1px solid var(--surface-border)',
        }
      }} />
      <div className="app-layout">
        {/* Sidebar Navigation */}
        <aside className="sidebar">
          <div className="flex items-center gap-2 mb-8">
            <div style={{ background: 'var(--accent-color)', padding: '8px', borderRadius: '8px' }}>
              <Headphones size={24} color="white" />
            </div>
            <h2 style={{ marginBottom: 0, fontSize: '1.25rem' }}>AudioTrans</h2>
          </div>
          
          <nav className="sidebar-nav">
            <NavLink 
              to="/" 
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
              end
            >
              <LayoutDashboard size={20} />
              <span>Dashboard</span>
            </NavLink>
            <NavLink 
              to="/upload" 
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            >
              <UploadCloud size={20} />
              <span>Upload Audio</span>
            </NavLink>
          </nav>
        </aside>

        {/* Main Content Area */}
        <main className="main-content">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/upload" element={<UploadPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;

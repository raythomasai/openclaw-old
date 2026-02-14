'use client';

import React, { useState, useEffect } from 'react';
import Header from '../components/Header';

export default function ScholarPage() {
  return (
    <div style={{ minHeight: '100vh', background: '#f5f5f5' }}>
      <Header />
      <main style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
        <div style={{ 
          background: '#fff', 
          padding: '20px', 
          borderRadius: '8px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          <iframe 
            src="/scholar/index.html" 
            style={{ 
              width: '100%', 
              minHeight: '80vh',
              border: 'none'
            }}
            title="Scholar Research Index"
          />
        </div>
      </main>
      <footer style={{ textAlign: 'center', padding: '20px', color: '#666' }}>
        <span>Scholar Research</span>
        <span>•</span>
        <span>Powered by OpenClaw</span>
      </footer>
    </div>
  );
}

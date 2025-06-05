import React, { useState, useCallback, useEffect } from 'react';
import Webcam from 'react-webcam';
import './App.css';

function App() {
  const [facingMode, setFacingMode] = useState<string | { exact: string }>('environment');
  const [isMobile, setIsMobile] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const userAgent = navigator.userAgent;
    if (/android|iPad|iPhone|iPod/i.test(userAgent.toLowerCase())) {
      setIsMobile(true);
    }
  }, []);

  const videoConstraints: MediaStreamConstraints = {
    video: {
      facingMode: isMobile ? 'environment' : 'user'
    }
  };

  const switchCamera = useCallback(() => {
    setFacingMode((prevMode: string | { exact: string }) => 
      prevMode === 'environment' ? 'user' : 'environment'
    );
  }, []);

  const handleUserMediaError = (error: string) => {
    setError(`Camera access error: ${error}`);
  };

  return (
    <div className="App" style={{ display: 'flex', flexDirection: 'column', height: '100vh', justifyContent: 'center', alignItems: 'center' }}>
      <header className="App-header" style={{ width: '100%', textAlign: 'center', padding: '10px' }}>
        <h1 style={{ margin: 0 }}>Llama Astra Camera PWA</h1>
        {error ? (
          <div style={{ color: 'red', margin: '10px 0' }}>
            <p>{error}</p>
            <p>Please ensure camera permissions are granted and the camera is available.</p>
          </div>
        ) : (
          <div style={{ width: '90%', maxHeight: '80vh', margin: '10px auto', overflow: 'hidden', borderRadius: '10px', aspectRatio: '4 / 3' }}>
            <Webcam
              audio={false}
              screenshotFormat="image/jpeg"
              videoConstraints={videoConstraints}
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
              onUserMediaError={handleUserMediaError}
            />
          </div>
        )}
        <button onClick={switchCamera} style={{ margin: '10px 0', padding: '10px 20px', fontSize: '16px', cursor: 'pointer' }}>
          Switch Camera
        </button>
        <p style={{ margin: 0, fontSize: '14px' }}>Install this app on your device for the best experience.</p>
      </header>
    </div>
  );
}

export default App; 
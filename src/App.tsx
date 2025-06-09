import React, { useState, useCallback, useEffect } from 'react';
import Webcam from 'react-webcam';
import './App.css';

function App() {
  const [facingMode, setFacingMode] = useState<string | { exact: string }>('environment');
  const [isMobile, setIsMobile] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cameraReady, setCameraReady] = useState(false);

  useEffect(() => {
    const userAgent = navigator.userAgent;
    if (/android|iPad|iPhone|iPod/i.test(userAgent.toLowerCase())) {
      setIsMobile(true);
    }
    
    // Request camera permissions
    navigator.mediaDevices?.getUserMedia({ video: true })
      .then(() => {
        setCameraReady(true);
        setError(null);
      })
      .catch((err) => {
        setError(`Camera permission denied: ${err.message}`);
      });
  }, []);

  const videoConstraints = {
    video: {
      facingMode: facingMode
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

  const handleUserMedia = (stream: MediaStream) => {
    setCameraReady(true);
    setError(null);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Llama Astra Camera PWA</h1>
        {error ? (
          <div className="error-message">
            <p>{error}</p>
            <p>Please ensure camera permissions are granted and the camera is available.</p>
          </div>
        ) : (
          <div className="camera-container">
            <Webcam
              audio={false}
              screenshotFormat="image/jpeg"
              videoConstraints={videoConstraints}
              className="camera-feed"
              onUserMediaError={handleUserMediaError}
              onUserMedia={handleUserMedia}
            />
          </div>
        )}
        <div className="camera-controls">
          <button onClick={switchCamera} className="control-button">
            Switch Camera
          </button>
        </div>
        <p className="status-text">
          {cameraReady ? 'Camera ready!' : 'Loading camera...'}
        </p>
        <p className="status-text">
          Install this app on your device for the best experience.
        </p>
      </header>
    </div>
  );
}

export default App; 
import { useState, useEffect, useRef, useMemo } from "react";
import FingerprintJS from "@fingerprintjs/fingerprintjs";
import { useNavigate } from 'react-router-dom';
import "./captcha-form.css";

const CaptchaForm = () => {
  
  const [usaiId, setUsaiId] = useState("");
  const [honeypot, setHoneypot] = useState("");
  const [message, setMessage] = useState("");
  const [isBlocked, setIsBlocked] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [verificationResult, setVerificationResult] = useState(null);
  const navigate = useNavigate();
  const startTimeRef = useRef(Date.now());

  const goToHttpBotPage = () => {
    navigate('/http-bot-check');
  };

  const inputId = useMemo(
    () => `input_${Math.random().toString(36).slice(2, 10)}`,
    []
  );
  const buttonId = useMemo(
    () => `btn_${Math.random().toString(36).slice(2, 10)}`,
    []
  );

  // Check honeypot after hooks are defined
  useEffect(() => {
    if (honeypot.trim()) {
      setMessage("Suspicious activity detected!");
      setIsBlocked(true);
    }
  }, [honeypot]);

  // Generate browser fingerprint
  const generateFingerprint = async () => {
    try {
      const fp = await FingerprintJS.load();
      const result = await fp.get();
      return result.visitorId;
    } catch (error) {
      console.error('Error generating fingerprint:', error);
      return 'fingerprint_error';
    }
  };

  // Collect comprehensive browser information
  const collectBrowserInfo = async () => {
    const fingerprint = await generateFingerprint();
    const requestTime = Date.now();
    const timeSincePageLoad = requestTime - startTimeRef.current;

    return {
      fingerprint,
      screen: {
        width: window.screen.width,
        height: window.screen.height,
        colorDepth: window.screen.colorDepth
      },
      viewport: {
        width: window.innerWidth,
        height: window.innerHeight
      },
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      language: navigator.language,
      languages: navigator.languages,
      platform: navigator.platform,
      cookiesEnabled: navigator.cookieEnabled,
      doNotTrack: navigator.doNotTrack,
      timeSincePageLoad,
      timestamp: new Date().toISOString()
    };
  };

  // Initialize session and cookies
  const initializeSession = async () => {
    try {
      console.log("Initializing session and cookies...");
      const response = await fetch('http://127.0.0.1:8000/httpbot_detector/init/', {
        method: 'GET',
        credentials: 'include',  // Important: include cookies
        headers: {
          'Accept': 'application/json'
        }
      });
      
      if (response.ok) {
        const result = await response.json();
        console.log("Session initialized:", result);
        return result.session_data; // Return full session data including CSRF token
      } else {
        console.warn("Session initialization failed, continuing without session");
        return null;
      }
    } catch (error) {
      console.warn("Session initialization error:", error);
      return null;
    }
  };

  const handleVerify = async () => {
    if (!usaiId.trim()) {
      setMessage("Please enter a USAI ID");
      return;
    }

    if (isBlocked) {
      setMessage("Verification blocked due to suspicious activity");
      return;
    }

    setIsLoading(true);
    setMessage("Verifying user...");

    try {
      console.log("Starting verification process...");
      
      // Step 1: Initialize session and cookies
      const sessionData = await initializeSession();
      console.log("Backend session data:", sessionData);
      
      const browserInfo = await collectBrowserInfo();
      console.log("Browser info collected:", browserInfo);
      
      // Use backend-generated session ID and CSRF token
      const sessionId = sessionData?.session_id || `fallback_${Date.now()}`;
      const csrfToken = sessionData?.csrf_token || '';
      console.log("Using session ID:", sessionId);
      console.log("Using CSRF token:", csrfToken ? "Present" : "Not available");
      
      // Prepare comprehensive request data
      const requestData = {
        usai_id: usaiId,
        browser_info: browserInfo,
        verification_timestamp: new Date().toISOString()
      };
      console.log("Request data prepared:", requestData);

      // Debug: Check cookies being sent
      console.log("Document cookies:", document.cookie);

      const requestUrl = 'http://127.0.0.1:8000/httpbot_detector/detect/';
      const requestHeaders = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Session-ID': sessionId,
        'X-Requested-With': 'XMLHttpRequest',
        'X-USAI-ID': usaiId,
        'X-Browser-Fingerprint': browserInfo.fingerprint,
        'X-Verification-Type': 'usai-verification',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
      };
      
      // Add CSRF token if available
      if (csrfToken) {
        requestHeaders['X-CSRFToken'] = csrfToken;
      }
      
      console.log("Sending request to:", requestUrl);
      console.log("Request headers:", requestHeaders);
      console.log("Request body:", JSON.stringify(requestData));

      const response = await fetch(requestUrl, {
        method: 'POST',
        headers: requestHeaders,
         credentials: "include",
        body: JSON.stringify(requestData)
      });

      console.log('Response status:', response.status);
      console.log('Response headers:', response.headers);
      console.log('Response ok:', response.ok);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Error response body:', errorText);
        throw new Error(`HTTP ${response.status}: ${response.statusText} - ${errorText}`);
      }

      const result = await response.json();
      console.log('Backend response:', result);
      setVerificationResult(result);

      if (result.status === 'blocked') {
        setIsBlocked(true);
        setMessage(result.message || "Access blocked - automated client detected");
      } else if (result.status === 'allowed') {
        setMessage(result.message || "Verification successful - legitimate user detected");
      } else {
        setMessage("Verification completed with warnings");
      }

    } catch (error) {
      console.error('Verification error:', error);
      
      // Provide more specific error messages
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        setMessage("Connection failed - please ensure the backend server is running on port 8000");
      } else if (error.name === 'SyntaxError') {
        setMessage("Invalid response from server - please check backend configuration");
      } else if (error.message.includes('NetworkError') || error.message.includes('Failed to fetch')) {
        setMessage("Network error - please check your connection and CORS settings");
      } else {
        setMessage(`Verification failed: ${error.message || 'Unknown error'} - please try again`);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="form-container">
      <h1>HTTP Bot Verification System</h1>
      <p>Enter your USAI ID to verify your identity</p>
      
      {/* Honeypot field */}
      <input
        type="text"
        value={honeypot}
        onChange={(e) => setHoneypot(e.target.value)}
        style={{ display: "none" }}
        tabIndex="-1"
        autoComplete="off"
      />
      
      {/* Main input field */}
      <div className="input-group">
        <label htmlFor={inputId}>USAI ID:</label>
        <input
          type="text"
          value={usaiId}
          onChange={(e) => setUsaiId(e.target.value)}
          placeholder="Enter your USAI ID"
          id={inputId}
          disabled={isLoading || isBlocked}
          className={isBlocked ? "blocked" : ""}
        />
      </div>
      
      {/* Verify button */}
      <button 
        id={buttonId}
        onClick={handleVerify}
        disabled={isLoading || isBlocked || !usaiId.trim()}
        className={isLoading ? "loading" : ""}
      >
        {isLoading ? "Verifying..." : "Verify User"}
      </button>
      
      {/* Status message */}
      <div className={`message ${isBlocked ? "error-message" : "success-message"}`}>
        {message}
      </div>

      {/* Verification results */}
      {verificationResult && (
        <div className="verification-results">
          <h3>Verification Results:</h3>
          <div className="result-grid">
            <div><strong>Status:</strong> {verificationResult.status}</div>
            <div><strong>Classification:</strong> {verificationResult.classification}</div>
            <div><strong>Confidence:</strong> {verificationResult.confidence}%</div>
            <div><strong>Bot Probability:</strong> {verificationResult.bot_probability}%</div>
            <div><strong>Cookies Present:</strong> {verificationResult.cookies_present ? 'Yes' : 'No'}</div>
            {verificationResult.cookies && (
              <>
                <div><strong>Session ID:</strong> {verificationResult.cookies.sessionid || 'Not set'}</div>
                <div><strong>CSRF Token:</strong> {verificationResult.cookies.csrftoken ? 'Present' : 'Not set'}</div>
              </>
            )}
            {verificationResult.detection_id && (
              <div><strong>Detection ID:</strong> {verificationResult.detection_id}</div>
            )}
          </div>
          
          {verificationResult.detected_indicators && (
            <div className="indicators">
              <h4>Detection Indicators:</h4>
              <ul>
                {Object.entries(verificationResult.detected_indicators).map(([key, value]) => (
                  <li key={key}>
                    <strong>{key.replace(/_/g, ' ')}:</strong> {value.toString()}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
      
      
      
      <div className="info-text">
        <p>
          This system analyzes your request patterns, browser characteristics, and behavior 
          to distinguish between legitimate users and automated clients.
        </p>
      </div>
    </div>
  );
};

export default CaptchaForm;

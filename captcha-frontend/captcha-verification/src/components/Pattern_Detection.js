import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from 'react-router-dom';
import "./captcha-form.css";
import globalBehavioralTracker from '../utils/globalBehavioralTracker';

const Pattern_Detection = () => {
  const navigate = useNavigate();

  // Initialize state with global behavioral tracker data
  const [behavioralData, setBehavioralData] = useState(() => {
    return globalBehavioralTracker.getBehavioralData();
  });

  // Initialize global behavioral tracking for pattern detection page
  useEffect(() => {
    console.log('🚀 PATTERN DETECTION page mounted - checking behavioral tracker state');
    
    // 🔄 Notify global tracker of page change but keep tracking continuous
    if (window.globalBehavioralTrackerInstance) {
      console.log('🔄 Triggering behavioral continuity for pattern detection page load');
      window.globalBehavioralTrackerInstance.handleUrlChange(
        'component_mount', 
        window.location.href
      );
    }
    
    globalBehavioralTracker.setCurrentPage('pattern_detection');
    console.log('✅ PATTERN DETECTION page initialized with continuous behavioral tracking');
    
    return () => {
      console.log('🔄 PATTERN DETECTION page cleanup - maintaining behavioral tracking continuity');
    };
  }, []);

  // Real-time sync with global behavioral tracker to maintain continuity
  useEffect(() => {
    const syncInterval = setInterval(() => {
      const freshData = globalBehavioralTracker.getBehavioralData();
      setBehavioralData(freshData);
      
      // Update global tracker with pattern detection specific data
      globalBehavioralTracker.updateBehavioralData({
        currentPage: 'pattern_detection',
        pageVisitTime: Date.now(),
        navigationContext: 'pattern_analysis'
      });
    }, 1000);
    
    return () => clearInterval(syncInterval);
  }, []);

  const cursorMovements = behavioralData.cursorMovements || [];
  const keyPressTimes = behavioralData.keyPressTimes || [];
  const clickTimestamps = behavioralData.clickTimestamps || [];
  const scrollSpeeds = behavioralData.scrollSpeeds || [];
  const actionCount = behavioralData.actionCount || 0;
  const lastActionTime = behavioralData.lastActionTime || Date.now();
  const pageLoadTime = behavioralData.pageLoadTime || Date.now();

  // Pattern analysis specific functions
  const analyzePatterns = () => {
    console.log('🔍 Analyzing behavioral patterns...');
    // Pattern analysis logic here
  };

  // Effect to log behavioral insights
  useEffect(() => {
    console.log('📊 Pattern Detection - Behavioral insights:', {
      totalCursorMovements: cursorMovements.length,
      totalKeyPresses: keyPressTimes.length,
      totalClicks: clickTimestamps.length,
      scrollEvents: scrollSpeeds.length,
      actionCount,
      sessionDuration: Date.now() - pageLoadTime
    });
  }, [cursorMovements.length, keyPressTimes.length, clickTimestamps.length, scrollSpeeds.length, actionCount, pageLoadTime]);

  // Clear behavioral data on logout/reset
  const handleClearData = () => {
    globalBehavioralTracker.clearSession();
    console.log('🧹 Pattern Detection behavioral data cleared');
  };

  return (
    <div style={{ padding: "20px" }}>
      <h1>🔍 Pattern Detection</h1>
      <p>
        This page detects patterns in user behavior and compares against known baselines.
        All interactions are being tracked by the global behavioral system.
      </p>
      
      <div style={{ marginTop: "20px", padding: "10px", border: "1px solid #ccc", backgroundColor: "#f9f9f9" }}>
        <h3>📊 Live Behavioral Metrics</h3>
        <ul>
          <li>🖱️ Cursor Movements: {cursorMovements.length} recorded</li>
          <li>⌨️ Key Presses: {keyPressTimes.length} recorded</li>
          <li>👆 Click Events: {clickTimestamps.length} recorded</li>
          <li>📜 Scroll Events: {scrollSpeeds.length} recorded</li>
          <li>📈 Total Actions: {actionCount}</li>
          <li>⏱️ Page Load Time: {new Date(pageLoadTime).toLocaleTimeString()}</li>
        </ul>
      </div>

      <div style={{ marginTop: "20px", padding: "10px", border: "1px solid #ccc" }}>
        <h3>🎯 Pattern Analysis Status</h3>
        <ul>
          <li>Cursor Movement: {cursorMovements.length > 0 ? "✅ Active Tracking" : "⏳ Waiting for input"}</li>
          <li>Click Frequency: {clickTimestamps.length > 0 ? `${clickTimestamps.length} clicks recorded` : "⏳ No clicks yet"}</li>
          <li>Keystroke Speed: {keyPressTimes.length > 0 ? `${keyPressTimes.length} keystrokes tracked` : "⏳ No typing yet"}</li>
          <li>Global Tracker: {window.globalBehavioralTrackerInstance ? "🟢 Connected" : "🔴 Disconnected"}</li>
        </ul>
      </div>

      <div style={{ marginTop: "20px" }}>
        <button 
          onClick={handleClearData}
          style={{ 
            padding: "10px 20px", 
            backgroundColor: "#ff4444", 
            color: "white", 
            border: "none", 
            borderRadius: "5px",
            cursor: "pointer"
          }}
        >
          🧹 Clear Behavioral Data
        </button>
      </div>
    </div>
  );
};

export default Pattern_Detection;

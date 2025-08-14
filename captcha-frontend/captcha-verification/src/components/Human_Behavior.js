import React, { useState, useEffect } from "react";
import { useNavigate } from 'react-router-dom';
import "./captcha-form.css";
import globalBehavioralTracker from '../utils/globalBehavioralTracker';

const Human_Behavior = () => {
  const navigate = useNavigate();

  // Initialize state with global behavioral tracker data
  const [behavioralData, setBehavioralData] = useState(() => {
    return globalBehavioralTracker.getBehavioralData();
  });

  // Initialize global behavioral tracking for human behavior page
  useEffect(() => {
    console.log('🚀 HUMAN BEHAVIOR page mounted - checking behavioral tracker state');
    
    // 🔄 Notify global tracker of page change but keep tracking continuous
    if (window.globalBehavioralTrackerInstance) {
      console.log('🔄 Triggering behavioral continuity for human behavior page load');
      window.globalBehavioralTrackerInstance.handleUrlChange(
        'component_mount', 
        window.location.href
      );
    }
    
    globalBehavioralTracker.setCurrentPage('human_behavior');
    console.log('✅ HUMAN BEHAVIOR page initialized with continuous behavioral tracking');
    
    return () => {
      console.log('🔄 HUMAN BEHAVIOR page cleanup - maintaining behavioral tracking continuity');
    };
  }, []);

  // Real-time sync with global behavioral tracker to maintain continuity
  useEffect(() => {
    const syncInterval = setInterval(() => {
      const freshData = globalBehavioralTracker.getBehavioralData();
      setBehavioralData(freshData);
      
      // Update global tracker with human behavior specific data
      globalBehavioralTracker.updateBehavioralData({
        currentPage: 'human_behavior',
        pageVisitTime: Date.now(),
        navigationContext: 'human_behavior_analysis'
      });
    }, 1000);
    
    return () => clearInterval(syncInterval);
  }, []);

  // Extract data for display
  const cursorMovements = behavioralData.cursorMovements || [];
  const keyPressTimes = behavioralData.keyPressTimes || [];
  const clickTimestamps = behavioralData.clickTimestamps || [];
  const scrollSpeeds = behavioralData.scrollSpeeds || [];
  const actionCount = behavioralData.actionCount || 0;
  const lastActionTime = behavioralData.lastActionTime || Date.now();
  const pageLoadTime = behavioralData.pageLoadTime || Date.now();

  // Human behavior analysis specific functions
  const analyzeHumanConfidence = () => {
    const totalActions = cursorMovements.length + keyPressTimes.length + clickTimestamps.length;
    
    // Simple human confidence calculation
    let confidence = 0;
    if (totalActions > 10) confidence += 30;
    if (cursorMovements.length > 5) confidence += 25;
    if (keyPressTimes.length > 3) confidence += 25;
    if (!behavioralData.isAutomatedBrowser) confidence += 20;
    
    return Math.min(confidence, 100);
  };

  // Effect to log behavioral insights for human behavior analysis
  useEffect(() => {
    const humanConf = analyzeHumanConfidence();
    console.log('👤 Human Behavior Analysis - Behavioral insights:', {
      totalCursorMovements: cursorMovements.length,
      totalKeyPresses: keyPressTimes.length,
      totalClicks: clickTimestamps.length,
      scrollEvents: scrollSpeeds.length,
      actionCount,
      humanConfidence: humanConf,
      sessionDuration: Date.now() - pageLoadTime
    });
  }, [cursorMovements.length, keyPressTimes.length, clickTimestamps.length, scrollSpeeds.length, actionCount, pageLoadTime]);

  // Clear behavioral data on reset
  const handleClearData = () => {
    globalBehavioralTracker.clearSession();
    console.log('🧹 Human Behavior behavioral data cleared');
  };

  // Determine human behavior status
  const getHumanStatus = () => {
    const humanConfidence = analyzeHumanConfidence();
    if (humanConfidence === 0) return { icon: "⏳", text: "Initializing...", color: "#orange" };
    if (humanConfidence >= 80) return { icon: "✅", text: "High Confidence Human", color: "#green" };
    if (humanConfidence >= 60) return { icon: "🟢", text: "Likely Human", color: "#darkgreen" };
    if (humanConfidence >= 40) return { icon: "🟡", text: "Moderate Confidence", color: "#orange" };
    return { icon: "🔴", text: "Low Human Confidence", color: "#red" };
  };

  const status = getHumanStatus();

  // Calculate behavior metrics safely
  const avgCursorSpeed = cursorMovements.length > 1 ? 
    cursorMovements.reduce((acc, curr, i) => {
      if (i === 0) return acc;
      const prev = cursorMovements[i - 1];
      if (!prev || !curr || typeof prev !== 'object' || typeof curr !== 'object') return acc;
      
      const currX = curr.x || 0;
      const currY = curr.y || 0;
      const prevX = prev.x || 0;
      const prevY = prev.y || 0;
      const currTime = curr.timestamp || 0;
      const prevTime = prev.timestamp || 0;
      
      const distance = Math.sqrt(Math.pow(currX - prevX, 2) + Math.pow(currY - prevY, 2));
      const time = currTime - prevTime;
      return acc + (time > 0 ? distance / time : 0);
    }, 0) / (cursorMovements.length - 1) : 0;

  const avgKeyInterval = keyPressTimes.length > 1 ?
    keyPressTimes.reduce((acc, curr, i) => {
      if (i === 0) return acc;
      return acc + (curr - keyPressTimes[i - 1]);
    }, 0) / (keyPressTimes.length - 1) : 0;

  return (
    <div style={{ padding: "20px" }}>
      <h1>👤 Human Behavior Analysis</h1>
      <p>
        This page analyzes user behavior patterns to determine human characteristics and 
        identify natural interaction patterns. All analysis is performed using global tracking data.
      </p>
      
      <div style={{ marginTop: "20px", padding: "10px", border: "1px solid #ccc", backgroundColor: "#f9f9f9" }}>
        <h3>📊 Live Behavioral Metrics</h3>
        <ul>
          <li>🖱️ Cursor Movements: {cursorMovements.length} recorded</li>
          <li>⌨️ Key Presses: {keyPressTimes.length} recorded</li>
          <li>👆 Click Events: {clickTimestamps.length} recorded</li>
          <li>📜 Scroll Events: {scrollSpeeds.length} recorded</li>
          <li>📈 Total Actions: {actionCount}</li>
          <li>🕒 Session Duration: {Math.floor((Date.now() - pageLoadTime) / 1000)}s</li>
        </ul>
      </div>

      <div style={{ marginTop: "20px", padding: "10px", border: "1px solid #ccc" }}>
        <h3>🧠 Human Behavior Assessment</h3>
        <div style={{ fontSize: "18px", marginBottom: "10px" }}>
          <span style={{ color: status.color, fontSize: "24px" }}>{status.icon}</span>
          <span style={{ marginLeft: "10px", color: status.color, fontWeight: "bold" }}>{status.text}</span>
        </div>
        <ul>
          <li>Human Confidence: {analyzeHumanConfidence()}%</li>
          <li>Average Cursor Speed: {avgCursorSpeed.toFixed(2)} px/ms</li>
          <li>Average Key Interval: {avgKeyInterval.toFixed(2)} ms</li>
          <li>Global Tracker: {window.globalBehavioralTrackerInstance ? "🟢 Connected" : "🔴 Disconnected"}</li>
        </ul>
      </div>

      <div style={{ marginTop: "20px", padding: "10px", border: "1px solid #ccc", backgroundColor: "#fffacd" }}>
        <h3>🔍 Behavior Pattern Analysis</h3>
        <ul>
          <li>Natural Movement: {cursorMovements.length > 10 ? "✅ Detected" : "⏳ Insufficient data"}</li>
          <li>Variable Timings: {keyPressTimes.length > 5 ? "✅ Detected" : "⏳ Insufficient data"}</li>
          <li>Organic Clicks: {clickTimestamps.length > 3 ? "✅ Detected" : "⏳ Insufficient data"}</li>
          <li>Scroll Variability: {scrollSpeeds.length > 5 ? "✅ Detected" : "⏳ Insufficient data"}</li>
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
            cursor: "pointer",
            marginRight: "10px"
          }}
        >
          🧹 Clear Behavior Data
        </button>
        
        <button 
          onClick={() => globalBehavioralTracker.updateBehavioralData({ humanConfidence: 0 })}
          style={{ 
            padding: "10px 20px", 
            backgroundColor: "#4444ff", 
            color: "white", 
            border: "none", 
            borderRadius: "5px",
            cursor: "pointer"
          }}
        >
          🔄 Reset Analysis
        </button>
      </div>
    </div>
  );
};

export default Human_Behavior;

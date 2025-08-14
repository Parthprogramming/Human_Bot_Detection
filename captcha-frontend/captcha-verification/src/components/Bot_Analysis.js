import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from 'react-router-dom';
import "./captcha-form.css";
import globalBehavioralTracker from '../utils/globalBehavioralTracker';

const Bot_Analysis = () => {
  const navigate = useNavigate();

  // Initialize state with global behavioral tracker data
  const [behavioralData, setBehavioralData] = useState(() => {
    return globalBehavioralTracker.getBehavioralData();
  });

  // Initialize global behavioral tracking for bot analysis page
  useEffect(() => {
    console.log('🚀 BOT ANALYSIS page mounted - checking behavioral tracker state');
    
    // 🔄 Notify global tracker of page change but keep tracking continuous
    if (window.globalBehavioralTrackerInstance) {
      console.log('🔄 Triggering behavioral continuity for bot analysis page load');
      window.globalBehavioralTrackerInstance.handleUrlChange(
        'component_mount', 
        window.location.href
      );
    }
    
    globalBehavioralTracker.setCurrentPage('bot_analysis');
    console.log('✅ BOT ANALYSIS page initialized with continuous behavioral tracking');
    
    return () => {
      console.log('🔄 BOT ANALYSIS page cleanup - maintaining behavioral tracking continuity');
    };
  }, []);

  // Real-time sync with global behavioral tracker to maintain continuity
  useEffect(() => {
    const syncInterval = setInterval(() => {
      const freshData = globalBehavioralTracker.getBehavioralData();
      setBehavioralData(freshData);
      
      // Update global tracker with bot analysis specific data
      globalBehavioralTracker.updateBehavioralData({
        currentPage: 'bot_analysis',
        pageVisitTime: Date.now(),
        navigationContext: 'bot_analysis'
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
  const botProbability = behavioralData.botProbability || 0;
  const isAutomatedBrowser = behavioralData.isAutomatedBrowser || false;

  // Bot analysis specific functions
  const analyzeBotProbability = () => {
    const totalActions = cursorMovements.length + keyPressTimes.length + clickTimestamps.length;
    
    // Simple bot probability calculation (can be enhanced)
    let probability = 0;
    if (isAutomatedBrowser) probability += 50;
    if (totalActions > 0 && cursorMovements.length === 0) probability += 30;
    if (behavioralData.evasionSignals && Object.keys(behavioralData.evasionSignals).length > 0) probability += 20;
    
    return Math.min(probability, 100);
  };

  // Effect to log behavioral insights for bot analysis
  useEffect(() => {
    const botProb = analyzeBotProbability();
    console.log('🤖 Bot Analysis - Behavioral insights:', {
      totalCursorMovements: cursorMovements.length,
      totalKeyPresses: keyPressTimes.length,
      totalClicks: clickTimestamps.length,
      scrollEvents: scrollSpeeds.length,
      actionCount,
      isAutomatedBrowser,
      botProbability: botProb,
      sessionDuration: Date.now() - pageLoadTime
    });
  }, [cursorMovements.length, keyPressTimes.length, clickTimestamps.length, scrollSpeeds.length, actionCount, isAutomatedBrowser, pageLoadTime]);

  // Clear behavioral data on logout/reset
  const handleClearData = () => {
    globalBehavioralTracker.clearSession();
    console.log('🧹 Bot Analysis behavioral data cleared');
  };

  // Determine bot status based on probability
  const getBotStatus = () => {
    if (botProbability === 0) return { icon: "⏳", text: "Analyzing...", color: "#orange" };
    if (botProbability < 30) return { icon: "✅", text: "Human", color: "#green" };
    if (botProbability < 70) return { icon: "⚠️", text: "Suspicious", color: "#orange" };
    return { icon: "🚫", text: "Bot Detected", color: "#red" };
  };

  const status = getBotStatus();

  return (
    <div style={{ padding: "20px" }}>
      <h1>🤖 Bot Analysis</h1>
      <p>
        This page runs bot detection algorithms and displays whether the current session is automated.
        Advanced behavioral analysis is performed using global tracking data.
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

      <div style={{ 
        marginTop: "20px", 
        padding: "15px", 
        border: `2px solid ${status.color}`, 
        backgroundColor: `${status.color}15`,
        borderRadius: "8px"
      }}>
        <h3>🎯 Detection Status</h3>
        <div style={{ fontSize: "18px", fontWeight: "bold", marginBottom: "10px" }}>
          Bot Probability: {botProbability.toFixed(1)}%
        </div>
        <div style={{ fontSize: "20px", color: status.color, fontWeight: "bold" }}>
          Status: {status.icon} {status.text}
        </div>
        <div style={{ marginTop: "10px", fontSize: "14px" }}>
          <div>Automated Browser: {isAutomatedBrowser ? "🔴 Detected" : "🟢 Not Detected"}</div>
          <div>Global Tracker: {window.globalBehavioralTrackerInstance ? "🟢 Active" : "🔴 Inactive"}</div>
        </div>
      </div>

      <div style={{ marginTop: "20px", padding: "10px", border: "1px solid #ccc" }}>
        <h3>🔍 Analysis Details</h3>
        <ul>
          <li>Behavioral Consistency: {cursorMovements.length > 10 ? "🟢 Sufficient Data" : "🟡 Collecting..."}</li>
          <li>Interaction Patterns: {(keyPressTimes.length + clickTimestamps.length) > 5 ? "🟢 Natural" : "🟡 Limited"}</li>
          <li>Movement Entropy: {cursorMovements.length > 20 ? "🟢 Human-like" : "🟡 Insufficient"}</li>
          <li>Timing Analysis: {actionCount > 10 ? "🟢 Complete" : "🟡 In Progress"}</li>
        </ul>
      </div>

      <div style={{ marginTop: "20px" }}>
        <button 
          
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
          🧹 Clear Analysis Data
        </button>
        
        <button 
          
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

export default Bot_Analysis;

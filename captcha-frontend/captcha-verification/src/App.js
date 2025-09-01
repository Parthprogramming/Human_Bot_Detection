import logo from './logo.svg';
import './App.css';
import Verification from "./components/captcha-form";
import Http_bot from "./components/http_client_verification";
import Auth_used from "./components/auth_user";
import Sign_in from "./components/sign-in";
import Sign_up from "./components/sign-up";
import Patter_Detection from "./components/Pattern_Detection";
import Bot_Analysis from "./components/Bot_Analysis";
import Human_Behavior from "./components/Human_Behavior";
import globalBehavioralTracker from './utils/globalBehavioralTracker';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { useEffect } from 'react';

// Component to handle route changes and behavioral tracking
function RouteChangeHandler() {
  const location = useLocation();
  
  useEffect(() => {
    console.log('🔄 Route changed to:', location.pathname);
    
    // Trigger behavioral reset for route changes
    if (window.globalBehavioralTrackerInstance) {
      console.log('🔄 Triggering behavioral reset for route change');
      window.globalBehavioralTrackerInstance.handleUrlChange(
        'route_change', 
        window.location.href
      );
    }
  }, [location]);
  
  return null; // This component doesn't render anything
}

function App() {
  useEffect(() => {
    // Initialize global behavioral tracker
    if (typeof window !== 'undefined') {
      window.globalBehavioralTrackerInstance = globalBehavioralTracker;
    }

    // Optional: Listen for tracking events
    const handleTrackingStart = (event) => {
      console.log('🎯 Auth route tracking started:', event.detail);
    };

    const handleTrackingStop = (event) => {
      console.log('🛑 Auth route tracking stopped:', event.detail);
    };

    window.addEventListener('authRouteTrackingStarted', handleTrackingStart);
    window.addEventListener('authRouteTrackingStopped', handleTrackingStop);

    return () => {
      window.removeEventListener('authRouteTrackingStarted', handleTrackingStart);
      window.removeEventListener('authRouteTrackingStopped', handleTrackingStop);
    };
  }, []);

  return (
    <Router>
      <RouteChangeHandler />
      <Routes>
        <Route path="/" element={<Verification />} />
        <Route path="/http-bot-check" element={<Http_bot />} />
        <Route path="/auth-user" element={<Auth_used />} />
        <Route path="/sign-in" element={<Sign_in />} />
        <Route path="/sign-up" element={<Sign_up />} />
        <Route path="/pattern-detection" element={<Patter_Detection />} />
        <Route path="/bot-analysis" element={<Bot_Analysis />} />
        <Route path="/human-behavior" element={<Human_Behavior />} />
      </Routes>
    </Router>
  );
}

export default App;

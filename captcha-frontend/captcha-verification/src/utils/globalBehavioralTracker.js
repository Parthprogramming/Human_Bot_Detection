/**
 * Global Behavioral Tracking System
 * Tracks user behavior continuously across all pages/components
 * Persists data in localStorage and manages session-wide behavioral analytics
 */

class GlobalBehavioralTracker {
  constructor() {
    this.isInitialized = false;
    this.sessionId = null;
    this.trackingStartTime = null;
    this.lastSaveTime = 0;
    this.saveInterval = 2000; // Save every 2 seconds
    this.isTracking = false;
    
    // Event listeners storage for cleanup
    this.eventListeners = [];
    
    // Behavioral data storage
    this.behavioralData = {
      sessionId: null,
      trackingStartTime: null,
      pageLoadTime: null,
      cursorMovements: [],
      cursorSpeeds: [],
      cursorAcceleration: [],
      cursorJitter: [],
      keyPressTimes: [],
      cursorCurvature: [],
      keyHoldTimes: [],
      clickTimes: [],
      scrollSpeeds: [],
      scrollChanges: 0,
      idleTime: 0,
      pasteDetected: false,
      clickTimestamps: [],
      lastKeyPress: null,
      lastKeyDown: {},
      lastMouseMove: null,
      lastClickTime: null,
      lastScroll: 0,
      latestSpeed: 0,
      allSpeeds: [],
      lastUpdateTime: 0,
      lastScrollTime: Date.now(),
      pasteTimestamp: null,
      cursorEntropy: 0,
      botFingerprintScore: null,
      submitTime: null,
      TabKeyCount: 0,
      cursorAngles: [],
      postPasteActivity: {
        keyPresses: 0,
        mouseMoves: 0,
        clicks: 0,
        timeToFirstAction: null,
        timeToLastAction: null,
        actionsAfterPaste: [],
        clipboardContent: null,
      },
      mouseTrajectory: [],
      keyboardPatterns: [],
      deviceInfo: {},
      isAutomatedBrowser: false,
      lastActionTime: Date.now(),
      actionCount: 0,
      suspiciousPatterns: [],
      botDetectionResults: null,
      mouseJitter: [],
      microPauses: [],
      hesitationTimes: [],
      lastHoverStart: null,
      deviceFingerprint: null,
      canvasMetrics: {
        winding: null,
        geometryLength: 0,
        textLength: 0,
      },
      missingCanvasFingerprint: true,
      audio_fp_entropy_low: null,
      evasionSignals: {},
      unusualScreenResolution: {
        width_height: "0x0",
        inner_width: 0,
        device_pixel_ratio: 0,
        is_unusual: false,
        spoofedMismatch: false,
        aspectRatio: 0,
      },
      gpuInfo: {
        gpu_name: null,
        vendor: null,
        renderer: null,
        webgl_info: null,
        capabilities: null,
        extensions: [],
        driver_info: null,
        graphics_api: null
      },
      gpublacklist: {
        gpu_name_blacklisted: false,
        gpu_name: null,
      },
      timingMetrics: {},
      cursorMicroJitter: 0,
      pathEntropy: 0,
      accelerationVariance: 0,
      fittsDeviationScore: 0,
      idleResumeAngularJerk: 0,
      thermalHoverNoise: 0,
      hoverPositions: [],
      currentPage: null,
      pageHistory: [],
      totalSessionTime: 0,
      crossPageMetrics: {
        totalPageTransitions: 0,
        avgTimePerPage: 0,
        totalActions: 0,
        avgActionsPerPage: 0
      }
    };
    
    // Storage keys
    this.STORAGE_KEY = 'global_behavioral_session';
    this.SESSION_KEY = 'behavioral_session_id';
    
    this.init();
  }
  
  init() {
    if (this.isInitialized) return;
    
    // Load existing session or create new one
    this.loadSession();
    
    // Start global tracking
    this.startGlobalTracking();
    
    // Set up periodic saving
    this.setupPeriodicSaving();
    
    // Set up page unload handler
    this.setupUnloadHandler();
    
    this.isInitialized = true;
    console.log('🚀 Global Behavioral Tracker initialized');
  }
  
  loadSession() {
    try {
      // Check for existing session ID
      const existingSessionId = localStorage.getItem(this.SESSION_KEY);
      const existingData = localStorage.getItem(this.STORAGE_KEY);
      
      if (existingSessionId && existingData) {
        // Continue existing session
        this.sessionId = existingSessionId;
        this.behavioralData = { ...this.behavioralData, ...JSON.parse(existingData) };
        this.trackingStartTime = this.behavioralData.trackingStartTime || Date.now();
        console.log('📋 Continuing existing behavioral session:', this.sessionId);
      } else {
        // Create new session
        this.sessionId = this.generateSessionId();
        this.trackingStartTime = Date.now();
        this.behavioralData.sessionId = this.sessionId;
        this.behavioralData.trackingStartTime = this.trackingStartTime;
        
        localStorage.setItem(this.SESSION_KEY, this.sessionId);
        console.log('🆕 New behavioral session created:', this.sessionId);
      }
    } catch (error) {
      console.error('Error loading session:', error);
      this.createNewSession();
    }
  }
  
  createNewSession() {
    this.sessionId = this.generateSessionId();
    this.trackingStartTime = Date.now();
    this.behavioralData.sessionId = this.sessionId;
    this.behavioralData.trackingStartTime = this.trackingStartTime;
    localStorage.setItem(this.SESSION_KEY, this.sessionId);
  }
  
  generateSessionId() {
    return 'behavioral_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }
  
  startGlobalTracking() {
    if (this.isTracking) return;
    
    this.isTracking = true;
    
    // Mouse movement tracking
    const handleMouseMove = (event) => {
      this.trackMouseMovement(event);
    };
    
    // Keyboard tracking
    const handleKeyDown = (event) => {
      this.trackKeyDown(event);
    };
    
    const handleKeyUp = (event) => {
      this.trackKeyUp(event);
    };
    
    // Click tracking
    const handleClick = (event) => {
      this.trackClick(event);
    };
    
    // Scroll tracking
    const handleScroll = (event) => {
      this.trackScroll(event);
    };
    
    // Paste tracking
    const handlePaste = (event) => {
      this.trackPaste(event);
    };
    
    // Add all event listeners
    this.addEventListener(document, 'mousemove', handleMouseMove);
    this.addEventListener(document, 'keydown', handleKeyDown);
    this.addEventListener(document, 'keyup', handleKeyUp);
    this.addEventListener(document, 'click', handleClick);
    this.addEventListener(window, 'scroll', handleScroll);
    this.addEventListener(document, 'paste', handlePaste);
    
    console.log('🎯 Global behavioral tracking started');
  }
  
  addEventListener(element, event, handler) {
    element.addEventListener(event, handler);
    this.eventListeners.push({ element, event, handler });
  }
  
  removeAllEventListeners() {
    this.eventListeners.forEach(({ element, event, handler }) => {
      element.removeEventListener(event, handler);
    });
    this.eventListeners = [];
    this.isTracking = false;
    console.log('🛑 All behavioral event listeners removed');
  }
  
  trackMouseMovement(event) {
    const now = Date.now();
    const newPoint = {
      x: event.clientX,
      y: event.clientY,
      timestamp: now,
      page: this.behavioralData.currentPage
    };
    
    // Throttle mouse tracking
    if (now - this.behavioralData.lastUpdateTime < 50) return;
    
    // Store movement with page context
    this.behavioralData.cursorMovements = [
      ...this.behavioralData.cursorMovements.slice(-499), // Keep last 500 movements
      newPoint
    ];
    
    // Calculate speed if we have previous movement
    if (this.behavioralData.lastMouseMove) {
      const dx = newPoint.x - this.behavioralData.lastMouseMove.x;
      const dy = newPoint.y - this.behavioralData.lastMouseMove.y;
      const dt = (now - this.behavioralData.lastMouseMove.timestamp) / 1000;
      
      if (dt > 0) {
        const distance = Math.sqrt(dx * dx + dy * dy);
        const speed = distance / dt;
        
        if (speed > 0 && speed < 5000) { // Filter out unrealistic speeds
          this.behavioralData.cursorSpeeds = [
            ...this.behavioralData.cursorSpeeds.slice(-99),
            speed
          ];
          this.behavioralData.latestSpeed = speed;
        }
      }
    }
    
    this.behavioralData.lastMouseMove = newPoint;
    this.behavioralData.lastUpdateTime = now;
    this.behavioralData.actionCount++;
    this.behavioralData.lastActionTime = now;
  }
  
  trackKeyDown(event) {
    const now = Date.now();
    this.behavioralData.lastKeyDown[event.key] = now;
    
    if (event.key === 'Tab') {
      this.behavioralData.TabKeyCount++;
    }
    
    this.behavioralData.actionCount++;
    this.behavioralData.lastActionTime = now;
  }
  
  trackKeyUp(event) {
    const now = Date.now();
    const keyDownTime = this.behavioralData.lastKeyDown[event.key];
    
    if (keyDownTime) {
      const holdTime = now - keyDownTime;
      this.behavioralData.keyHoldTimes = [
        ...this.behavioralData.keyHoldTimes.slice(-99),
        holdTime
      ];
      delete this.behavioralData.lastKeyDown[event.key];
    }
    
    this.behavioralData.keyPressTimes = [
      ...this.behavioralData.keyPressTimes.slice(-99),
      now
    ];
    
    this.behavioralData.lastKeyPress = now;
  }
  
  trackClick(event) {
    const now = Date.now();
    
    this.behavioralData.clickTimestamps = [
      ...this.behavioralData.clickTimestamps.slice(-99),
      now
    ];
    
    // Calculate click intervals
    if (this.behavioralData.lastClickTime) {
      const interval = now - this.behavioralData.lastClickTime;
      this.behavioralData.clickTimes = [
        ...this.behavioralData.clickTimes.slice(-99),
        interval
      ];
    }
    
    this.behavioralData.lastClickTime = now;
    this.behavioralData.actionCount++;
    this.behavioralData.lastActionTime = now;
  }
  
  trackScroll(event) {
    const now = Date.now();
    this.behavioralData.scrollChanges++;
    
    // Calculate scroll speed
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    const timeDiff = now - this.behavioralData.lastScrollTime;
    const scrollDiff = Math.abs(scrollTop - this.behavioralData.lastScroll);
    
    if (timeDiff > 0) {
      const scrollSpeed = scrollDiff / timeDiff;
      this.behavioralData.scrollSpeeds = [
        ...this.behavioralData.scrollSpeeds.slice(-99),
        scrollSpeed
      ];
    }
    
    this.behavioralData.lastScroll = scrollTop;
    this.behavioralData.lastScrollTime = now;
    this.behavioralData.actionCount++;
    this.behavioralData.lastActionTime = now;
  }
  
  trackPaste(event) {
    this.behavioralData.pasteDetected = true;
    this.behavioralData.pasteTimestamp = Date.now();
    
    try {
      const clipboardContent = event.clipboardData.getData('text');
      this.behavioralData.postPasteActivity.clipboardContent = clipboardContent;
    } catch (error) {
      console.warn('Could not access clipboard content:', error);
    }
  }
  
  setCurrentPage(pageName) {
    const now = Date.now();
    const previousPage = this.behavioralData.currentPage;
    
    if (previousPage && previousPage !== pageName) {
      // Track page transition
      this.behavioralData.crossPageMetrics.totalPageTransitions++;
      
      // Calculate time spent on previous page
      const pageStartTime = this.behavioralData.pageHistory.find(
        p => p.page === previousPage && !p.endTime
      );
      
      if (pageStartTime) {
        pageStartTime.endTime = now;
        pageStartTime.duration = now - pageStartTime.startTime;
      }
    }
    
    this.behavioralData.currentPage = pageName;
    this.behavioralData.pageHistory.push({
      page: pageName,
      startTime: now,
      endTime: null,
      duration: null
    });
    
    console.log(`📄 Page tracking: ${pageName}`);
  }
  
  updateCrossPageMetrics() {
    const completedPages = this.behavioralData.pageHistory.filter(p => p.duration !== null);
    
    if (completedPages.length > 0) {
      const totalTime = completedPages.reduce((sum, page) => sum + page.duration, 0);
      this.behavioralData.crossPageMetrics.avgTimePerPage = totalTime / completedPages.length;
    }
    
    this.behavioralData.crossPageMetrics.totalActions = this.behavioralData.actionCount;
    
    if (this.behavioralData.pageHistory.length > 0) {
      this.behavioralData.crossPageMetrics.avgActionsPerPage = 
        this.behavioralData.actionCount / this.behavioralData.pageHistory.length;
    }
    
    this.behavioralData.totalSessionTime = Date.now() - this.trackingStartTime;
  }
  
  setupPeriodicSaving() {
    setInterval(() => {
      this.saveToStorage();
    }, this.saveInterval);
  }
  
  saveToStorage() {
    try {
      this.updateCrossPageMetrics();
      
      // Update session time
      this.behavioralData.totalSessionTime = Date.now() - this.trackingStartTime;
      
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.behavioralData));
      this.lastSaveTime = Date.now();
      
      // Send to backend for analysis (if needed)
      this.sendToBackend();
      
    } catch (error) {
      console.error('Error saving behavioral data:', error);
    }
  }
  
  async sendToBackend() {
    try {
      // Only send if we have significant data
      if (this.behavioralData.actionCount < 5) return;
      
      const response = await fetch('/user/behavioral-analysis/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: this.sessionId,
          behavioral_data: this.behavioralData
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        console.log('📊 Behavioral analysis result:', result.user_auth_status);
        
        // Store analysis result
        this.behavioralData.lastAnalysisResult = result;
        
        // Emit custom event for components to react to
        window.dispatchEvent(new CustomEvent('behavioralAnalysis', {
          detail: result
        }));
      }
    } catch (error) {
      console.warn('Could not send behavioral data to backend:', error);
    }
  }
  
  setupUnloadHandler() {
    const handleUnload = () => {
      // Final save before page unload
      this.updateCrossPageMetrics();
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.behavioralData));
      console.log('💾 Final behavioral data save on unload');
    };
    
    window.addEventListener('beforeunload', handleUnload);
    window.addEventListener('pagehide', handleUnload);
  }
  
  getBehavioralData() {
    this.updateCrossPageMetrics();
    return { ...this.behavioralData };
  }
  
  getSessionId() {
    return this.sessionId;
  }
  
  clearSession() {
    // Clear all tracking data and stop tracking
    this.removeAllEventListeners();
    localStorage.removeItem(this.STORAGE_KEY);
    localStorage.removeItem(this.SESSION_KEY);
    
    // Reset data
    this.behavioralData = {
      ...this.behavioralData,
      cursorMovements: [],
      keyPressTimes: [],
      clickTimestamps: [],
      // ... reset all arrays and counters
    };
    
    console.log('🧹 Behavioral session cleared');
  }
  
  // Methods for components to update specific behavioral data
  updateBehavioralData(updates) {
    this.behavioralData = { ...this.behavioralData, ...updates };
  }
  
  // Get current statistics
  getSessionStats() {
    this.updateCrossPageMetrics();
    
    return {
      sessionId: this.sessionId,
      sessionDuration: Date.now() - this.trackingStartTime,
      totalActions: this.behavioralData.actionCount,
      currentPage: this.behavioralData.currentPage,
      pagesVisited: this.behavioralData.pageHistory.length,
      totalMouseMovements: this.behavioralData.cursorMovements.length,
      totalKeyPresses: this.behavioralData.keyPressTimes.length,
      totalClicks: this.behavioralData.clickTimestamps.length,
      crossPageMetrics: this.behavioralData.crossPageMetrics,
      lastAnalysis: this.behavioralData.lastAnalysisResult
    };
  }
}

// Create global instance
const globalBehavioralTracker = new GlobalBehavioralTracker();

export default globalBehavioralTracker;

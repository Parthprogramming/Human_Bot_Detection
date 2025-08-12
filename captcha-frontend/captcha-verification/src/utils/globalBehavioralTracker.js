/**
 * Global Behavioral Tracking System
 * Tracks user behavior continuously across all pages/components
 * Persists data in localStorage and manages session-wide behavioral analytics
 */

class GlobalBehavioralTracker {
  constructor() {
    // 🔍 DEBUG: Check for multiple instances
    if (window.globalBehavioralTrackerInstance) {
      console.warn('⚠️ Multiple GlobalBehavioralTracker instances detected!');
      console.warn('Existing instance:', window.globalBehavioralTrackerInstance);
      console.warn('New instance:', this);
    }
    window.globalBehavioralTrackerInstance = this;
    
    this.isInitialized = false;
    this.sessionId = null;
    this.trackingStartTime = null;
    this.lastSaveTime = 0;
    this.saveInterval = 2000; // Save to localStorage every 2 seconds
    this.backendInterval = 1000; // Send to backend every 1 second
    this.isTracking = false;
    
    // Event listeners storage for cleanup
    this.eventListeners = [];
    this.backendIntervalId = null;
    
    // 🎯 CRITICAL: Store baseline timer ID for persistence across pages
    this.baselineTimerId = null;
    
    // Behavioral data storage
    this.behavioralData = {
      sessionId: null,
      trackingStartTime: null,
      pageLoadTime: null,
      
      // Baseline collection state
      isCollectingBaseline: false,
      baselineCollectionStartTime: null,
      baselineCollectionDuration: 20000, // 20 seconds baseline collection
      baselineCompleted: false,
      baselineBehaviorData: null,
      baselineTimerId: null, // 🎯 Store timer ID for persistence
      
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
    
    // 🎯 START BASELINE COLLECTION IMMEDIATELY IN BACKGROUND
    this.startBackgroundBaselineCollection();

    this.isInitialized = true;
    console.log('🚀 Global Behavioral Tracker initialized with background baseline collection');
    
    // Show baseline status
    if (this.behavioralData.isCollectingBaseline) {
      console.log('✅ Baseline collection is ACTIVE - Duration:', this.behavioralData.baselineCollectionDuration/1000, 'seconds');
    } else if (this.behavioralData.baselineCompleted) {
      console.log('ℹ️ Baseline already completed. To restart: window.globalBehavioralTrackerInstance.debugForceStartBaseline()');
    }
  }
  
  loadSession() {
    try {
      // Check for existing session ID
      const existingSessionId = localStorage.getItem(this.SESSION_KEY);
      const existingData = localStorage.getItem(this.STORAGE_KEY);
      
      if (existingSessionId && existingData) {
        // Continue existing session
        this.sessionId = existingSessionId;
        const loadedData = JSON.parse(existingData);
        
        // 🛡️ Safely merge loaded data, ensuring all essential properties exist
        this.behavioralData = { 
          ...this.behavioralData, 
          ...loadedData,
          // Ensure critical arrays exist
          pageHistory: loadedData.pageHistory || [],
          cursorMovements: loadedData.cursorMovements || [],
          cursorSpeeds: loadedData.cursorSpeeds || [],
          keyPressTimes: loadedData.keyPressTimes || [],
          clickTimestamps: loadedData.clickTimestamps || [],
          scrollSpeeds: loadedData.scrollSpeeds || [],
          // Ensure cross-page metrics exist
          crossPageMetrics: {
            totalPageTransitions: 0,
            avgTimePerPage: 0,
            totalActions: 0,
            avgActionsPerPage: 0,
            ...(loadedData.crossPageMetrics || {})
          }
        };
        
        this.trackingStartTime = this.behavioralData.trackingStartTime || Date.now();
        
        console.log('📋 Continuing existing behavioral session:', this.sessionId);
        console.log('📊 Session state:', {
          baselineCompleted: this.behavioralData.baselineCompleted,
          isCollectingBaseline: this.behavioralData.isCollectingBaseline
        });
        
        // 🎯 CRITICAL: Recover baseline timer if collection is in progress
        this.recoverBaselineTimer();
        
        // 🚨 IMPORTANT: Don't auto-start continuous transmission on session load
        // Only start it when explicitly triggered by baseline completion
        
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

  // 🎯 CRITICAL: Recover baseline timer after page navigation/reload
  recoverBaselineTimer() {
    // Only recover if baseline collection is in progress but not completed
    if (!this.behavioralData.isCollectingBaseline || this.behavioralData.baselineCompleted) {
      return;
    }
    
    // Calculate remaining time for baseline collection
    const now = Date.now();
    const startTime = this.behavioralData.baselineCollectionStartTime;
    const totalDuration = this.behavioralData.baselineCollectionDuration;
    const elapsed = now - startTime;
    const remaining = totalDuration - elapsed;
    
    console.log(`🔄 Recovering baseline timer - Elapsed: ${elapsed}ms, Remaining: ${remaining}ms`);
    
    if (remaining <= 0) {
      // Timer should have already fired, complete it now
      console.log('⏰ Baseline collection time already passed, completing immediately');
      this.completeBackgroundBaselineCollection();
      return;
    }
    
    // 🛡️ Clear any existing timer first
    if (this.baselineTimerId) {
      clearTimeout(this.baselineTimerId);
    }
    
    // Set new timer for remaining time
    this.baselineTimerId = setTimeout(() => {
      this.completeBackgroundBaselineCollection();
    }, remaining);
    
    // Update stored timer reference
    this.behavioralData.baselineTimerId = this.baselineTimerId;
    
    console.log(`🎯 Baseline timer recovered - ${remaining}ms remaining, Timer ID: ${this.baselineTimerId}`);
  }

  // 🛡️ SAFE SESSION RESET - for debugging and error recovery
  forceResetSession() {
    console.warn('🔄 Force resetting behavioral tracking session...');
    
    // Clear all localStorage data
    localStorage.removeItem(this.SESSION_KEY);
    localStorage.removeItem(this.STORAGE_KEY);
    
    // Stop any ongoing intervals
    if (this.backendIntervalId) {
      clearInterval(this.backendIntervalId);
      this.backendIntervalId = null;
    }
  }

  // 🔧 DEBUG: Reset only baseline collection for testing
  debugResetBaseline() {
    console.warn('🔧 DEBUG: Resetting baseline collection...');
    
    if (this.baselineTimerId) {
      clearTimeout(this.baselineTimerId);
      this.baselineTimerId = null;
    }
    
    this.behavioralData.baselineCompleted = false;
    this.behavioralData.isCollectingBaseline = false;
    this.behavioralData.baselineCollectionStartTime = null;
    this.behavioralData.baselineTimerId = null;
    this.behavioralData.baselineBehaviorData = null;
    
    this.saveSession();
    return this;
  }

  // 🔧 DEBUG: Force start baseline collection (even if already completed)
  debugForceStartBaseline() {
    console.warn('🔧 DEBUG: Force starting baseline collection...');
    this.debugResetBaseline();
    this.startBackgroundBaselineCollection();
    return this;
  }

  // 🔧 DEBUG: Check current baseline state
  debugBaselineState() {
    const data = this.behavioralData;
    console.log('🔧 BASELINE STATE:', {
      collecting: data.isCollectingBaseline,
      completed: data.baselineCompleted,
      startTime: data.baselineCollectionStartTime,
      hasData: !!data.baselineBehaviorData
    });
    return data;
  }

  debugTestBaselineTransmission() {
    console.warn('🔧 DEBUG: Testing baseline transmission...');
    
    if (!this.behavioralData.baselineBehaviorData) {
      console.error('🔧 No baseline data to transmit');
      return;
    }
    
    this.sendBaselineToBackend().then(result => {
      console.log('🔧 Transmission result:', result);
    }).catch(error => {
      console.error('🔧 Transmission error:', error);
    });
    
    return this;
  }

  // 🔧 DEBUG: Manually complete baseline collection for testing
  debugCompleteBaseline() {
    console.warn('🔧 DEBUG: Completing baseline collection...');
    
    if (!this.behavioralData.isCollectingBaseline) {
      console.error('🔧 Baseline collection not active');
      return;
    }
    
    this.completeBackgroundBaselineCollection();
    return this;
  }
  
  // 🛡️ Defensive programming - Ensure all essential arrays are initialized
  ensureArraysInitialized() {
    const requiredArrays = [
      'cursorMovements', 'cursorSpeeds', 'allSpeeds', 'keyPressTimes', 
      'clickTimestamps', 'clickTimes', 'scrollSpeeds', 'keyHoldTimes',
      'cursorAcceleration', 'cursorJitter', 'mouseJitter', 'micropause',
      'hesitation', 'mouseTrajectory', 'keyboardPatterns', 'suspiciousPatterns'
    ];
    
    requiredArrays.forEach(arrayName => {
      if (!Array.isArray(this.behavioralData[arrayName])) {
        this.behavioralData[arrayName] = [];
        console.warn(`🛡️ Initialized missing array: ${arrayName}`);
      }
    });
    
    // Ensure objects are initialized
    const requiredObjects = [
      'lastKeyDown', 'postPasteActivity', 'canvasMetrics', 'unusualScreenResolution',
      'gpuInfo', 'gpublacklist', 'timingMetrics', 'evasionSignals', 'crossPageMetrics'
    ];
    
    requiredObjects.forEach(objName => {
      if (typeof this.behavioralData[objName] !== 'object' || this.behavioralData[objName] === null) {
        this.behavioralData[objName] = {};
        console.warn(`🛡️ Initialized missing object: ${objName}`);
      }
    });
    
    // Ensure crossPageMetrics has required properties
    if (!this.behavioralData.crossPageMetrics.totalPageTransitions) {
      this.behavioralData.crossPageMetrics = {
        totalPageTransitions: 0,
        avgTimePerPage: 0,
        totalActions: 0,
        avgActionsPerPage: 0,
        ...this.behavioralData.crossPageMetrics
      };
    }
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
    
    // 🛡️ Ensure arrays are initialized
    this.ensureArraysInitialized();
    
    // 🎯 RECORD BASELINE EVENT if collecting baseline
    if (this.behavioralData.isCollectingBaseline) {
      this.recordBaselineEvent('mouseMove', event, now);
    }
    
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
    
    // 🛡️ Ensure arrays and objects are initialized
    this.ensureArraysInitialized();
    if (!this.behavioralData.lastKeyDown) {
      this.behavioralData.lastKeyDown = {};
    }
    
    this.behavioralData.lastKeyDown[event.key] = now;
    
    // 🎯 RECORD BASELINE EVENT if collecting baseline
    if (this.behavioralData.isCollectingBaseline) {
      this.recordBaselineEvent('keyPress', event, now);
    }
    
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
    
    // 🎯 RECORD BASELINE EVENT if collecting baseline
    if (this.behavioralData.isCollectingBaseline) {
      this.recordBaselineEvent('click', event, now);
    }
    
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
    
    // 🎯 RECORD BASELINE EVENT if collecting baseline
    if (this.behavioralData.isCollectingBaseline) {
      this.recordBaselineEvent('scroll', event, now);
    }
    
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
    
    // 🛡️ Ensure pageHistory is initialized (defensive programming)
    if (!this.behavioralData.pageHistory) {
      this.behavioralData.pageHistory = [];
    }
    
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
    // 🛡️ Ensure pageHistory exists
    if (!this.behavioralData.pageHistory) {
      this.behavioralData.pageHistory = [];
    }
    
    // 🛡️ Ensure crossPageMetrics exists
    if (!this.behavioralData.crossPageMetrics) {
      this.behavioralData.crossPageMetrics = {
        totalPageTransitions: 0,
        avgTimePerPage: 0,
        totalActions: 0,
        avgActionsPerPage: 0
      };
    }
    
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
    // Save to localStorage every 2 seconds
    setInterval(() => {
      this.saveToStorage();
    }, this.saveInterval);
    
    // DON'T start backend transmission here - only after baseline collection
    // Backend transmission will be started by startContinuousTransmission() after baseline
    
    console.log('🔄 Set up periodic saving (2s) - backend transmission will start after baseline collection');
  }
  
  saveToStorage() {
    try {
      this.updateCrossPageMetrics();
      
      // Update session time
      this.behavioralData.totalSessionTime = Date.now() - this.trackingStartTime;
      
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.behavioralData));
      this.lastSaveTime = Date.now();
      
    } catch (error) {
      console.error('Error saving behavioral data:', error);
    }
  }
  
  async sendToBackend() {
    try {
      // 🔍 DEBUG: Log why this function is being called
      console.log('🔍 DEBUG: sendToBackend called', {
        timestamp: new Date().toISOString(),
        stackTrace: new Error().stack.split('\n').slice(1, 4), // Show call stack
        sessionId: this.sessionId,
        baselineCompleted: this.behavioralData.baselineCompleted,
        isCollectingBaseline: this.behavioralData.isCollectingBaseline,
        backendIntervalId: this.backendIntervalId
      });
      
      // 🎯 SKIP sending during baseline collection - baseline has dedicated endpoint
      if (this.behavioralData.isCollectingBaseline) {
        console.log('⏭️ Skipping regular backend transmission during baseline collection');
        return;
      }
      
      // 🎯 ONLY send regular data after baseline is completed
      if (!this.behavioralData.baselineCompleted) {
        console.log('⏭️ Skipping regular backend transmission - baseline not completed yet');
        return;
      }
      
      // Send full behavioral payload for continuous monitoring (post-baseline)
      console.log('📤 Sending continuous behavioral payload to backend...', {
        sessionId: this.sessionId,
        dataPoints: Object.keys(this.behavioralData).length,
        actionCount: this.behavioralData.actionCount,
        baselineCompleted: this.behavioralData.baselineCompleted,
        isCollectingBaseline: this.behavioralData.isCollectingBaseline
      });
      
      const response = await fetch('http://127.0.0.1:8000/user/behavioral-analysis/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: this.sessionId,
          is_baseline: false, // This is continuous monitoring data
          behavioral_data: {
            ...this.behavioralData,
            timestamp: Date.now(),
            currentPage: this.behavioralData.currentPage || 'unknown',
            // Reference baseline data if available
            baselineData: this.behavioralData.baselineBehaviorData,
            baselineMetrics: this.calculateBaselineMetrics()
          }
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        console.log('📊 Continuous monitoring analysis result:', {
          status: result.user_auth_status,
          authorized: result.is_authorized,
          riskScore: result.risk_score,
          recommendation: result.recommendation
        });
        
        // Store analysis result
        this.behavioralData.lastAnalysisResult = result;
        this.behavioralData.lastAnalysisTime = Date.now();
        
        // 🚨 Handle unauthorized users
        if (!result.is_authorized && result.requires_authentication) {
          console.warn('🚨 UNAUTHORIZED USER DETECTED!');
          console.warn('⚠️ Authentication Required:', result.authentication_message);
          
          // Show authentication needed message
          this.showAuthenticationMessage(result.authentication_message);
          
          // Stop further behavioral tracking for unauthorized users
          this.handleUnauthorizedUser(result);
        }
        
        // Emit custom event for components to react to
        window.dispatchEvent(new CustomEvent('behavioralAnalysis', {
          detail: result
        }));
      } else {
        console.warn('Backend analysis failed:', response.status, response.statusText);
      }
    } catch (error) {
      console.warn('Could not send behavioral data to backend:', error.message);
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
    
    // Clear intervals
    if (this.backendIntervalId) {
      clearInterval(this.backendIntervalId);
      this.backendIntervalId = null;
      console.log('🛑 Cleared backend interval');
    }
    
    localStorage.removeItem(this.STORAGE_KEY);
    localStorage.removeItem(this.SESSION_KEY);
    
    // Reset data
    this.behavioralData = {
      sessionId: null,
      trackingStartTime: null,
      pageLoadTime: null,
      
      // Reset baseline collection state
      isCollectingBaseline: false,
      baselineCollectionStartTime: null,
      baselineCollectionDuration: 20000,
      baselineCompleted: false,
      baselineBehaviorData: null,
      
      cursorMovements: [],
      keyPressTimes: [],
      clickTimestamps: [],
      actionCount: 0,
      // ... reset all arrays and counters
    };
    
    this.isTracking = false;
    console.log('🧹 Behavioral session cleared - stopped all intervals and reset state');
  }
  
  // 🔄 Method to force reset session (for debugging)
  forceResetSession() {
    console.log('🔄 Force resetting behavioral session...');
    this.clearSession();
    this.createNewSession();
    console.log('✅ Session force reset complete');
  }
  
  // Methods for components to update specific behavioral data
  updateBehavioralData(updates) {
    this.behavioralData = { ...this.behavioralData, ...updates };
  }
  
  // 🎯 Baseline Collection System
  startBaselineCollection() {
    console.log('🎯 Starting baseline behavioral data collection...');
    
    this.behavioralData.isCollectingBaseline = true;
    this.behavioralData.baselineCollectionStartTime = Date.now();
    this.behavioralData.baselineCompleted = false;
    
    // Reset baseline data
    this.behavioralData.baselineBehaviorData = {
      cursorMovements: [],
      cursorSpeeds: [],
      keyPressTimes: [],
      clickTimestamps: [],
      scrollSpeeds: [],
      actionCount: 0,
      collectionStartTime: Date.now(),
      collectionEndTime: null
    };
    
    // Show baseline collection UI feedback
    this.showBaselineCollectionMessage();
    
    // Set timeout to complete baseline collection
    setTimeout(() => {
      this.completeBaselineCollection();
    }, this.behavioralData.baselineCollectionDuration);
    
    return this.behavioralData.baselineCollectionDuration;
  }
  
  completeBaselineCollection() {
    if (!this.behavioralData.isCollectingBaseline) return;
    
    console.log('✅ Baseline collection completed (20 seconds)');
    
    this.behavioralData.isCollectingBaseline = false;
    this.behavioralData.baselineCompleted = true;
    this.behavioralData.baselineBehaviorData.collectionEndTime = Date.now();
    
    // Remove baseline collection UI
    this.removeBaselineCollectionMessage();
    
    // Send baseline data to backend first
    this.sendBaselineToBackend().then(() => {
      console.log('📤 Baseline data sent to backend, starting continuous transmission...');
      
      // Start continuous data transmission to backend immediately after baseline is sent
      this.startContinuousTransmission();
      
      // Emit baseline completion event
      window.dispatchEvent(new CustomEvent('baselineCompleted', {
        detail: {
          baselineData: this.behavioralData.baselineBehaviorData,
          sessionId: this.sessionId
        }
      }));
    }).catch((error) => {
      console.error('❌ Failed to send baseline data, but starting continuous transmission anyway:', error);
      
      // Start continuous transmission even if baseline sending failed
      this.startContinuousTransmission();
      
      // Emit baseline completion event
      window.dispatchEvent(new CustomEvent('baselineCompleted', {
        detail: {
          baselineData: this.behavioralData.baselineBehaviorData,
          sessionId: this.sessionId
        }
      }));
    });
  }
  
  // 🎯 GLOBAL BACKGROUND Baseline Collection - Eagle's Eye View
  startBackgroundBaselineCollection() {
    // Only start if not already collecting baseline and not already completed
    if (this.behavioralData.isCollectingBaseline || this.behavioralData.baselineCompleted) {
      console.log('⏭️ Baseline already collecting or completed, skipping background start');
      return;
    }
    
    // 🛡️ PROTECTION: Clear any existing baseline timer
    if (this.baselineTimerId) {
      clearTimeout(this.baselineTimerId);
      this.baselineTimerId = null;
    }
    
    console.log('🦅 Starting GLOBAL baseline collection for 20 seconds...');
    
    // 📊 CRITICAL: Set collection state BEFORE initializing data
    this.behavioralData.isCollectingBaseline = true;
    this.behavioralData.baselineCollectionStartTime = Date.now();
    this.behavioralData.baselineCompleted = false;
    
    // Reset baseline data with comprehensive tracking
    this.behavioralData.baselineBehaviorData = {
      // Mouse behavior across all pages
      cursorMovements: [],
      cursorSpeeds: [],
      cursorPaths: [],
      hoverPatterns: [],
      
      // Keyboard behavior across all pages
      keyPressTimes: [],
      keySequences: [],
      typingRhythm: [],
      
      // Click behavior across all pages
      clickTimestamps: [],
      clickPatterns: [],
      doubleClickIntervals: [],
      
      // Scroll behavior across all pages
      scrollSpeeds: [],
      scrollDirections: [],
      scrollPatterns: [],
      
      // Page navigation behavior
      pageTransitions: [],
      timePerPage: [],
      navigationPatterns: [],
      
      // Global session metrics
      actionCount: 0,
      totalActiveTime: 0,
      idlePeriods: [],
      
      // Collection metadata
      collectionStartTime: Date.now(),
      collectionEndTime: null,
      pagesVisited: [this.behavioralData.currentPage || 'unknown'],
      overallBehaviorProfile: null
    };
    
    // Set baseline as HIGH PRIORITY background task
    console.log('🔕 SILENT baseline collection - NO UI interruption, EAGLE\'S EYE monitoring');
    console.log('� Collecting baseline across ALL pages for 20 seconds...');
    
    // Set 20-second timer for baseline completion
    this.baselineTimerId = setTimeout(() => {
      console.log('⏰ Baseline timer completed - finishing collection...');
      this.completeBackgroundBaselineCollection();
    }, this.behavioralData.baselineCollectionDuration);
    
    // Store timer reference for persistence
    this.behavioralData.baselineTimerId = this.baselineTimerId;
    
    // Save session state
    this.saveSession();
    
    console.log('✅ Baseline collection started - Timer ID:', this.baselineTimerId);
    
    return this.behavioralData.baselineCollectionDuration;
  }
  
  completeBackgroundBaselineCollection() {
    if (!this.behavioralData.isCollectingBaseline) {
      console.log('⚠️ Baseline was not collecting, cannot complete background collection');
      return;
    }
    
    console.log('🦅 Baseline collection completed after 20 seconds');
    
    // Clean up baseline timer
    if (this.baselineTimerId) {
      clearTimeout(this.baselineTimerId);
      this.baselineTimerId = null;
    }
    this.behavioralData.baselineTimerId = null;
    
    this.behavioralData.isCollectingBaseline = false;
    this.behavioralData.baselineCompleted = true;
    this.behavioralData.baselineBehaviorData.collectionEndTime = Date.now();
    
    // Validate and log baseline data quality
    const baselineStats = this.validateBaselineData();
    console.log('📊 Baseline Data Quality:', {
      duration: (this.behavioralData.baselineBehaviorData.collectionEndTime - this.behavioralData.baselineBehaviorData.collectionStartTime) / 1000 + 's',
      mouseMovements: baselineStats.mouseMovements,
      keyPresses: baselineStats.keyPresses,
      clicks: baselineStats.clicks,
      totalActions: baselineStats.totalActions,
      isValid: baselineStats.isValid
    });
    
    if (!baselineStats.isValid) {
      console.warn('⚠️ WARNING: Baseline data quality is insufficient but proceeding with transmission');
    }
    
    // Calculate comprehensive baseline profile
    this.behavioralData.baselineBehaviorData.overallBehaviorProfile = this.generateComprehensiveBaselineProfile();
    
    console.log('📤 Sending baseline data to backend...');
    
    // Send baseline data to backend first
    this.sendBaselineToBackend().then((result) => {
      console.log('✅ Baseline data successfully transmitted to backend');
      console.log('✅ Backend Response:', {
        baseline_id: result.baseline_id,
        user_id: result.user_id,
        quality_score: result.data_quality_score
      });
      
      // Start continuous data transmission
      this.startContinuousTransmission();
      
      // Emit baseline completion event
      window.dispatchEvent(new CustomEvent('backgroundBaselineCompleted', {
        detail: {
          baselineData: this.behavioralData.baselineBehaviorData,
          sessionId: this.sessionId,
          profileType: 'comprehensive_eagle_eye',
          backendResult: result
        }
      }));
    }).catch((error) => {
      console.error('❌ Baseline data transmission failed:', error);
      
      // Start continuous transmission anyway
      this.startContinuousTransmission();
      
      // Emit baseline completion event
      window.dispatchEvent(new CustomEvent('backgroundBaselineCompleted', {
        detail: {
          baselineData: this.behavioralData.baselineBehaviorData,
          sessionId: this.sessionId,
          error: error.message
        }
      }));
    });
  }

  // 📊 Validate baseline data quality
  validateBaselineData() {
    if (!this.behavioralData.baselineBehaviorData) {
      return {
        mouseMovements: 0,
        keyPresses: 0,
        clicks: 0,
        scrollEvents: 0,
        totalActions: 0,
        isValid: false,
        reason: 'No baseline data exists'
      };
    }
    
    const baseline = this.behavioralData.baselineBehaviorData;
    const stats = {
      mouseMovements: baseline.cursorMovements?.length || 0,
      keyPresses: baseline.keyPressTimes?.length || 0,
      clicks: baseline.clickTimestamps?.length || 0,
      scrollEvents: baseline.scrollSpeeds?.length || 0,
      totalActions: 0,
      isValid: false,
      reason: ''
    };
    
    stats.totalActions = stats.mouseMovements + stats.keyPresses + stats.clicks + stats.scrollEvents;
    
    // Validation criteria
    const minMouseMovements = 10;  // Minimum mouse movements
    const minTotalActions = 15;    // Minimum total interactions
    
    if (stats.mouseMovements < minMouseMovements) {
      stats.reason = `Insufficient mouse movements (${stats.mouseMovements} < ${minMouseMovements})`;
    } else if (stats.totalActions < minTotalActions) {
      stats.reason = `Insufficient total actions (${stats.totalActions} < ${minTotalActions})`;
    } else {
      stats.isValid = true;
      stats.reason = 'Data quality is sufficient';
    }
    
    return stats;
  }

  // 🦅 Generate comprehensive baseline profile - Eagle's Eye Analysis
  generateComprehensiveBaselineProfile() {
    if (!this.behavioralData.baselineBehaviorData) return null;
    
    const baseline = this.behavioralData.baselineBehaviorData;
    const totalDuration = baseline.collectionEndTime - baseline.collectionStartTime;
    
    console.log('🦅 Generating comprehensive eagle\'s eye baseline profile...');
    
    return {
      // Mouse behavior profile
      mouseProfile: {
        totalMovements: baseline.cursorMovements.length,
        avgSpeed: baseline.cursorSpeeds.length > 0 ? 
          baseline.cursorSpeeds.reduce((a, b) => a + b, 0) / baseline.cursorSpeeds.length : 0,
        speedVariance: this.calculateVariance(baseline.cursorSpeeds),
        movementEntropy: this.calculatePathEntropy(baseline.cursorMovements),
        hoverPatterns: baseline.hoverPatterns.length
      },
      
      // Keyboard behavior profile
      keyboardProfile: {
        totalKeyPresses: baseline.keyPressTimes.length,
        typingRhythm: this.calculateTypingRhythm(baseline.keyPressTimes),
        keySequencePatterns: baseline.keySequences.length,
        avgKeyInterval: this.calculateAvgKeyInterval(baseline.keyPressTimes)
      },
      
      // Click behavior profile
      clickProfile: {
        totalClicks: baseline.clickTimestamps.length,
        clickFrequency: baseline.clickTimestamps.length / (totalDuration / 1000),
        doubleClickPatterns: baseline.doubleClickIntervals.length,
        clickRhythm: this.calculateClickRhythm(baseline.clickTimestamps)
      },
      
      // Scroll behavior profile
      scrollProfile: {
        totalScrolls: baseline.scrollSpeeds.length,
        avgScrollSpeed: baseline.scrollSpeeds.length > 0 ?
          baseline.scrollSpeeds.reduce((a, b) => a + b, 0) / baseline.scrollSpeeds.length : 0,
        scrollPatterns: baseline.scrollPatterns.length,
        scrollVariance: this.calculateVariance(baseline.scrollSpeeds)
      },
      
      // Navigation behavior profile
      navigationProfile: {
        pagesVisited: baseline.pagesVisited.length,
        pageTransitions: baseline.pageTransitions.length,
        avgTimePerPage: baseline.timePerPage.length > 0 ?
          baseline.timePerPage.reduce((a, b) => a + b, 0) / baseline.timePerPage.length : 0,
        navigationPatterns: baseline.navigationPatterns.length
      },
      
      // Overall activity profile
      activityProfile: {
        totalActions: baseline.actionCount,
        actionsPerSecond: baseline.actionCount / (totalDuration / 1000),
        activeTime: baseline.totalActiveTime,
        idlePeriods: baseline.idlePeriods.length,
        overallActivityLevel: this.calculateActivityLevel(baseline)
      },
      
      // Meta information
      collectionMeta: {
        duration: totalDuration,
        startTime: baseline.collectionStartTime,
        endTime: baseline.collectionEndTime,
        profileType: 'comprehensive_eagle_eye',
        dataQualityScore: this.calculateDataQualityScore(baseline)
      }
    };
  }
  
  showBaselineCollectionMessage() {
    // Remove any existing message
    this.removeBaselineCollectionMessage();
    
    const baselineMessage = document.createElement('div');
    baselineMessage.id = 'baseline-collection-message';
    baselineMessage.style.cssText = `
      position: fixed;
      top: 20px;
      left: 50%;
      transform: translateX(-50%);
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 15px 25px;
      border-radius: 25px;
      font-size: 16px;
      font-weight: 500;
      z-index: 10000;
      box-shadow: 0 4px 20px rgba(0,0,0,0.15);
      text-align: center;
      animation: slideDown 0.3s ease-out;
    `;
    
    baselineMessage.innerHTML = `
      <div style="display: flex; align-items: center; gap: 10px;">
        <div style="
          width: 20px;
          height: 20px;
          border: 2px solid #ffffff40;
          border-top: 2px solid white;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        "></div>
        <span>Collecting baseline behavior... Please interact normally (${this.behavioralData.baselineCollectionDuration/1000}s)</span>
      </div>
    `;
    
    // Add CSS animations
    const style = document.createElement('style');
    style.textContent = `
      @keyframes slideDown {
        from { transform: translateX(-50%) translateY(-20px); opacity: 0; }
        to { transform: translateX(-50%) translateY(0); opacity: 1; }
      }
      @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }
    `;
    document.head.appendChild(style);
    
    document.body.appendChild(baselineMessage);
  }
  
  removeBaselineCollectionMessage() {
    const existingMessage = document.getElementById('baseline-collection-message');
    if (existingMessage) {
      existingMessage.remove();
    }
  }
  
  // 📤 Send baseline data to backend
  async sendBaselineToBackend() {
    if (!this.behavioralData.baselineBehaviorData) {
      console.warn('⚠️ No baseline data to send');
      return;
    }
    
    try {
      console.log('📤 Sending baseline data to backend...');
      
      const baselineMetrics = this.calculateBaselineMetrics();
      
      const payload = {
        session_id: this.sessionId,
        is_baseline: true,
        baseline_data: {
          ...this.behavioralData.baselineBehaviorData,
          metrics: baselineMetrics,
          sessionId: this.sessionId,
          timestamp: Date.now(),
          currentPage: this.behavioralData.currentPage || 'unknown'
        }
      };
      
      const response = await fetch('http://127.0.0.1:8000/user/behavioral-analysis/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
      });
      
      if (response.ok) {
        const result = await response.json();
        console.log('✅ Baseline data sent successfully:', {
          baseline_id: result.baseline_id,
          user_id: result.user_id,
          quality_score: result.data_quality_score
        });
        
        // Store baseline analysis result
        this.behavioralData.baselineAnalysisResult = result;
        this.behavioralData.baselineAnalysisTime = Date.now();
        
        return result;
      } else {
        console.error('❌ Failed to send baseline data:', response.status, response.statusText);
        
        // Try to get error response body
        try {
          const errorBody = await response.text();
          console.error('❌ Error details:', errorBody);
        } catch (e) {
          console.error('❌ Could not read error response');
        }
        
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
    } catch (error) {
      console.error('❌ Error sending baseline data:', error.message);
      throw error;
    }
  }
  
  startContinuousTransmission() {
    console.log('🔄 Starting continuous behavioral data transmission to backend...');
    
    // Clear any existing interval
    if (this.backendIntervalId) {
      clearInterval(this.backendIntervalId);
    }
    
    // Send first batch immediately to avoid gap
    console.log('📤 Sending immediate post-baseline data...');
    this.sendToBackend();
    
    // Start sending data every 1 second with no gaps
    this.backendIntervalId = setInterval(() => {
      this.sendToBackend();
    }, this.backendInterval);
    
    console.log('✅ Continuous transmission started (every 1 second, no gaps)');
  }
  
  stopContinuousTransmission() {
    if (this.backendIntervalId) {
      clearInterval(this.backendIntervalId);
      this.backendIntervalId = null;
      console.log('⏹️ Continuous transmission stopped');
    }
  }
  
  // Track events from components
  trackEvent(eventType, eventData) {
    const timestamp = Date.now();
    
    // 🛡️ Ensure all essential arrays are initialized (defensive programming)
    this.ensureArraysInitialized();
    
    // If collecting baseline, also store in baseline data
    if (this.behavioralData.isCollectingBaseline && this.behavioralData.baselineBehaviorData) {
      this.recordBaselineEvent(eventType, eventData, timestamp);
    }
    
    switch (eventType) {
      case 'mouseMove':
        if (eventData.clientX !== undefined && eventData.clientY !== undefined) {
          const movement = {
            x: eventData.clientX,
            y: eventData.clientY,
            timestamp: timestamp
          };
          
          this.behavioralData.cursorMovements.push(movement);
          this.behavioralData.lastMouseMove = timestamp;
          
          // Calculate speed if we have previous movement
          if (this.behavioralData.cursorMovements.length > 1) {
            const prev = this.behavioralData.cursorMovements[this.behavioralData.cursorMovements.length - 2];
            const distance = Math.sqrt(
              Math.pow(movement.x - prev.x, 2) + Math.pow(movement.y - prev.y, 2)
            );
            const timeDiff = (timestamp - prev.timestamp) / 1000; // Convert to seconds
            const speed = timeDiff > 0 ? distance / timeDiff : 0;
            
            this.behavioralData.cursorSpeeds.push(speed);
            this.behavioralData.latestSpeed = speed;
            this.behavioralData.allSpeeds.push(speed);
          }
        }
        break;
        
      case 'keyPress':
        this.behavioralData.keyPressTimes.push(timestamp);
        this.behavioralData.lastKeyPress = timestamp;
        if (eventData.key === 'Tab') {
          this.behavioralData.TabKeyCount++;
        }
        break;
        
      case 'click':
        this.behavioralData.clickTimestamps.push(timestamp);
        this.behavioralData.clickTimes.push(timestamp);
        this.behavioralData.lastClickTime = timestamp;
        break;
        
      case 'scroll':
        this.behavioralData.scrollChanges++;
        this.behavioralData.lastScroll = timestamp;
        this.behavioralData.lastScrollTime = timestamp;
        
        if (eventData.deltaY !== undefined) {
          const speed = Math.abs(eventData.deltaY);
          this.behavioralData.scrollSpeeds.push(speed);
        }
        break;
        
      case 'paste':
        this.behavioralData.pasteDetected = true;
        this.behavioralData.pasteTimestamp = timestamp;
        
        // Reset post-paste activity tracking
        this.behavioralData.postPasteActivity = {
          keyPresses: 0,
          mouseMoves: 0,
          clicks: 0,
          timeToFirstAction: null,
          timeToLastAction: null,
          actionsAfterPaste: [],
          clipboardContent: null,
        };
        break;
        
      case 'input':
        // Track input field interactions
        this.behavioralData.lastActionTime = timestamp;
        this.behavioralData.actionCount++;
        break;
        
      case 'buttonClick':
        this.behavioralData.clickTimestamps.push(timestamp);
        this.behavioralData.lastActionTime = timestamp;
        this.behavioralData.actionCount++;
        break;
        
      default:
        console.warn('Unknown event type:', eventType);
    }
    
    // Update last action time for all events
    this.behavioralData.lastActionTime = timestamp;
    this.behavioralData.actionCount++;
    
    // Save to storage periodically
    if (timestamp - this.lastSaveTime > this.saveInterval) {
      this.saveToStorage();
      this.lastSaveTime = timestamp;
    }
  }
  
  // 🦅 Record events during baseline collection - Eagle's Eye Comprehensive Tracking
  recordBaselineEvent(eventType, eventData, timestamp) {
    // Check if baseline collection is active
    if (!this.behavioralData.isCollectingBaseline) {
      return; // Silently return if not collecting baseline
    }
    
    if (!this.behavioralData.baselineBehaviorData) {
      console.error('🚨 BASELINE ERROR: baselineBehaviorData is null but isCollectingBaseline is true');
      return;
    }
    
    // Log baseline recording status every 5 seconds
    if (!this.lastBaselineLogTime || Date.now() - this.lastBaselineLogTime > 5000) {
      const baseline = this.behavioralData.baselineBehaviorData;
      const timeRemaining = Math.max(0, (this.behavioralData.baselineCollectionStartTime + this.behavioralData.baselineCollectionDuration - Date.now()) / 1000);
      console.log(`🦅 Baseline recording: Mouse:${baseline.cursorMovements?.length || 0}, Keys:${baseline.keyPressTimes?.length || 0}, Clicks:${baseline.clickTimestamps?.length || 0} | ${timeRemaining.toFixed(1)}s remaining`);
      this.lastBaselineLogTime = Date.now();
    }
    
    const baseline = this.behavioralData.baselineBehaviorData;
    const currentPage = this.behavioralData.currentPage || 'unknown';
    
    switch (eventType) {
      case 'mouseMove':
        if (eventData.clientX !== undefined && eventData.clientY !== undefined) {
          const movement = {
            x: eventData.clientX,
            y: eventData.clientY,
            timestamp: timestamp,
            page: currentPage
          };
          
          baseline.cursorMovements.push(movement);
          
          // 🦅 Track cursor path for eagle's eye analysis
          if (baseline.cursorMovements.length > 1) {
            const prev = baseline.cursorMovements[baseline.cursorMovements.length - 2];
            const distance = Math.sqrt(
              Math.pow(movement.x - prev.x, 2) + Math.pow(movement.y - prev.y, 2)
            );
            const timeDiff = (timestamp - prev.timestamp) / 1000;
            const speed = timeDiff > 0 ? distance / timeDiff : 0;
            
            baseline.cursorSpeeds.push(speed);
            
            // Track path segments for pattern analysis
            baseline.cursorPaths.push({
              from: { x: prev.x, y: prev.y },
              to: { x: movement.x, y: movement.y },
              distance: distance,
              speed: speed,
              page: currentPage,
              timestamp: timestamp
            });
          }
          
          // Track hover patterns
          if (baseline.cursorMovements.length > 0) {
            const lastMove = baseline.cursorMovements[baseline.cursorMovements.length - 2];
            if (lastMove && (timestamp - lastMove.timestamp) > 500) {
              baseline.hoverPatterns.push({
                x: movement.x,
                y: movement.y,
                duration: timestamp - lastMove.timestamp,
                page: currentPage
              });
            }
          }
        }
        break;
        
      case 'keyPress':
        baseline.keyPressTimes.push(timestamp);
        
        // 🦅 Track typing rhythm and sequences
        if (baseline.keyPressTimes.length > 1) {
          const prev = baseline.keyPressTimes[baseline.keyPressTimes.length - 2];
          const interval = timestamp - prev;
          baseline.typingRhythm.push(interval);
        }
        
        // Track key sequences for pattern analysis
        baseline.keySequences.push({
          key: eventData.key || 'unknown',
          timestamp: timestamp,
          page: currentPage
        });
        break;
        
      case 'click':
      case 'buttonClick':
        baseline.clickTimestamps.push(timestamp);
        
        // 🦅 Track click patterns and double-clicks
        if (baseline.clickTimestamps.length > 1) {
          const prev = baseline.clickTimestamps[baseline.clickTimestamps.length - 2];
          const interval = timestamp - prev;
          
          if (interval < 500) { // Double-click detection
            baseline.doubleClickIntervals.push(interval);
          }
          
          baseline.clickPatterns.push({
            interval: interval,
            page: currentPage,
            timestamp: timestamp
          });
        }
        break;
        
      case 'scroll':
        const scrollSpeed = eventData.deltaY ? Math.abs(eventData.deltaY) : 0;
        baseline.scrollSpeeds.push(scrollSpeed);
        
        // 🦅 Track scroll directions and patterns
        baseline.scrollDirections.push({
          direction: eventData.deltaY > 0 ? 'down' : 'up',
          speed: scrollSpeed,
          page: currentPage,
          timestamp: timestamp
        });
        
        baseline.scrollPatterns.push({
          deltaX: eventData.deltaX || 0,
          deltaY: eventData.deltaY || 0,
          page: currentPage,
          timestamp: timestamp
        });
        break;
    }
    
    // 🦅 Track page transitions during baseline
    if (currentPage && !baseline.pagesVisited.includes(currentPage)) {
      baseline.pagesVisited.push(currentPage);
      
      if (baseline.pagesVisited.length > 1) {
        baseline.pageTransitions.push({
          from: baseline.pagesVisited[baseline.pagesVisited.length - 2],
          to: currentPage,
          timestamp: timestamp
        });
      }
    }
    
    // 🦅 Update activity metrics
    baseline.actionCount++;
    baseline.totalActiveTime = timestamp - baseline.collectionStartTime;
    
    // Track idle periods (gaps > 2 seconds)
    if (baseline.actionCount > 1) {
      const timeSinceLastAction = timestamp - (baseline.lastActionTimestamp || baseline.collectionStartTime);
      if (timeSinceLastAction > 2000) {
        baseline.idlePeriods.push({
          duration: timeSinceLastAction,
          startTime: baseline.lastActionTimestamp,
          endTime: timestamp,
          page: currentPage
        });
      }
    }
    
    baseline.lastActionTimestamp = timestamp;
  }
  
  // 🦅 Helper methods for comprehensive baseline analysis
  calculateVariance(values) {
    if (values.length === 0) return 0;
    const mean = values.reduce((a, b) => a + b, 0) / values.length;
    const variance = values.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / values.length;
    return variance;
  }
  
  calculatePathEntropy(movements) {
    if (movements.length < 2) return 0;
    // Simple entropy calculation based on direction changes
    let directionChanges = 0;
    for (let i = 2; i < movements.length; i++) {
      const prev = movements[i-2];
      const curr = movements[i-1];
      const next = movements[i];
      
      const angle1 = Math.atan2(curr.y - prev.y, curr.x - prev.x);
      const angle2 = Math.atan2(next.y - curr.y, next.x - curr.x);
      const angleDiff = Math.abs(angle2 - angle1);
      
      if (angleDiff > Math.PI / 4) directionChanges++; // 45-degree threshold
    }
    return directionChanges / (movements.length - 2);
  }
  
  calculateTypingRhythm(keyPressTimes) {
    if (keyPressTimes.length < 2) return 0;
    const intervals = [];
    for (let i = 1; i < keyPressTimes.length; i++) {
      intervals.push(keyPressTimes[i] - keyPressTimes[i-1]);
    }
    return this.calculateVariance(intervals);
  }
  
  calculateAvgKeyInterval(keyPressTimes) {
    if (keyPressTimes.length < 2) return 0;
    const totalInterval = keyPressTimes[keyPressTimes.length - 1] - keyPressTimes[0];
    return totalInterval / (keyPressTimes.length - 1);
  }
  
  calculateClickRhythm(clickTimestamps) {
    if (clickTimestamps.length < 2) return 0;
    const intervals = [];
    for (let i = 1; i < clickTimestamps.length; i++) {
      intervals.push(clickTimestamps[i] - clickTimestamps[i-1]);
    }
    return this.calculateVariance(intervals);
  }
  
  calculateActivityLevel(baseline) {
    const duration = baseline.collectionEndTime - baseline.collectionStartTime;
    const actionsPerSecond = baseline.actionCount / (duration / 1000);
    
    // Activity level based on actions per second
    if (actionsPerSecond > 5) return 'high';
    if (actionsPerSecond > 2) return 'medium';
    if (actionsPerSecond > 0.5) return 'low';
    return 'very_low';
  }
  
  calculateDataQualityScore(baseline) {
    let score = 0;
    const maxScore = 100;
    
    // Mouse data quality (25 points)
    if (baseline.cursorMovements.length > 10) score += 25;
    else score += (baseline.cursorMovements.length / 10) * 25;
    
    // Keyboard data quality (25 points)
    if (baseline.keyPressTimes.length > 5) score += 25;
    else score += (baseline.keyPressTimes.length / 5) * 25;
    
    // Click data quality (25 points)
    if (baseline.clickTimestamps.length > 2) score += 25;
    else score += (baseline.clickTimestamps.length / 2) * 25;
    
    // Overall activity quality (25 points)
    const activityScore = Math.min(baseline.actionCount / 20, 1) * 25;
    score += activityScore;
    
    return Math.round(score);
  }
  
  // Calculate baseline metrics for comparison
  calculateBaselineMetrics() {
    if (!this.behavioralData.baselineBehaviorData) return null;
    
    const baseline = this.behavioralData.baselineBehaviorData;
    
    const metrics = {
      collectionDuration: baseline.collectionEndTime - baseline.collectionStartTime,
      averageMouseSpeed: baseline.cursorSpeeds.length > 0 ? 
        baseline.cursorSpeeds.reduce((a, b) => a + b, 0) / baseline.cursorSpeeds.length : 0,
      mouseMovementCount: baseline.cursorMovements.length,
      keyPressCount: baseline.keyPressTimes.length,
      clickCount: baseline.clickTimestamps.length,
      scrollCount: baseline.scrollSpeeds.length,
      actionsPerSecond: baseline.actionCount / ((baseline.collectionEndTime - baseline.collectionStartTime) / 1000),
      mouseMovementFrequency: baseline.cursorMovements.length / ((baseline.collectionEndTime - baseline.collectionStartTime) / 1000),
      keyPressFrequency: baseline.keyPressTimes.length / ((baseline.collectionEndTime - baseline.collectionStartTime) / 1000)
    };
    
    console.log('📊 Baseline metrics calculated:', metrics);
    return metrics;
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
  
  // 🚨 Handle unauthorized user detection
  showAuthenticationMessage(message = 'Need for Authentication') {
    // Create or update authentication modal/alert
    this.removeExistingAuthModal();
    
    const authModal = document.createElement('div');
    authModal.id = 'auth-required-modal';
    authModal.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.8);
      z-index: 10000;
      display: flex;
      align-items: center;
      justify-content: center;
      font-family: Arial, sans-serif;
    `;
    
    authModal.innerHTML = `
      <div style="
        background: white;
        padding: 30px;
        border-radius: 12px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        text-align: center;
        max-width: 400px;
        width: 90%;
      ">
        <div style="
          color: #e74c3c;
          font-size: 48px;
          margin-bottom: 20px;
        ">🚨</div>
        <h2 style="
          color: #2c3e50;
          margin: 0 0 15px 0;
          font-size: 24px;
        ">${message}</h2>
        <p style="
          color: #7f8c8d;
          margin: 0 0 25px 0;
          line-height: 1.5;
        ">Suspicious behavior detected. Please verify your identity to continue.</p>
        <button onclick="this.parentElement.parentElement.remove()" style="
          background: #e74c3c;
          color: white;
          border: none;
          padding: 12px 24px;
          border-radius: 6px;
          font-size: 16px;
          cursor: pointer;
          transition: background 0.3s;
        " onmouseover="this.style.background='#c0392b'" onmouseout="this.style.background='#e74c3c'">
          Acknowledge
        </button>
      </div>
    `;
    
    document.body.appendChild(authModal);
    console.log('🚨 Authentication modal displayed:', message);
  }
  
  removeExistingAuthModal() {
    const existingModal = document.getElementById('auth-required-modal');
    if (existingModal) {
      existingModal.remove();
    }
  }
  
  handleUnauthorizedUser(analysisResult) {
    // Log unauthorized user details
    console.warn('🔒 Unauthorized user session details:', {
      sessionId: this.sessionId,
      riskScore: analysisResult.risk_score,
      suspiciousIndicators: analysisResult.suspicious_indicators,
      recommendation: analysisResult.recommendation
    });
    
    // Mark session as unauthorized
    this.behavioralData.userAuthStatus = 'Unauthorized_user';
    this.behavioralData.requiresAuthentication = true;
    this.behavioralData.unauthorizedTime = Date.now();
    
    // Emit unauthorized user event
    window.dispatchEvent(new CustomEvent('unauthorizedUser', {
      detail: {
        sessionId: this.sessionId,
        analysisResult,
        message: 'Need for Authentication'
      }
    }));
    
    // Save unauthorized status
    this.saveToStorage();
  }
}

// Create global instance
const globalBehavioralTracker = new GlobalBehavioralTracker();

export default globalBehavioralTracker;

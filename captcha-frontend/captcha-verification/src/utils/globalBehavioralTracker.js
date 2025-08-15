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
      baselineCollectionDuration: 45000, // 45 seconds baseline collection
      baselineCompleted: false,
      continuousTransmissionStarted: false, // 🚨 PREVENT DOUBLE TRANSMISSION START
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
    this.SESSION_KEY = 'session_id';

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.init());
    } else {
      // DOM is already ready
      setTimeout(() => this.init(), 0);
    }
  }

  init() {
    if (this.isInitialized) return;

    // 🚀 ALWAYS START WITH COMPLETELY FRESH SESSION
    console.log('🆕 Initializing GlobalBehavioralTracker with fresh session...');

    // Clear any existing session data
    localStorage.removeItem('behavioral_session_id');
    localStorage.removeItem('behavioral_data');

    // Force create new session (bypassing loadSession)
    this.createNewSession();

    // 🔍 COLLECT DEVICE FINGERPRINT AND EVASION SIGNALS
    this.collectDeviceFingerprint();

    // Start global tracking
    this.startGlobalTracking();

    // Set up periodic saving
    this.setupPeriodicSaving();

    // Set up page unload handler
    this.setupUnloadHandler();

    // � Set up navigation detection for URL changes
    this.setupNavigationDetection();

    // �🎯 START BASELINE COLLECTION IMMEDIATELY IN BACKGROUND
    // 🛑 COMMENTED OUT TO PREVENT DUPLICATE BASELINE COLLECTION
    // this.startBackgroundBaselineCollection();

    // 📊🎯 START IMMEDIATE BASELINE COLLECTION FROM URL ENTRY
    this.startImmediateBaselineCollection();

    this.isInitialized = true;
  }

  loadSession() {
    try {
      // 🔄 ALWAYS START FRESH SESSION ON WEBSITE LOAD
      console.log('🔄 Starting fresh behavioral session on website load...');

      // Clear any existing session data to ensure clean start
      localStorage.removeItem(this.SESSION_KEY);
      localStorage.removeItem(this.STORAGE_KEY);

      // Force creation of new session
      this.createNewSession();

      console.log('✅ Fresh behavioral session created:', this.sessionId);

    } catch (error) {
      console.error('Error creating fresh session:', error);
      this.createNewSession();
    }
  }

  createNewSession() {
    // Generate completely new session ID
    this.sessionId = this.generateSessionId();
    this.trackingStartTime = Date.now();

    // 🔄 COMPLETELY RESET ALL BEHAVIORAL DATA
    this.behavioralData = {
      sessionId: this.sessionId,
      trackingStartTime: this.trackingStartTime,
      pageLoadTime: Date.now(),

      // Reset baseline collection state
      isCollectingBaseline: false,
      baselineCollectionStartTime: null,
      baselineCollectionDuration: 20000,
      baselineCompleted: false,
      continuousTransmissionStarted: false,
      baselineBehaviorData: null,
      baselineTimerId: null,

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

    // Clear any existing timers
    if (this.baselineTimerId) {
      clearTimeout(this.baselineTimerId);
      this.baselineTimerId = null;
    }

    if (this.backendIntervalId) {
      clearInterval(this.backendIntervalId);
      this.backendIntervalId = null;
    }

    // Save new session to localStorage
    localStorage.setItem(this.SESSION_KEY, this.sessionId);
    this.saveToStorage();

    console.log('🔄 Complete fresh behavioral session created:', this.sessionId);
    console.log('🧹 All behavioral data has been reset for new session');
  }

  // 🔧 DEBUG: Force generate new session ID (clears old format)
  debugForceNewSession() {
    console.warn('🔧 DEBUG: Forcing new session generation...');
    localStorage.removeItem(this.SESSION_KEY);
    localStorage.removeItem(this.STORAGE_KEY);
    this.createNewSession();
    console.log('🔧 New session ID generated:', this.sessionId);
    return this.sessionId;
  }

  // Save session data to localStorage
  saveSession() {
    this.saveToStorage();
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
    this.behavioralData.continuousTransmissionStarted = false; // 🚨 RESET TRANSMISSION FLAG
    this.behavioralData.isCollectingBaseline = false;
    this.behavioralData.baselineCollectionStartTime = null;
    this.behavioralData.baselineTimerId = null;
    this.behavioralData.baselineBehaviorData = null;

    this.saveSession();
    return this;
  }



  // 🔧 DEBUG: Check current baseline state
  debugBaselineState() {
    const data = this.behavioralData;
    console.log('🔧 BASELINE STATE:', {
      collecting: data.isCollectingBaseline,
      completed: data.baselineCompleted,
      startTime: data.baselineCollectionStartTime,
      hasData: !!data.baselineBehaviorData,
      timerId: this.baselineTimerId,
      sessionId: this.sessionId
    });

    // Check localStorage state
    const storedData = localStorage.getItem(this.STORAGE_KEY);
    if (storedData) {
      const parsed = JSON.parse(storedData);
      console.log('🔧 STORED STATE:', {
        collecting: parsed.isCollectingBaseline,
        completed: parsed.baselineCompleted,
        startTime: parsed.baselineCollectionStartTime
      });
    }

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

  // 🔧 DEBUG: Test payload format without full baseline collection
  debugTestPayloadFormat() {
    console.warn('🔧 DEBUG: Testing baseline payload format...');

    // Create minimal test baseline data
    const testBaselineData = {
      collectionStartTime: Date.now() - 20000,
      collectionEndTime: Date.now(),
      cursorMovements: [
        { x: 100, y: 150, timestamp: Date.now() - 19000 },
        { x: 120, y: 160, timestamp: Date.now() - 18000 }
      ],
      keyPressTimes: [Date.now() - 17000, Date.now() - 16000],
      clickTimestamps: [Date.now() - 15000],
      scrollSpeeds: [10, 15],
      actionCount: 5
    };

    const payload = {
      session_id: this.sessionId,
      baseline_data: {
        ...testBaselineData,
        metrics: { avgSpeed: 25.5, totalActions: 5 },
        sessionId: this.sessionId,
        timestamp: Date.now(),
        currentPage: 'test-page'
      }
    };

    console.log('🔧 Test payload format:', JSON.stringify(payload, null, 2));
    return payload;
  }

  // 🔧 DEBUG: Force immediate baseline transmission (for testing)
  debugSendTestBaseline() {
    console.warn('🔧 DEBUG: Sending test baseline to backend...');

    // Create test baseline data
    const testPayload = this.debugTestPayloadFormat();

    // Send to backend
    return fetch('http://127.0.0.1:8000/user/baseline-storage/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(testPayload)
    }).then(response => {
      console.log('🔧 Test baseline response status:', response.status);
      return response.json();
    }).then(result => {
      console.log('🔧 Test baseline result:', result);
      return result;
    }).catch(error => {
      console.error('🔧 Test baseline error:', error);
      throw error;
    });
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


    const timestamp = Date.now().toString(36); // Base36 timestamp

    // Generate cryptographically secure random string
    const array = new Uint8Array(16);
    if (window.crypto && window.crypto.getRandomValues) {
      window.crypto.getRandomValues(array);
    } else {
      // Fallback for older browsers
      for (let i = 0; i < array.length; i++) {
        array[i] = Math.floor(Math.random() * 256);
      }
    }

    const randomString = Array.from(array, byte => byte.toString(36).padStart(2, '0')).join('').substring(0, 12);

    // Browser fingerprint component
    const userAgent = navigator.userAgent || '';
    const screen = `${window.screen.width}x${window.screen.height}`;
    const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    const language = navigator.language || 'en';

    // Create a simple hash of browser characteristics
    const browserData = `${userAgent}${screen}${timezone}${language}`;
    let fingerprint = 0;
    for (let i = 0; i < browserData.length; i++) {
      fingerprint = ((fingerprint << 5) - fingerprint + browserData.charCodeAt(i)) & 0xffffffff;
    }
    const fingerprintHex = Math.abs(fingerprint).toString(36).substring(0, 8);

    // Additional entropy from performance and timing
    const performanceNow = performance.now().toString().replace('.', '');
    const entropy = performanceNow.substring(-6) + Math.random().toString(36).substring(2, 8);

    // Combine components: timestamp-random-fingerprint-entropy
    return `${timestamp}-${randomString}-${fingerprintHex}-${entropy}`;
  }

  startGlobalTracking() {
    if (this.isTracking) return;

    this.isTracking = true;

    // Mouse movement tracking
    const handleMouseMove = (event) => {
      this.trackMouseMovement(event);
    };

    const handleKeyDown = (event) => {
      this.keydown(event);
    };

    const handleKeyUp = (event) => {
      this.keyup(event);
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

  // 🛑 STOP TRACKING: Remove all event listeners and clear intervals
  stopTracking() {
    if (!this.isTracking) return;

    console.log('🛑 Stopping behavioral tracking...');

    // Remove all event listeners
    this.eventListeners.forEach(({ element, event, handler }) => {
      try {
        element.removeEventListener(event, handler);
      } catch (error) {
        console.warn('Warning removing event listener:', error);
      }
    });

    // Clear event listeners array
    this.eventListeners = [];

    // Clear intervals
    if (this.urlCheckInterval) {
      clearInterval(this.urlCheckInterval);
      this.urlCheckInterval = null;
    }

    if (this.saveIntervalId) {
      clearInterval(this.saveIntervalId);
      this.saveIntervalId = null;
    }

    // Mark as not tracking
    this.isTracking = false;

    console.log('✅ Behavioral tracking stopped');
  }

  addEventListener(element, event, handler) {
    element.addEventListener(event, handler);
    this.eventListeners.push({ element, event, handler });
  }

  // 🔍 COMPREHENSIVE DEVICE FINGERPRINTING FOR ALL DJANGO FIELDS
  collectDeviceFingerprint() {
    try {
      // 📱 Basic device fingerprint
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      ctx.textBaseline = 'top';
      ctx.font = '14px Arial';
      ctx.fillText('Device fingerprint test 🎯', 2, 2);
      const canvasFingerprint = canvas.toDataURL();

      // 🎯 DEVICE FINGERPRINT STRING
      this.behavioralData.deviceFingerprint = this.createHashFromString(
        navigator.userAgent + window.screen.width + window.screen.height + canvasFingerprint
      );

      // 🖼️ CANVAS METRICS
      this.behavioralData.canvasMetrics = {
        winding: ctx.isPointInPath ? 'supported' : 'not_supported',
        geometryLength: canvasFingerprint.length,
        textLength: navigator.userAgent.length,
        canvasFingerprint: canvasFingerprint.substring(0, 100) // First 100 chars
      };

      // 🎨 GPU INFO
      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      if (gl) {
        const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
        this.behavioralData.gpuInfo = {
          gpu_name: debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : 'unknown',
          vendor: debugInfo ? gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) : 'unknown',
          renderer: gl.getParameter(gl.RENDERER),
          webgl_info: gl.getParameter(gl.VERSION),
          capabilities: {
            maxTextureSize: gl.getParameter(gl.MAX_TEXTURE_SIZE),
            maxViewportDims: gl.getParameter(gl.MAX_VIEWPORT_DIMS)
          },
          extensions: gl.getSupportedExtensions() || [],
          driver_info: navigator.userAgent,
          graphics_api: 'WebGL'
        };
      } else {
        this.behavioralData.missingCanvasFingerprint = true;
        this.behavioralData.gpuInfo = {
          gpu_name: 'webgl_not_supported',
          vendor: 'unknown',
          renderer: 'unknown',
          webgl_info: 'not_available',
          capabilities: null,
          extensions: [],
          driver_info: navigator.userAgent,
          graphics_api: 'none'
        };
      }

      // 📺 SCREEN RESOLUTION ANALYSIS
      const screenInfo = {
        width_height: `${window.screen.width}x${window.screen.height}`,
        inner_width: window.innerWidth,
        device_pixel_ratio: window.devicePixelRatio || 1,
        aspect_ratio: (window.screen.width / window.screen.height).toFixed(2)
      };

      // Detect unusual screen resolutions (common bot resolutions)
      const commonResolutions = ['1920x1080', '1366x768', '1536x864', '1440x900', '1280x720'];
      const isUnusual = !commonResolutions.includes(screenInfo.width_height);

      this.behavioralData.unusualScreenResolution = {
        ...screenInfo,
        is_unusual: isUnusual,
        spoofedMismatch: Math.abs(window.innerWidth - window.screen.width) > 100, // Detect potential spoofing
        aspectRatio: parseFloat(screenInfo.aspect_ratio)
      };

      // 🕵️ EVASION SIGNALS DETECTION
      this.behavioralData.evasionSignals = {
        // Automation detection
        webdriver: navigator.webdriver || false,
        automation: window.chrome && window.chrome.runtime && window.chrome.runtime.onConnect,
        phantom: window.callPhantom || window._phantom,
        selenium: window.selenium || document.$cdc_asdjflasutopfhvcZLmcfl_,

        // Browser inconsistencies
        languages_mismatch: navigator.language !== navigator.languages[0],
        plugins_empty: navigator.plugins.length === 0,
        webgl_disabled: !gl,

        // Timing inconsistencies
        performance_now_precision: performance.now() % 1 === 0, // Perfect milliseconds = suspicious

        // User agent analysis
        headless_chrome: navigator.userAgent.includes('HeadlessChrome'),
        automation_keywords: /PhantomJS|Selenium|WebDriver|ChromeDriver/.test(navigator.userAgent)
      };

      // 📊 TIMING METRICS INITIALIZATION
      this.behavioralData.timingMetrics = {
        trackingStartTime: Date.now(),
        domContentLoaded: performance.timing ? performance.timing.domContentLoaded : Date.now(),
        pageLoadComplete: performance.timing ? performance.timing.loadEventEnd : Date.now(),
        navigationStart: performance.timing ? performance.timing.navigationStart : Date.now(),
        firstPaint: performance.getEntriesByType ?
          (performance.getEntriesByType('paint').find(entry => entry.name === 'first-paint')?.startTime || 0) : 0,
        mouseMovementFrequency: 0,
        keyPressFrequency: 0,
        clickFrequency: 0,
        pageLoadTime: performance.timing ?
          (performance.timing.loadEventEnd - performance.timing.navigationStart) : 1200,
        timeToFirstClick: 0 // Will be set when first click occurs
      };

      console.log('🔍 Device fingerprinting completed:', {
        deviceFingerprint: this.behavioralData.deviceFingerprint,
        gpuSupported: !!gl,
        screenResolution: screenInfo.width_height,
        evasionSignals: Object.keys(this.behavioralData.evasionSignals).filter(
          key => this.behavioralData.evasionSignals[key]
        )
      });

    } catch (error) {
      console.error('❌ Error collecting device fingerprint:', error);
      this.behavioralData.deviceFingerprint = '0';
      this.behavioralData.missingCanvasFingerprint = true;
    }
  }

  // Helper function to create hash from string
  createHashFromString(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash).toString(16);
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

    // Debug: Log every mousemove event
    console.log('Mouse move event:', newPoint);

    // 🛡️ Ensure arrays are initialized
    this.ensureArraysInitialized();

    // 🎯 RECORD BASELINE EVENT if collecting baseline
    if (this.behavioralData.isCollectingBaseline) {
      this.recordBaselineEvent('mouseMove', event, now);
    }

    // Throttle mouse tracking
    if (now - this.behavioralData.lastUpdateTime < 50) return;

    // 🕰️ DETECT HESITATION PATTERNS - pauses between movements
    if (this.behavioralData.lastMouseMove) {
      const timeSinceLastMove = now - this.behavioralData.lastMouseMove.timestamp;

      // Detect hesitation (pause between 200ms - 2000ms during active interaction)
      if (timeSinceLastMove > 200 && timeSinceLastMove < 2000) {
        this.behavioralData.hesitationTimes.push({
          duration: timeSinceLastMove,
          timestamp: now,
          beforeAction: 'mouseMove'
        });
      }

      // Detect micropause (very short pauses 50ms - 200ms)
      if (timeSinceLastMove > 50 && timeSinceLastMove < 200) {
        this.behavioralData.microPauses.push({
          duration: timeSinceLastMove,
          timestamp: now,
          beforeAction: 'mouseMove'
        });
      }
    }

    // Store movement with page context
    this.behavioralData.cursorMovements = [
      ...this.behavioralData.cursorMovements.slice(-499), // Keep last 500 movements
      newPoint
    ];

    // Calculate speed and advanced metrics if we have previous movement
    if (this.behavioralData.lastMouseMove) {
      const dx = newPoint.x - this.behavioralData.lastMouseMove.x;
      const dy = newPoint.y - this.behavioralData.lastMouseMove.y;
      const dt = (now - this.behavioralData.lastMouseMove.timestamp) / 1000;

      if (dt > 0) {
        const distance = Math.sqrt(dx * dx + dy * dy);
        const speed = distance / dt;

        // Debug: Log calculated distance and speed
        console.log('Mouse movement metrics:', { distance, speed, dt });

        if (speed > 0 && speed < 5000) { // Filter out unrealistic speeds
          this.behavioralData.cursorSpeeds = [
            ...this.behavioralData.cursorSpeeds.slice(-99),
            speed
          ];
          this.behavioralData.latestSpeed = speed;

          // 📊 CALCULATE CURSOR ACCELERATION
          if (this.behavioralData.cursorSpeeds.length > 1) {
            const prevSpeed = this.behavioralData.cursorSpeeds[this.behavioralData.cursorSpeeds.length - 2];
            const acceleration = (speed - prevSpeed) / dt;
            this.behavioralData.cursorAcceleration.push(acceleration);
          }

          // 📈 CALCULATE CURSOR CURVATURE (angular change)
          if (this.behavioralData.cursorMovements.length > 2) {                   
            const prevMovement = this.behavioralData.cursorMovements[this.behavioralData.cursorMovements.length - 2];
            const currentAngle = Math.atan2(dy, dx);
            const prevDx = prevMovement.x - (this.behavioralData.cursorMovements[this.behavioralData.cursorMovements.length - 3] || {x: 0}).x;
            const prevDy = prevMovement.y - (this.behavioralData.cursorMovements[this.behavioralData.cursorMovements.length - 3] || {y: 0}).y;
            const prevAngle = Math.atan2(prevDy, prevDx);
            const curvature = Math.abs(currentAngle - prevAngle);
            this.behavioralData.cursorCurvature.push(curvature);
            this.behavioralData.cursorAngles.push(currentAngle);
          }

          // 🎯 DETECT MOUSE JITTER (rapid small movements)
          if (distance < 5 && speed > 100) { // Small distance but high speed = jitter
            console.log('Mouse jitter detected:', { distance, speed, coordinates: { x: newPoint.x, y: newPoint.y } });
            this.behavioralData.mouseJitter.push({
              timestamp: now,
              distance: distance,
              speed: speed,
              coordinates: {x: newPoint.x, y: newPoint.y}
            });
          }
        }
      }
    }

    // 📊 UPDATE TIMING METRICS
    this.behavioralData.timingMetrics.lastMouseMove = now;
    this.behavioralData.timingMetrics.mouseMovementFrequency = 
      (this.behavioralData.timingMetrics.mouseMovementFrequency || 0) + 1;

    this.behavioralData.lastMouseMove = newPoint;
    this.behavioralData.lastUpdateTime = now;
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

    // 🎯 Track time to first click
    if (this.behavioralData.timingMetrics.timeToFirstClick === 0) {
      this.behavioralData.timingMetrics.timeToFirstClick = now - this.behavioralData.trackingStartTime;
    }

    // 🎯 RECORD BASELINE EVENT if collecting baseline
    if (this.behavioralData.isCollectingBaseline) {
      this.recordBaselineEvent('click', event, now);
    }

    // 🕰️ DETECT HESITATION PATTERNS before clicks
    if (this.behavioralData.lastClickTime) {
      const timeSinceLastClick = now - this.behavioralData.lastClickTime;

      // Detect click hesitation (pause between 500ms - 5000ms)
      if (timeSinceLastClick > 500 && timeSinceLastClick < 5000) {
        this.behavioralData.hesitationTimes.push({
          duration: timeSinceLastClick,
          timestamp: now,
          beforeAction: 'click',
          coordinates: { x: event.clientX, y: event.clientY }
        });
      }
    }

    this.behavioralData.clickTimestamps = [
      ...this.behavioralData.clickTimestamps.slice(-99),
      now
    ];

    // Calculate click intervals and detect patterns
    if (this.behavioralData.lastClickTime) {
      const interval = now - this.behavioralData.lastClickTime;
      this.behavioralData.clickTimes = [
        ...this.behavioralData.clickTimes.slice(-99),
        interval
      ];

      // 🤖 DETECT ROBOTIC CLICKING PATTERNS
      if (this.behavioralData.clickTimes.length > 3) {
        const recentIntervals = this.behavioralData.clickTimes.slice(-5);
        const avgInterval = recentIntervals.reduce((sum, int) => sum + int, 0) / recentIntervals.length;
        const variance = recentIntervals.reduce((sum, int) => sum + Math.pow(int - avgInterval, 2), 0) / recentIntervals.length;

        // Very regular intervals suggest automation
        if (variance < 50 && avgInterval < 1000) {
          this.behavioralData.suspiciousPatterns.push({
            type: 'mechanical_clicking',
            timestamp: now,
            metrics: { avgInterval, variance }
          });
        }
      }
    }

    // 📊 UPDATE TIMING METRICS
    this.behavioralData.timingMetrics.lastClick = now;
    this.behavioralData.timingMetrics.clickFrequency =
      (this.behavioralData.timingMetrics.clickFrequency || 0) + 1;

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

  getCurrentPage() {
    return this.behavioralData.currentPage || 'unknown';
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

      // 📊 CALCULATE CURRENT IDLE TIME
      const now = Date.now();
      const timeSinceLastAction = now - this.behavioralData.lastActionTime;

      // Update idle time if user has been inactive for more than 2 seconds
      if (timeSinceLastAction > 2000) {
        this.behavioralData.idleTime += Math.min(timeSinceLastAction, 30000); // Cap at 30 seconds per measurement
      }

      // 📊 UPDATE TIMING METRICS
      this.behavioralData.timingMetrics.currentIdleTime = timeSinceLastAction;
      this.behavioralData.timingMetrics.totalIdleTime = this.behavioralData.idleTime;
      this.behavioralData.timingMetrics.lastSaveTime = now;

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

      // 🔬 COSINE SIMILARITY: Create rolling windows for analysis
      const rollingWindowData = this.createRollingWindows();

      // 🔧 Convert frontend data to backend format (Django model structure)
      const convertedBehavioralData = this.convertToBackendFormat();

      // 🔍 DEBUG: Log the converted data format
      console.log('🔧 Converted behavioral data format:', {
        cursor_movements_length: convertedBehavioralData.cursor_movements?.length || 0,
        cursor_movements_sample: convertedBehavioralData.cursor_movements?.slice(0, 3),
        original_movements_sample: this.behavioralData.cursorMovements?.slice(0, 3),
        total_time: convertedBehavioralData.total_time,
        action_count: convertedBehavioralData.action_count
      });

      // Send full behavioral payload for continuous monitoring (post-baseline)
      console.log('📤 Sending cosine similarity behavioral payload to backend...', {
        sessionId: this.sessionId,
        dataPoints: Object.keys(convertedBehavioralData).length,
        actionCount: convertedBehavioralData.action_count,
        baselineCompleted: this.behavioralData.baselineCompleted,
        rollingWindows: rollingWindowData.windows.length,
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
          analysis_type: 'cosine_similarity', // 🎯 NEW: Specify analysis type
          similarity_threshold: 0.75, // 🎯 75% threshold as requested
          behavioral_data: {
            // 🔧 USE CONVERTED DATA that matches Django model exactly
            ...convertedBehavioralData,
            timestamp: Date.now(),
            currentPage: this.behavioralData.currentPage || 'unknown',
            // 🔬 ROLLING WINDOW DATA for cosine similarity
            rollingWindows: rollingWindowData.windows,
            windowMetadata: rollingWindowData.metadata,
            // Reference baseline data if available
            baselineData: this.behavioralData.baselineBehaviorData,
            baselineMetrics: this.calculateBaselineMetrics()
          }
        })
      });

      if (response.ok) {
        const result = await response.json();
        console.log('📊 Cosine similarity analysis result:', {
          status: result.user_auth_status,
          authorized: result.is_authorized,
          cosineSimilarity: result.cosine_similarity,
          windowSimilarities: result.window_similarities,
          riskScore: result.risk_score,
          recommendation: result.recommendation,
          analysisType: result.analysis_type
        });

        // Store analysis result
        this.behavioralData.lastAnalysisResult = result;
        this.behavioralData.lastAnalysisTime = Date.now();

        // 🚨 Handle unauthorized users based on cosine similarity
        if (!result.is_authorized) {
          console.warn('🚨 UNAUTHORIZED USER DETECTED via Cosine Similarity!');
          console.warn(`⚠️ Similarity Score: ${result.cosine_similarity || 'unknown'}`);
          console.warn(`⚠️ Threshold: ${result.similarity_threshold || 0.75}`);
          console.warn('⚠️ Recommendation:', result.recommendation);

          // Show authentication needed message
          this.showAuthenticationMessage(result.recommendation || 'Behavioral patterns do not match authorized user');

          // Stop further behavioral tracking for unauthorized users
          this.handleUnauthorizedUser(result);
        }

        // Emit custom event for components to react to
        window.dispatchEvent(new CustomEvent('behavioralAnalysis', {
          detail: result
        }));
      } else {
        console.warn('Backend cosine similarity analysis failed:', response.status, response.statusText);
      }
    } catch (error) {
      console.warn('Could not send cosine similarity behavioral data to backend:', error.message);
    }
  }

  // 🔧 Convert frontend camelCase data to Django snake_case format
  convertToBackendFormat() {
    try {
      // Calculate derived metrics first
      const totalTime = Date.now() - (this.behavioralData.trackingStartTime || Date.now());
      const clickIntervals = this.calculateClickIntervals();
      const suspiciousFeatureRatio = this.calculateSuspiciousFeatureRatio();
      const averageSpeed = this.calculateAverageSpeed();
      const maxSpeed = this.calculateMaxSpeed();
      const cursorAngleVariance = this.calculateCursorAngleVariance();
      const cursorEntropy = this.calculateCursorEntropy();

      // Analyze behavioral patterns
      const keyboardPatterns = this.analyzeKeyboardPatterns();
      const suspiciousPatterns = this.detectSuspiciousPatterns();
      const humanIndicators = this.detectHumanIndicators();
      const botIndicators = this.detectBotIndicators();

      // Calculate human/bot scores
      const humanScore = this.calculateHumanScore();
      const botScore = 1 - humanScore;

      // Detect automation signals
      const isAutomatedBrowser = this.detectAutomatedBrowser();
      const evasionSignals = this.detectEvasionSignals();

      // Get device fingerprinting data
      const deviceFingerprint = this.generateDeviceFingerprint();
      const canvasMetrics = this.getCanvasMetrics();
      const gpuInfo = this.getGPUInfo();
      const screenResolution = this.getScreenResolution();

      // Map frontend data to Django model fields exactly
      const backendData = {
        // Core behavioral data - convert cursor movements to coordinate pairs
        cursor_movements: (this.behavioralData.cursorMovements || []).map(point => ({ x: point.x, y: point.y, timestamp: Date.now() })),
        key_press_times: this.behavioralData.keyPressTimes || [],
        key_hold_times: this.behavioralData.keyHoldTimes || [],
        click_timestamps: this.behavioralData.clickTimestamps || [],
        click_intervals: clickIntervals,
        cursor_speeds: this.behavioralData.cursorSpeeds || [],
        cursor_acceleration: this.behavioralData.cursorAcceleration || [],
        cursor_curvature: this.behavioralData.cursorCurvature || [],

        // Boolean and basic fields
        paste_detected: this.behavioralData.pasteDetected || false,
        total_time: Math.floor(totalTime),

        // Classification and scores
        classification: humanScore > 0.6 ? "Human" : (botScore > 0.6 ? "Bot" : "Unknown"),
        human_score: parseFloat(humanScore.toFixed(2)),
        bot_score: parseFloat(botScore.toFixed(2)),

        // Indicator arrays
        human_indicators: humanIndicators,
        bot_indicators: botIndicators,

        // Fingerprinting and detection scores
        bot_fingerprint_score: parseFloat((botScore * 0.1).toFixed(2)),
        suspicious_flag: suspiciousPatterns.length > 0 || botScore > 0.7,
        suspicious_feature_ratio: parseFloat(suspiciousFeatureRatio.toFixed(2)),

        // Enhanced metrics - debug data
        mouse_movement_debug: {
          raw_path_points: (this.behavioralData.cursorMovements || []).map(point => ({ x: point.x, y: point.y })),
          filtered_points: (this.behavioralData.cursorMovements || []).map(point => ({ x: point.x, y: point.y }))
        },

        speed_calculation_debug: {
          average_speed: parseFloat(averageSpeed.toFixed(2)),
          max_speed: parseFloat(maxSpeed.toFixed(2))
        },

        post_paste_activity: {
          keypress_after_paste: this.behavioralData.postPasteActivity?.keypressAfterPaste || 0
        },

        keyboard_patterns: keyboardPatterns,
        suspicious_patterns: suspiciousPatterns,

        // Counters and metrics
        action_count: this.behavioralData.actionCount || 0,
        is_automated_browser: isAutomatedBrowser,
        cursor_entropy: parseFloat(cursorEntropy.toFixed(2)),
        scroll_speeds: this.behavioralData.scrollSpeeds || [],
        scroll_changes: this.behavioralData.scrollChanges || 0,
        idle_time: this.behavioralData.idleTime || 0,

        // Additional detection fields
        honeypot_value: this.behavioralData.honeypotValue || "",
        tabkeycount: this.behavioralData.TabKeyCount || 0,
        cursorAngleVariance: parseFloat(cursorAngleVariance.toFixed(3)),
        mouseJitter: (this.behavioralData.mouseJitter || []).map(j => parseFloat((j.distance || 0).toFixed(3))),
        micropause: (this.behavioralData.microPauses || []).map(p => p.duration || 0),
        hesitation: (this.behavioralData.hesitationTimes || []).map(h => h.duration || 0),

        // Device and fingerprinting
        devicefingerprint: deviceFingerprint,
        missing_canvas_fingerprint: !canvasMetrics.hash,
        canvas_metrics: canvasMetrics,
        unsualscreenresolution: screenResolution,
        gpu_info: gpuInfo,

        timing_metrics: {
          page_load_time: this.behavioralData.timingMetrics?.pageLoadTime || 0,
          time_to_first_click: this.behavioralData.timingMetrics?.timeToFirstClick || 0
        },

        evasion_signals: evasionSignals
      };

      console.log('🔧 Converted frontend data to backend format:', {
        totalFields: Object.keys(backendData).length,
        cursorMovements: backendData.cursor_movements.length,
        keyPresses: backendData.key_press_times.length,
        clicks: backendData.click_timestamps.length,
        actionCount: backendData.action_count,
        humanScore: backendData.human_score,
        botScore: backendData.bot_score,
        classification: backendData.classification
      });

      return backendData;

    } catch (error) {
      console.error('❌ Error converting to backend format:', error);
      return {};
    }
  }

  // Helper functions for calculated fields
  calculateClickIntervals() {
    const clickTimes = this.behavioralData.clickTimestamps || [];
    if (clickTimes.length < 2) return [];

    const intervals = [];
    for (let i = 1; i < clickTimes.length; i++) {
      intervals.push(clickTimes[i] - clickTimes[i - 1]);
    }
    return intervals;
  }

  calculateSuspiciousFeatureRatio() {
    const totalFeatures = 10; // Total number of features we check
    const suspiciousCount = (this.behavioralData.suspiciousPatterns || []).length;
    return totalFeatures > 0 ? suspiciousCount / totalFeatures : 0;
  }

  calculateAverageSpeed() {
    const speeds = this.behavioralData.cursorSpeeds || [];
    return speeds.length > 0 ? speeds.reduce((sum, speed) => sum + speed, 0) / speeds.length : 0;
  }

  calculateMaxSpeed() {
    const speeds = this.behavioralData.cursorSpeeds || [];
    return speeds.length > 0 ? Math.max(...speeds) : 0;
  }

  calculateSpeedVariance() {
    const speeds = this.behavioralData.cursorSpeeds || [];
    if (speeds.length < 2) return 0;

    const mean = this.calculateAverageSpeed();
    const variance = speeds.reduce((sum, speed) => sum + Math.pow(speed - mean, 2), 0) / speeds.length;
    return variance;
  }

  calculateCursorAngleVariance() {
    const angles = this.behavioralData.cursorAngles || [];
    if (angles.length < 2) return 0;

    const mean = angles.reduce((sum, angle) => sum + angle, 0) / angles.length;
    const variance = angles.reduce((sum, angle) => sum + Math.pow(angle - mean, 2), 0) / angles.length;
    return variance;
  }

  calculateCursorEntropy() {
    const movements = this.behavioralData.cursorMovements || [];
    if (movements.length < 2) return 0;

    // Calculate entropy based on movement patterns
    const distances = [];
    for (let i = 1; i < movements.length; i++) {
      const dx = movements[i].x - movements[i - 1].x;
      const dy = movements[i].y - movements[i - 1].y;
      const distance = Math.sqrt(dx * dx + dy * dy);
      distances.push(distance);
    }

    // Simple entropy calculation
    if (distances.length === 0) return 0;
    const mean = distances.reduce((sum, d) => sum + d, 0) / distances.length;
    const variance = distances.reduce((sum, d) => sum + Math.pow(d - mean, 2), 0) / distances.length;
    return Math.min(0.99, variance / (mean + 1)); // Normalize to 0-1 range
  }

  analyzeKeyboardPatterns() {
    const patterns = [];
    const keyTimes = this.behavioralData.keyPressTimes || [];

    if (keyTimes.length > 1) {
      // Analyze typing rhythm
      const intervals = [];
      for (let i = 1; i < keyTimes.length; i++) {
        intervals.push(keyTimes[i] - keyTimes[i - 1]);
      }

      const avgInterval = intervals.reduce((sum, interval) => sum + interval, 0) / intervals.length;

      if (avgInterval < 100) {
        patterns.push("fast_typing");
      } else if (avgInterval > 300) {
        patterns.push("slow_typing");
      } else {
        patterns.push("normal_typing");
      }

      // Check for pauses
      const longPauses = intervals.filter(interval => interval > 1000);
      if (longPauses.length > 0) {
        patterns.push("pause_resume_typing");
      }

      // Check for consistent timing
      const variance = intervals.reduce((sum, interval) => sum + Math.pow(interval - avgInterval, 2), 0) / intervals.length;
      if (variance < avgInterval * 0.1) {
        patterns.push("consistent_timing");
      } else {
        patterns.push("variable_typing_speed");
      }
    }

    return patterns;
  }

  detectSuspiciousPatterns() {
    const patterns = [];

    // Check for very regular timing
    const keyTimes = this.behavioralData.keyPressTimes || [];
    if (keyTimes.length > 3) {
      const intervals = [];
      for (let i = 1; i < keyTimes.length; i++) {
        intervals.push(keyTimes[i] - keyTimes[i - 1]);
      }

      const avgInterval = intervals.reduce((sum, interval) => sum + interval, 0) / intervals.length;
      const variance = intervals.reduce((sum, interval) => sum + Math.pow(interval - avgInterval, 2), 0) / intervals.length;

      if (variance < avgInterval * 0.05) {
        patterns.push("too_regular_timing");
      }
    }

    // Check for impossible speeds
    const speeds = this.behavioralData.cursorSpeeds || [];
    const impossibleSpeeds = speeds.filter(speed => speed > 3000); // Pixels per second
    if (impossibleSpeeds.length > speeds.length * 0.1) {
      patterns.push("impossible_mouse_speed");
    }

    // Check for straight line movements
    const movements = this.behavioralData.cursorMovements || [];
    if (movements.length > 10) {
      let straightLines = 0;
      for (let i = 2; i < movements.length; i++) {
        const p1 = movements[i - 2], p2 = movements[i - 1], p3 = movements[i];
        // Calculate if points are nearly collinear
        const area = Math.abs((p2.x - p1.x) * (p3.y - p1.y) - (p3.x - p1.x) * (p2.y - p1.y));
        if (area < 1) straightLines++;
      }

      if (straightLines > movements.length * 0.8) {
        patterns.push("too_many_straight_lines");
      }
    }

    return patterns;
  }

  detectHumanIndicators() {
    const indicators = [];

    // Smooth mouse movements
    const movements = this.behavioralData.cursorMovements || [];
    if (movements.length > 5) {
      let smoothMovements = 0;
      for (let i = 1; i < movements.length; i++) {
        const dx = movements[i].x - movements[i - 1].x;
        const dy = movements[i].y - movements[i - 1].y;
        const distance = Math.sqrt(dx * dx + dy * dy);
        if (distance > 1 && distance < 50) smoothMovements++;
      }

      if (smoothMovements > movements.length * 0.6) {
        indicators.push("smooth_mouse");
      }
    }

    // Variable typing speed
    const patterns = this.analyzeKeyboardPatterns();
    if (patterns.includes("variable_typing_speed")) {
      indicators.push("variable_typing_speed");
    }

    // Natural hesitation
    const hesitations = this.behavioralData.hesitationTimes || [];
    if (hesitations.length > 0) {
      indicators.push("natural_hesitation");
    }

    // Mouse jitter (natural micro-movements)
    const jitter = this.behavioralData.mouseJitter || [];
    if (jitter.length > 0 && jitter.length < movements.length * 0.1) {
      indicators.push("natural_micro_movements");
    }

    return indicators;
  }

  detectBotIndicators() {
    const indicators = [];
    const suspicious = this.detectSuspiciousPatterns();

    suspicious.forEach(pattern => {
      switch (pattern) {
        case "too_regular_timing":
          indicators.push("robotic_timing");
          break;
        case "impossible_mouse_speed":
          indicators.push("impossible_speeds");
          break;
        case "too_many_straight_lines":
          indicators.push("mechanical_movements");
          break;
      }
    });

    return indicators;
  }

  calculateHumanScore() {
    let score = 0.5; // Start neutral

    const humanIndicators = this.detectHumanIndicators();
    const botIndicators = this.detectBotIndicators();

    // Add points for human indicators
    score += humanIndicators.length * 0.1;

    // Subtract points for bot indicators
    score -= botIndicators.length * 0.15;

    // Bonus for natural behavior patterns
    const movements = this.behavioralData.cursorMovements || [];
    const keyTimes = this.behavioralData.keyPressTimes || [];

    if (movements.length > 10 && keyTimes.length > 5) {
      score += 0.1; // Bonus for sufficient activity
    }

    // Ensure score is between 0 and 1
    return Math.max(0, Math.min(1, score));
  }

  detectAutomatedBrowser() {
    // Check for automation indicators
    const botIndicators = this.detectBotIndicators();
    const suspiciousPatterns = this.detectSuspiciousPatterns();

    // Check for webdriver properties
    const hasWebDriver = navigator.webdriver || window.webdriver;

    // Check for automation frameworks
    const hasPhantom = window.phantom || window._phantom;
    const hasSelenium = window.selenium || window.__selenium_unwrapped;

    return hasWebDriver || hasPhantom || hasSelenium ||
      botIndicators.length > 2 || suspiciousPatterns.length > 3;
  }

  detectEvasionSignals() {
    return {
      headless_mode: navigator.webdriver === true,
      devtools_open: this.detectDevToolsOpen(),
      phantom_detected: !!(window.phantom || window._phantom),
      selenium_detected: !!(window.selenium || window.__selenium_unwrapped),
      webdriver_detected: !!navigator.webdriver
    };
  }

  detectDevToolsOpen() {
    // Simple detection method - there are more sophisticated ways
    let devtools = false;
    const threshold = 160;

    try {
      if (window.outerHeight - window.innerHeight > threshold ||
        window.outerWidth - window.innerWidth > threshold) {
        devtools = true;
      }
    } catch (e) {
      // Silent fail
    }

    return devtools;
  }

  generateDeviceFingerprint() {
    // Create a simple device fingerprint
    const components = [
      navigator.userAgent,
      navigator.language,
      window.screen.width + 'x' + window.screen.height,
      new Date().getTimezoneOffset(),
      navigator.platform,
      navigator.cookieEnabled
    ];

    // Simple hash function
    let hash = 0;
    const str = components.join('|');
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }

    return Math.abs(hash).toString(16);
  }

  getCanvasMetrics() {
    try {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      canvas.width = 200;
      canvas.height = 50;

      ctx.textBaseline = 'top';
      ctx.font = '14px Arial';
      ctx.fillText('Canvas fingerprint', 2, 2);

      const dataURL = canvas.toDataURL();

      // Simple hash of canvas data
      let hash = 0;
      for (let i = 0; i < dataURL.length; i++) {
        const char = dataURL.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash;
      }

      return {
        width: canvas.width,
        height: canvas.height,
        hash: Math.abs(hash).toString(16).substring(0, 9)
      };
    } catch (e) {
      return { width: 0, height: 0, hash: null };
    }
  }

  getGPUInfo() {
    try {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');

      if (gl) {
        const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
        if (debugInfo) {
          const vendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
          const renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);

          return {
            vendor: vendor || 'Unknown',
            model: renderer || 'Unknown'
          };
        }
      }
    } catch (e) {
      // Silent fail
    }

    return { vendor: 'Unknown', model: 'Unknown' };
  }

  getScreenResolution() {
    return {
      width: window.screen.width,
      height: window.screen.height,
      unusual: window.screen.width < 800 || window.screen.height < 600 ||
        window.screen.width > 3840 || window.screen.height > 2160
    };
  }

  setupUnloadHandler() {
    const handleUnload = () => {
      // Final save before page unload
      this.updateCrossPageMetrics();
      this.saveToLocalStorage();
    };

    window.addEventListener('beforeunload', handleUnload);
    window.addEventListener('pagehide', handleUnload);
  }

  // 🌐 NAVIGATION DETECTION: Handle URL changes and manual navigation
  setupNavigationDetection() {
    console.log('🌐 Setting up navigation detection for URL changes...');

    // Store initial URL
    this.currentUrl = window.location.href;
    this.lastNavigationTime = Date.now();

    // 1️⃣ Detect popstate events (back/forward button, manual URL entry)
    const handlePopState = (event) => {
      console.log('🔄 POPSTATE detected - URL changed manually or via browser navigation');
      this.handleUrlChange('popstate', window.location.href);
    };

    // 2️⃣ Detect hash changes
    const handleHashChange = (event) => {
      console.log('🔄 HASHCHANGE detected - Fragment identifier changed');
      this.handleUrlChange('hashchange', window.location.href);
    };

    // 3️⃣ Override pushState and replaceState to detect programmatic navigation
    const originalPushState = window.history.pushState;
    const originalReplaceState = window.history.replaceState;

    window.history.pushState = function (...args) {
      originalPushState.apply(window.history, args);
      console.log('🔄 PUSHSTATE detected - Programmatic navigation');
      window.globalBehavioralTrackerInstance?.handleUrlChange('pushstate', window.location.href);
    };

    window.history.replaceState = function (...args) {
      originalReplaceState.apply(window.history, args);
      console.log('🔄 REPLACESTATE detected - Programmatic navigation');
      window.globalBehavioralTrackerInstance?.handleUrlChange('replacestate', window.location.href);
    };

    // 4️⃣ Periodic URL checking (fallback for manual address bar changes)
    this.urlCheckInterval = setInterval(() => {
      const currentUrl = window.location.href;
      if (currentUrl !== this.currentUrl) {
        console.log('🔄 URL CHANGE detected via periodic check');
        console.log(`Previous: ${this.currentUrl}`);
        console.log(`Current: ${currentUrl}`);
        this.handleUrlChange('manual_check', currentUrl);
      }
    }, 500); // Check every 500ms

    // 5️⃣ Listen for page visibility changes (when user comes back to tab)
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        const currentUrl = window.location.href;
        if (currentUrl !== this.currentUrl) {
          console.log('🔄 URL CHANGE detected on visibility change');
          this.handleUrlChange('visibility_change', currentUrl);
        }
      }
    };

    // 6️⃣ Listen for focus events (when user clicks on browser tab)
    const handleFocus = () => {
      const currentUrl = window.location.href;
      if (currentUrl !== this.currentUrl) {
        console.log('🔄 URL CHANGE detected on focus');
        this.handleUrlChange('focus_change', currentUrl);
      }
    };

    // Add event listeners
    window.addEventListener('popstate', handlePopState);
    window.addEventListener('hashchange', handleHashChange);
    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('focus', handleFocus);

    // Store listeners for cleanup
    this.eventListeners.push(
      { element: window, event: 'popstate', handler: handlePopState },
      { element: window, event: 'hashchange', handler: handleHashChange },
      { element: document, event: 'visibilitychange', handler: handleVisibilityChange },
      { element: window, event: 'focus', handler: handleFocus }
    );

    console.log('✅ Navigation detection setup complete');
  }

  // 🔄 HANDLE URL CHANGES: Reset behavioral data when URL changes
  handleUrlChange(changeType, newUrl) {
    try {
      const now = Date.now();
      const timeSinceLastNav = now - this.lastNavigationTime;

      console.log(`🌐 URL CHANGE DETECTED:`);
      console.log(`  Type: ${changeType}`);
      console.log(`  Previous URL: ${this.currentUrl}`);
      console.log(`  New URL: ${newUrl}`);
      console.log(`  Time since last navigation: ${timeSinceLastNav}ms`);

      // 🚨 CRITICAL: Only reset if significant time has passed or it's a different page
      const isDifferentPage = this.isDifferentPage(this.currentUrl, newUrl);
      const isSignificantNavigation = timeSinceLastNav > 1000; // More than 1 second

      if (isDifferentPage && isSignificantNavigation) {
        console.log('🔄 RESETTING BEHAVIORAL DATA due to page navigation');
        this.resetBehavioralDataForNewPage(changeType, newUrl);
      } else {
        console.log('⏭️ Skipping reset - same page or rapid navigation');
      }

      // Update tracking variables
      this.currentUrl = newUrl;
      this.lastNavigationTime = now;

    } catch (error) {
      console.error('❌ Error handling URL change:', error);
    }
  }

  // 🔍 CHECK IF DIFFERENT PAGE: Determine if URL change represents a new page
  isDifferentPage(oldUrl, newUrl) {
    try {
      if (!oldUrl || !newUrl) return true;

      const oldParsed = new URL(oldUrl);
      const newParsed = new URL(newUrl);

      // Different if:
      // 1. Different domain
      if (oldParsed.hostname !== newParsed.hostname) return true;

      // 2. Different path (ignoring hash)
      if (oldParsed.pathname !== newParsed.pathname) return true;

      // 3. Different search parameters
      if (oldParsed.search !== newParsed.search) return true;

      // Same page if only hash changed
      return false;

    } catch (error) {
      console.error('❌ Error comparing URLs:', error);
      return true; // Assume different page on error
    }
  }

  // 🔄 RESET BEHAVIORAL DATA: Start fresh tracking for new page
  resetBehavioralDataForNewPage(navigationType, newUrl) {
    try {
      console.log('🔄 RESETTING BEHAVIORAL DATA FOR NEW PAGE');

      // 1️⃣ Save backend interval state before clearing
      const wasBackendTransmissionActive = this.backendIntervalId !== null;
      console.log(`🔍 Backend transmission was active: ${wasBackendTransmissionActive}`);

      // 2️⃣ Stop current event tracking (but preserve backend transmission)
      this.stopTracking();

      // 3️⃣ Handle baseline timer carefully during navigation
      // Only clear baseline timer if baseline collection is actually complete
      if (this.baselineTimerId && this.behavioralData.baselineCompleted) {
        console.log('🧹 Clearing completed baseline timer during navigation');
        clearTimeout(this.baselineTimerId);
        this.baselineTimerId = null;
      } else if (this.baselineTimerId) {
        console.log('⏰ Preserving active baseline timer during navigation');
        // Keep the timer running across navigation
      }

      // ⚠️ DO NOT clear backendIntervalId - keep it running for continuous transmission

      // 4️⃣ Clear only component-specific storage (not session data)
      localStorage.removeItem('behavioral_data_auth_session');
      localStorage.removeItem('behavioral_data_signin_session');
      localStorage.removeItem('behavioral_data_signup_session');
      localStorage.removeItem('behavioral_data_captcha_session');
      localStorage.removeItem('behavioral_data_pattern_session');
      localStorage.removeItem('behavioral_data_bot_analysis_session');
      localStorage.removeItem('behavioral_data_human_behavior_session');

      // 5️⃣ Reset behavioral data arrays but keep session intact
      const previousSessionId = this.sessionId;
      const previousTrackingStart = this.trackingStartTime;
      const previousTransmissionStarted = this.behavioralData.continuousTransmissionStarted; // 🚨 PRESERVE TRANSMISSION STATE

      // 🚨 PRESERVE BASELINE STATE DURING NAVIGATION
      const previousBaselineCompleted = this.behavioralData.baselineCompleted;
      const previousIsCollectingBaseline = this.behavioralData.isCollectingBaseline;
      const previousBaselineStartTime = this.behavioralData.baselineCollectionStartTime;
      const previousBaselineTimerId = this.behavioralData.baselineTimerId;

      // Reset behavioral arrays for new page
      this.behavioralData.cursorMovements = [];
      this.behavioralData.cursorSpeeds = [];
      this.behavioralData.cursorAcceleration = [];
      this.behavioralData.cursorJitter = [];
      this.behavioralData.keyPressTimes = [];
      this.behavioralData.keySequences = [];
      this.behavioralData.clickTimestamps = [];
      this.behavioralData.clickPositions = [];
      this.behavioralData.scrollSpeeds = [];
      this.behavioralData.scrollDirections = [];
      this.behavioralData.pasteCount = 0;
      this.behavioralData.actionCount = 0;

      // Keep session identity
      this.sessionId = previousSessionId;
      this.trackingStartTime = previousTrackingStart;
      this.behavioralData.sessionId = previousSessionId;
      this.behavioralData.trackingStartTime = previousTrackingStart;
      this.behavioralData.continuousTransmissionStarted = previousTransmissionStarted; // 🚨 RESTORE TRANSMISSION STATE

      // 🚨 RESTORE BASELINE STATE DURING NAVIGATION
      this.behavioralData.baselineCompleted = previousBaselineCompleted;
      this.behavioralData.isCollectingBaseline = previousIsCollectingBaseline;
      this.behavioralData.baselineCollectionStartTime = previousBaselineStartTime;
      this.behavioralData.baselineTimerId = previousBaselineTimerId;

      // 6️⃣ Update page tracking
      this.behavioralData.currentPage = newUrl;
      this.behavioralData.pageLoadTime = Date.now();

      // Initialize pageHistory if it doesn't exist
      if (!this.behavioralData.pageHistory) {
        this.behavioralData.pageHistory = [];
      }

      this.behavioralData.pageHistory.push({
        url: newUrl,
        navigationType: navigationType,
        timestamp: Date.now(),
        timeSpent: 0
      });

      // 7️⃣ Restart tracking systems (but don't restart backend if it was already running)
      this.startGlobalTracking();

      // 🚨 CRITICAL: DO NOT restart baseline collection during navigation
      // Baseline should only start once when URL is manually entered
      if (!this.behavioralData.baselineCompleted && !this.behavioralData.isCollectingBaseline) {
        console.log('🎯 Starting baseline collection (first time only)');
        this.startImmediateBaselineCollection();
      } else {
        console.log('✅ Baseline already running or completed - no restart needed');
      }

      this.setupPeriodicSaving();

      // 8️⃣ Only start backend transmission if baseline collection is ACTUALLY complete
      console.log('🔍 TRANSMISSION CHECK:');
      console.log('  wasBackendTransmissionActive:', wasBackendTransmissionActive);
      console.log('  baselineCompleted:', this.behavioralData.baselineCompleted);
      console.log('  isCollectingBaseline:', this.behavioralData.isCollectingBaseline);
      console.log('  continuousTransmissionStarted:', this.behavioralData.continuousTransmissionStarted);
      console.log('  baselineCollectionStartTime:', this.behavioralData.baselineCollectionStartTime);
      console.log('  currentTime:', Date.now());

      // 🎯 CRITICAL: Check if 20 seconds have actually elapsed
      let actuallyPastBaseline = false;
      if (this.behavioralData.baselineCollectionStartTime) {
        const elapsed = Date.now() - this.behavioralData.baselineCollectionStartTime;
        actuallyPastBaseline = elapsed >= 20000;
        console.log('  Time elapsed since baseline start:', elapsed, 'ms');
        console.log('  Has 20 seconds actually passed?', actuallyPastBaseline);
      } else {
        console.log('  No baseline start time found - baseline not started');
      }

      // 🚨 CRITICAL FIX: Only start transmission if ALL conditions are met:
      // 1. Backend transmission was not already active
      // 2. Baseline is marked as completed
      // 3. 20 seconds have actually elapsed since baseline started
      // 4. Continuous transmission hasn't already started
      if (!wasBackendTransmissionActive &&
        this.behavioralData.baselineCompleted &&
        actuallyPastBaseline &&
        !this.behavioralData.continuousTransmissionStarted) {
        console.log('🚀 Starting backend transmission for new page (baseline ACTUALLY completed)...');
        this.startContinuousTransmission();
      } else if (!this.behavioralData.baselineCompleted || !actuallyPastBaseline) {
        console.log('⏳ Waiting for baseline collection to complete before starting transmission...');
        if (!actuallyPastBaseline) {
          const remaining = 20000 - (Date.now() - (this.behavioralData.baselineCollectionStartTime || Date.now()));
          console.log(`⏰ ${Math.max(0, remaining / 1000).toFixed(1)} seconds remaining in baseline collection`);
        }
      } else if (this.behavioralData.continuousTransmissionStarted) {
        console.log('✅ Continuous transmission already started - no action needed');
      } else {
        console.log('✅ Backend transmission continues uninterrupted');
      }

      // 9️⃣ Log the reset
      console.log('✅ BEHAVIORAL DATA RESET COMPLETE (Session Preserved)');
      console.log(`  Session ID: ${this.sessionId} (preserved)`);
      console.log(`  Navigation Type: ${navigationType}`);
      console.log(`  New URL: ${newUrl}`);
      console.log(`  Backend transmission: ${this.backendIntervalId ? 'ACTIVE' : 'INACTIVE'}`);

    } catch (error) {
      console.error('❌ Error resetting behavioral data:', error);
    }
  }

  // 🔬 COSINE SIMILARITY: Create rolling windows for behavioral analysis
  createRollingWindows(windowSize = 10, stepSize = 5) {
    try {
      console.log('🔬 Creating rolling windows for cosine similarity analysis...');

      const windows = [];
      const metadata = {
        windowSize,
        stepSize,
        totalDataPoints: 0,
        windowsCreated: 0,
        timestamp: Date.now()
      };

      // Helper function to create windows from array data
      const createWindowsFromArray = (dataArray, windowSize, stepSize) => {
        if (!dataArray || dataArray.length < windowSize) {
          return dataArray ? [dataArray] : []; // Return single window if data is smaller
        }

        const windows = [];
        for (let i = 0; i <= dataArray.length - windowSize; i += stepSize) {
          const window = dataArray.slice(i, i + windowSize);
          windows.push(window);
        }
        return windows;
      };

      // 📊 CURSOR MOVEMENT WINDOWS
      if (this.behavioralData.cursorMovements && this.behavioralData.cursorMovements.length > 0) {
        const cursorWindows = createWindowsFromArray(
          this.behavioralData.cursorMovements,
          windowSize,
          stepSize
        );

        cursorWindows.forEach((window, index) => {
          windows.push({
            type: 'cursor_movement',
            windowIndex: index,
            data: window,
            features: this.extractCursorFeatures(window),
            timestamp: Date.now()
          });
        });

        metadata.totalDataPoints += this.behavioralData.cursorMovements.length;
        console.log(`📊 Created ${cursorWindows.length} cursor movement windows`);
      }

      // ⌨️ KEYSTROKE TIMING WINDOWS
      if (this.behavioralData.keyPressTimes && this.behavioralData.keyPressTimes.length > 0) {
        const keystrokeWindows = createWindowsFromArray(
          this.behavioralData.keyPressTimes,
          Math.min(windowSize, this.behavioralData.keyPressTimes.length),
          stepSize
        );

        keystrokeWindows.forEach((window, index) => {
          windows.push({
            type: 'keystroke_timing',
            windowIndex: index,
            data: window,
            features: this.extractKeystrokeFeatures(window),
            timestamp: Date.now()
          });
        });

        metadata.totalDataPoints += this.behavioralData.keyPressTimes.length;
        console.log(`⌨️ Created ${keystrokeWindows.length} keystroke timing windows`);
      }

      // 🖱️ CLICK PATTERN WINDOWS
      if (this.behavioralData.clickTimestamps && this.behavioralData.clickTimestamps.length > 0) {
        const clickWindows = createWindowsFromArray(
          this.behavioralData.clickTimestamps,
          Math.min(windowSize, this.behavioralData.clickTimestamps.length),
          stepSize
        );

        clickWindows.forEach((window, index) => {
          windows.push({
            type: 'click_pattern',
            windowIndex: index,
            data: window,
            features: this.extractClickFeatures(window),
            timestamp: Date.now()
          });
        });

        metadata.totalDataPoints += this.behavioralData.clickTimestamps.length;
        console.log(`🖱️ Created ${clickWindows.length} click pattern windows`);
      }

      // 📏 SCROLL BEHAVIOR WINDOWS
      if (this.behavioralData.scrollSpeeds && this.behavioralData.scrollSpeeds.length > 0) {
        const scrollWindows = createWindowsFromArray(
          this.behavioralData.scrollSpeeds,
          Math.min(windowSize, this.behavioralData.scrollSpeeds.length),
          stepSize
        );

        scrollWindows.forEach((window, index) => {
          windows.push({
            type: 'scroll_behavior',
            windowIndex: index,
            data: window,
            features: this.extractScrollFeatures(window),
            timestamp: Date.now()
          });
        });

        metadata.totalDataPoints += this.behavioralData.scrollSpeeds.length;
        console.log(`📏 Created ${scrollWindows.length} scroll behavior windows`);
      }

      metadata.windowsCreated = windows.length;

      console.log('✅ Rolling windows created successfully:', {
        totalWindows: windows.length,
        totalDataPoints: metadata.totalDataPoints,
        windowSize,
        stepSize
      });

      return {
        windows,
        metadata
      };

    } catch (error) {
      console.error('❌ Error creating rolling windows:', error);
      return {
        windows: [],
        metadata: {
          error: error.message,
          timestamp: Date.now()
        }
      };
    }
  }

  // 🔬 Extract features from cursor movement windows
  extractCursorFeatures(cursorWindow) {
    try {
      if (!cursorWindow || cursorWindow.length < 2) return [];

      const features = [];
      const speeds = [];
      const angles = [];
      const accelerations = [];

      for (let i = 1; i < cursorWindow.length; i++) {
        const prev = cursorWindow[i - 1];
        const curr = cursorWindow[i];

        const dx = curr.x - prev.x;
        const dy = curr.y - prev.y;
        const dt = (curr.timestamp - prev.timestamp) / 1000.0;

        if (dt > 0) {
          const distance = Math.sqrt(dx * dx + dy * dy);
          const speed = distance / dt;
          speeds.push(speed);

          const angle = Math.atan2(dy, dx);
          angles.push(angle);

          if (i > 1 && speeds.length > 1) {
            const acceleration = speeds[speeds.length - 1] - speeds[speeds.length - 2];
            accelerations.push(acceleration);
          }
        }
      }

      // Statistical features
      if (speeds.length > 0) {
        features.push(
          this.calculateMean(speeds),
          this.calculateMedian(speeds),
          Math.max(...speeds),
          Math.min(...speeds),
          this.calculateStandardDeviation(speeds)
        );
      }

      if (angles.length > 0) {
        features.push(
          this.calculateMean(angles),
          this.calculateStandardDeviation(angles)
        );
      }

      if (accelerations.length > 0) {
        features.push(
          this.calculateMean(accelerations),
          this.calculateStandardDeviation(accelerations)
        );
      }

      return features;
    } catch (error) {
      console.error('Error extracting cursor features:', error);
      return [];
    }
  }

  // ⌨️ Extract features from keystroke timing windows
  extractKeystrokeFeatures(keystrokeWindow) {
    try {
      if (!keystrokeWindow || keystrokeWindow.length < 2) return [];

      const intervals = [];
      for (let i = 1; i < keystrokeWindow.length; i++) {
        intervals.push(keystrokeWindow[i] - keystrokeWindow[i - 1]);
      }

      if (intervals.length === 0) return [];

      return [
        this.calculateMean(intervals),
        this.calculateMedian(intervals),
        Math.max(...intervals),
        Math.min(...intervals),
        this.calculateStandardDeviation(intervals)
      ];
    } catch (error) {
      console.error('Error extracting keystroke features:', error);
      return [];
    }
  }

  // 🖱️ Extract features from click pattern windows
  extractClickFeatures(clickWindow) {
    try {
      if (!clickWindow || clickWindow.length < 2) return [clickWindow ? clickWindow.length : 0];

      const intervals = [];
      for (let i = 1; i < clickWindow.length; i++) {
        intervals.push(clickWindow[i] - clickWindow[i - 1]);
      }

      return [
        this.calculateMean(intervals),
        this.calculateStandardDeviation(intervals),
        clickWindow.length // Click frequency
      ];
    } catch (error) {
      console.error('Error extracting click features:', error);
      return [0];
    }
  }

  // 📏 Extract features from scroll behavior windows
  extractScrollFeatures(scrollWindow) {
    try {
      if (!scrollWindow || scrollWindow.length === 0) return [];

      return [
        this.calculateMean(scrollWindow),
        this.calculateMedian(scrollWindow),
        Math.max(...scrollWindow),
        Math.min(...scrollWindow),
        this.calculateStandardDeviation(scrollWindow)
      ];
    } catch (error) {
      console.error('Error extracting scroll features:', error);
      return [];
    }
  }

  // 📊 Statistical helper functions
  calculateMean(values) {
    return values.length > 0 ? values.reduce((sum, val) => sum + val, 0) / values.length : 0;
  }

  calculateMedian(values) {
    if (values.length === 0) return 0;
    const sorted = [...values].sort((a, b) => a - b);
    const mid = Math.floor(sorted.length / 2);
    return sorted.length % 2 === 0 ? (sorted[mid - 1] + sorted[mid]) / 2 : sorted[mid];
  }

  calculateStandardDeviation(values) {
    if (values.length <= 1) return 0;
    const mean = this.calculateMean(values);
    const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / (values.length - 1);
    return Math.sqrt(variance);
  }

  saveToLocalStorage() {
    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.behavioralData));
      console.log('💾 Final behavioral data save on unload');
    } catch (error) {
      console.error('Error saving to localStorage:', error);
    }
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

    this.behavioralData.isCollectingBaseline = false;
    this.behavioralData.baselineCompleted = true;
    this.behavioralData.baselineBehaviorData.collectionEndTime = Date.now();

    // Remove baseline collection UI
    this.removeBaselineCollectionMessage();

    // Send baseline data to backend first
    this.sendBaselineToBackend().then(() => {
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

  // 🎯📊 IMMEDIATE BASELINE COLLECTION - Starts right when URL is manually entered
  startImmediateBaselineCollection() {
    console.log('🎯 STARTING IMMEDIATE BASELINE COLLECTION FROM URL ENTRY');

    // 🔄 ALWAYS COLLECT FRESH 20-SECOND BASELINE FOR EACH SESSION
    // This ensures proper behavioral analysis for each visit

    // 🔄 FORCE FRESH START: Always reset baseline state for new URL entry
    this.behavioralData.isCollectingBaseline = false;
    this.behavioralData.baselineCompleted = false;
    this.behavioralData.continuousTransmissionStarted = false; // 🚨 RESET TRANSMISSION FLAG
    this.behavioralData.baselineCollectionStartTime = null;
    this.behavioralData.baselineBehaviorData = null;

    // 🛡️ PROTECTION: Clear any existing baseline timer
    if (this.baselineTimerId) {
      clearTimeout(this.baselineTimerId);
      this.baselineTimerId = null;
    }

    // 🛡️ PROTECTION: Stop any existing continuous transmission
    if (this.backendIntervalId) {
      clearInterval(this.backendIntervalId);
      this.backendIntervalId = null;
      console.log('🛑 Stopped existing continuous transmission for fresh baseline collection');
    }

    // Clear any previous baseline completion flag
    localStorage.removeItem('global_baseline_completed');

    console.log('📊 IMMEDIATE BASELINE: Starting 20-second collection from URL entry...');
    console.log('🔇 SILENT MODE: Collection runs in background without user awareness');

    // 📊 CRITICAL: Set collection state BEFORE initializing data
    this.behavioralData.isCollectingBaseline = true;
    this.behavioralData.baselineCollectionStartTime = Date.now();
    this.behavioralData.baselineCompleted = false;

    // Initialize comprehensive baseline data structure
    this.behavioralData.baselineBehaviorData = {
      // Immediate URL entry behavior
      urlEntryTime: Date.now(),
      initialBrowsingBehavior: [],
      collectionTrigger: 'url_manual_entry_immediate',

      // Mouse behavior from first interaction
      cursorMovements: [],
      cursorSpeeds: [],
      cursorPaths: [],
      hoverPatterns: [],
      naturalMouseMovement: [],

      // Keyboard behavior from first typing
      keyPressTimes: [],
      keySequences: [],
      typingRhythm: [],
      naturalTypingPatterns: [],

      // Click behavior from first clicks
      clickTimestamps: [],
      clickPatterns: [],
      doubleClickIntervals: [],
      naturalClickBehavior: [],

      // Scroll behavior from first scrolling
      scrollSpeeds: [],
      scrollDirections: [],
      scrollPatterns: [],
      naturalScrollBehavior: [],

      // Natural browsing patterns (IRRESPECTIVE OF PAGE)
      initialPageExploration: [],
      naturalNavigationPatterns: [],
      organicInteractionFlow: [],
      crossPageBehavior: [],

      // 🦅 Page tracking arrays (MISSING - CAUSING ERROR)
      pagesVisited: [this.behavioralData.currentPage || 'unknown'],
      pageTransitions: [],
      timePerPage: [],
      navigationPatterns: [],
      idlePeriods: [],

      // 🦅 Activity tracking
      actionCount: 0,
      totalActiveTime: 0,
      lastActionTimestamp: null,

      // Baseline quality indicators
      collectionStartTime: Date.now(),
      collectionEndTime: null,
      collectionTrigger: 'url_manual_entry_immediate',
      naturalBehaviorScore: 0,
      baselineQuality: 'collecting',
      backgroundMode: true
    };

    // Set EXACTLY 20-second timer for baseline completion
    this.baselineTimerId = setTimeout(() => {
      this.completeImmediateBaselineCollection();
    }, 20000); // Exactly 20 seconds

    // Store timer reference for persistence across page changes
    this.behavioralData.baselineTimerId = this.baselineTimerId;

    // Save session state
    this.saveSession();

    console.log('✅ IMMEDIATE BASELINE: 20-second collection started from URL entry');
    console.log(`⏰ Collection will complete at: ${new Date(Date.now() + 20000).toLocaleTimeString()}`);
    console.log('🔄 Collection will continue even if user navigates between pages');
    console.log('📡 CONTINUOUS TRANSMISSION: Will start automatically AFTER baseline completes');

    return 20000; // Return duration
  }

  // 🎯📊 Complete immediate baseline collection (RUNS IRRESPECTIVE OF CURRENT PAGE)
  completeImmediateBaselineCollection() {
    if (!this.behavioralData.isCollectingBaseline) {
      console.log('⚠️ Baseline already completed or not collecting');
      return;
    }

    console.log('✅ IMMEDIATE BASELINE: Completing 20-second collection...');
    console.log('📍 COMPLETION: Irrespective of which page user is currently on');
    console.log('🔇 SILENT COMPLETION: User unaware of background process');
    console.log('📍 Current page during completion:', this.behavioralData.currentPage);
    console.log('⏰ Baseline collection time elapsed:', Date.now() - this.behavioralData.baselineCollectionStartTime, 'ms');

    // Clean up baseline timer
    if (this.baselineTimerId) {
      clearTimeout(this.baselineTimerId);
      this.baselineTimerId = null;
    }
    this.behavioralData.baselineTimerId = null;

    // Mark baseline as completed
    this.behavioralData.isCollectingBaseline = false;
    this.behavioralData.baselineCompleted = true;
    this.behavioralData.baselineBehaviorData.collectionEndTime = Date.now();
    this.behavioralData.baselineBehaviorData.baselineQuality = 'completed';

    // Calculate collection duration
    const collectionDuration = this.behavioralData.baselineBehaviorData.collectionEndTime -
      this.behavioralData.baselineBehaviorData.collectionStartTime;

    console.log(`⏰ IMMEDIATE BASELINE: Collection completed in ${collectionDuration / 1000} seconds`);
    console.log(`📊 Current page: ${this.behavioralData.currentPage || 'unknown'} (collection ran across all pages)`);

    // Store baseline completion timestamp in localStorage
    localStorage.setItem('global_baseline_completed', JSON.stringify({
      completedAt: Date.now(),
      sessionId: this.sessionId,
      duration: collectionDuration,
      trigger: 'url_manual_entry_immediate',
      completedOnPage: this.behavioralData.currentPage || 'unknown'
    }));

    // Validate baseline data quality
    const baselineStats = this.validateImmediateBaselineData();
    this.behavioralData.baselineBehaviorData.naturalBehaviorScore = baselineStats.qualityScore;

    console.log(`📊 BASELINE QUALITY: Score ${baselineStats.qualityScore.toFixed(2)}, ${baselineStats.metrics.totalInteractions} total interactions`);

    // Send baseline data to backend
    this.sendImmediateBaselineToBackend().then((result) => {
      console.log('✅ IMMEDIATE BASELINE: Sent to backend successfully');
      console.log('🔄 READY: System now ready for continuous behavioral analysis');
      console.log('📡 STARTING CONTINUOUS TRANSMISSION: Now sending behavior data every 1 second');

      // Start continuous data transmission using our safety check
      this.startContinuousTransmission();

      // Emit completion event for any listeners
      window.dispatchEvent(new CustomEvent('immediateBaselineCompleted', {
        detail: {
          baselineData: this.behavioralData.baselineBehaviorData,
          sessionId: this.sessionId,
          collectionDuration: collectionDuration,
          trigger: 'url_manual_entry_immediate',
          completedOnPage: this.behavioralData.currentPage || 'unknown',
          silentMode: true,
          backendResult: result
        }
      }));

    }).catch((error) => {
      console.error('❌ IMMEDIATE BASELINE: Backend send failed:', error);
      console.log('🔄 STARTING CONTINUOUS TRANSMISSION: Despite baseline send error, starting behavioral analysis');

      // Start continuous transmission anyway
      if (!this.backendIntervalId) {
        this.startContinuousTransmission();
        console.log('🚀 CONTINUOUS TRANSMISSION: Started despite baseline error');
      }

      // Emit completion event with error
      window.dispatchEvent(new CustomEvent('immediateBaselineCompleted', {
        detail: {
          baselineData: this.behavioralData.baselineBehaviorData,
          sessionId: this.sessionId,
          error: error.message,
          trigger: 'url_manual_entry_immediate',
          completedOnPage: this.behavioralData.currentPage || 'unknown',
          silentMode: true
        }
      }));
    });
  }

  // 📊 Validate immediate baseline data quality
  validateImmediateBaselineData() {
    const data = this.behavioralData.baselineBehaviorData;
    if (!data) {
      return { qualityScore: 0, metrics: {} };
    }

    const metrics = {
      mouseMovements: data.cursorMovements?.length || 0,
      keyPresses: data.keyPressTimes?.length || 0,
      clicks: data.clickTimestamps?.length || 0,
      scrollEvents: data.scrollSpeeds?.length || 0,
      totalInteractions: 0
    };

    metrics.totalInteractions = metrics.mouseMovements + metrics.keyPresses +
      metrics.clicks + metrics.scrollEvents;

    // Calculate quality score (0-1)
    let qualityScore = 0;
    if (metrics.totalInteractions > 0) qualityScore += 0.3;
    if (metrics.mouseMovements > 5) qualityScore += 0.3;
    if (metrics.keyPresses > 0) qualityScore += 0.2;
    if (metrics.clicks > 0) qualityScore += 0.2;

    console.log(`📊 IMMEDIATE BASELINE QUALITY: Score=${qualityScore.toFixed(2)}, Interactions=${metrics.totalInteractions}`);

    return { qualityScore, metrics };
  }

  // 📊 Send immediate baseline to backend (TRIGGERED FROM URL ENTRY)
  async sendImmediateBaselineToBackend() {
    const baselineData = this.behavioralData.baselineBehaviorData;
    if (!baselineData) {
      throw new Error('No baseline data to send');
    }

    console.log('📤 IMMEDIATE BASELINE: Sending to backend...');
    console.log('📍 TRIGGER: URL manually entered in browser address bar');

    try {
      const response = await fetch('http://127.0.0.1:8000/user/store-baseline-behavior/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: this.sessionId,
          baseline_data: baselineData,
          collection_trigger: 'url_manual_entry_immediate',
          collection_duration: 20000,
          baseline_type: 'immediate_url_entry_background',
          data_quality_score: baselineData.naturalBehaviorScore || 0.5,
          silent_collection: true,
          background_mode: true,
          cross_page_collection: true
        })
      });

      const result = await response.json();

      if (result.success) {
        console.log('✅ IMMEDIATE BASELINE: Backend storage successful');
        console.log('🔄 READY: Behavioral analysis system now ready');
        return result;
      } else {
        throw new Error(result.message || 'Backend storage failed');
      }

    } catch (error) {
      console.error('❌ IMMEDIATE BASELINE: Backend send error:', error);
      throw error;
    }
  }

  // 🎯 LEGACY: Background Baseline Collection (for backward compatibility)
  startBackgroundBaselineCollection() {
    // 🔄 FORCE FRESH START: Always reset baseline state for new page loads
    this.behavioralData.isCollectingBaseline = false;
    this.behavioralData.baselineCompleted = false;
    this.behavioralData.baselineCollectionStartTime = null;
    this.behavioralData.baselineBehaviorData = null;

    // 🛡️ PROTECTION: Clear any existing baseline timer
    if (this.baselineTimerId) {
      clearTimeout(this.baselineTimerId);
      this.baselineTimerId = null;
    }

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

    // Set baseline as HIGH PRIORITY background task - SILENT OPERATION
    // Collecting baseline across ALL pages for 20 seconds silently

    // Set 20-second timer for baseline completion
    this.baselineTimerId = setTimeout(() => {
      this.completeBackgroundBaselineCollection();
    }, this.behavioralData.baselineCollectionDuration);

    // Store timer reference for persistence
    this.behavioralData.baselineTimerId = this.baselineTimerId;

    // Save session state
    this.saveSession();

    return this.behavioralData.baselineCollectionDuration;
  }

  completeBackgroundBaselineCollection() {
    if (!this.behavioralData.isCollectingBaseline) {
      return;
    }

    // Clean up baseline timer
    if (this.baselineTimerId) {
      clearTimeout(this.baselineTimerId);
      this.baselineTimerId = null;
    }
    this.behavioralData.baselineTimerId = null;

    this.behavioralData.isCollectingBaseline = false;
    this.behavioralData.baselineCompleted = true;
    this.behavioralData.baselineBehaviorData.collectionEndTime = Date.now();

    // Validate baseline data quality silently
    const baselineStats = this.validateBaselineData();

    // Calculate comprehensive baseline profile
    this.behavioralData.baselineBehaviorData.overallBehaviorProfile = this.generateComprehensiveBaselineProfile();

    // Send baseline data to backend silently
    this.sendBaselineToBackend().then((result) => {
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
        <span>Collecting baseline behavior... Please interact normally (${this.behavioralData.baselineCollectionDuration / 1000}s)</span>
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
      return;
    }
    try {
      // Temporarily swap behavioralData for baselineBehaviorData
      const originalBehavioralData = this.behavioralData;
      this.behavioralData = { ...this.behavioralData, ...this.behavioralData.baselineBehaviorData };
      const convertedBaselineData = this.convertToBackendFormat();
      // Restore behavioralData
      this.behavioralData = originalBehavioralData;
      const payload = {
        session_id: this.sessionId,
        baseline_data: convertedBaselineData
      };
      const response = await fetch('http://127.0.0.1:8000/user/baseline-storage/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
      });
      if (response.ok) {
        const result = await response.json();
        this.behavioralData.baselineAnalysisResult = result;
        this.behavioralData.baselineAnalysisTime = Date.now();
        return result;
      } else {
        try {
          const errorBody = await response.text();
        } catch (e) {
          // Silent error handling
        }

        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
    } catch (error) {
      // Silent error handling
      throw error;
    }
  }

  startContinuousTransmission() {
    // 🚨 SAFETY CHECK: Prevent multiple transmission starts
    if (this.behavioralData.continuousTransmissionStarted) {
      console.log('🚫 CONTINUOUS TRANSMISSION ALREADY STARTED - PREVENTING DUPLICATE');
      console.log('📍 Current page:', this.behavioralData.currentPage);
      console.log('⏰ Baseline completed:', this.behavioralData.baselineCompleted);
      console.log('📡 Existing interval ID:', this.backendIntervalId);
      console.trace('🔍 Call stack for duplicate transmission attempt:');
      return;
    }

    // 🚨 CRITICAL SAFETY CHECK: Ensure 20 seconds have actually passed
    if (this.behavioralData.baselineCollectionStartTime) {
      const elapsed = Date.now() - this.behavioralData.baselineCollectionStartTime;
      if (elapsed < 20000) {
        console.log('🚫 BLOCKED: Attempting to start transmission before 20-second baseline completes');
        console.log(`⏰ Only ${elapsed}ms elapsed, need 20000ms (${(20000 - elapsed) / 1000}s remaining)`);
        console.log('📍 Current page:', this.behavioralData.currentPage);
        console.trace('🔍 Call stack for premature transmission attempt:');
        return;
      }
    }

    // Prevent duplicate intervals - only start if not already running
    if (this.backendIntervalId) {
      console.log('⚠️ Backend transmission already active, preserving existing interval');
      console.log('📍 Current page:', this.behavioralData.currentPage);
      console.log('📡 Existing interval ID:', this.backendIntervalId);
      return;
    }

    console.log('🚀 ATTEMPTING TO START CONTINUOUS TRANSMISSION');
    console.log('📍 Current page:', this.behavioralData.currentPage);
    console.log('⏰ Baseline completed:', this.behavioralData.baselineCompleted);
    console.log('📊 Baseline collecting:', this.behavioralData.isCollectingBaseline);
    console.trace('🔍 Call stack for transmission start:');

    // 🎯 MARK TRANSMISSION AS STARTED
    this.behavioralData.continuousTransmissionStarted = true;

    console.log('🔄 STARTING CONTINUOUS BEHAVIORAL DATA TRANSMISSION');
    console.log('⏰ TIMING: This starts ONLY AFTER 20-second baseline collection completes');
    console.log('📡 FREQUENCY: Sending behavior data every 1 second to backend');

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

  // 🔄 ENSURE BACKEND TRANSMISSION: Make sure backend transmission is always running
  ensureBackendTransmission() {
    if (!this.backendIntervalId) {
      console.log('🔧 Backend transmission not active, starting...');
      this.startContinuousTransmission();
    } else {
      console.log('✅ Backend transmission is active');
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

    // 🛡️ DEFENSIVE: Ensure all baseline arrays exist
    if (!baseline.cursorMovements) baseline.cursorMovements = [];
    if (!baseline.cursorSpeeds) baseline.cursorSpeeds = [];
    if (!baseline.cursorPaths) baseline.cursorPaths = [];
    if (!baseline.hoverPatterns) baseline.hoverPatterns = [];
    if (!baseline.keyPressTimes) baseline.keyPressTimes = [];
    if (!baseline.keySequences) baseline.keySequences = [];
    if (!baseline.typingRhythm) baseline.typingRhythm = [];
    if (!baseline.clickTimestamps) baseline.clickTimestamps = [];
    if (!baseline.clickPatterns) baseline.clickPatterns = [];
    if (!baseline.doubleClickIntervals) baseline.doubleClickIntervals = [];
    if (!baseline.scrollSpeeds) baseline.scrollSpeeds = [];
    if (!baseline.scrollDirections) baseline.scrollDirections = [];
    if (!baseline.scrollPatterns) baseline.scrollPatterns = [];

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
    if (currentPage) {
      // 🛡️ DEFENSIVE: Ensure pagesVisited array exists
      if (!baseline.pagesVisited) {
        baseline.pagesVisited = [currentPage];
        console.warn('🚨 Fixed missing pagesVisited array in baseline data');
      }

      if (!baseline.pagesVisited.includes(currentPage)) {
        baseline.pagesVisited.push(currentPage);

        // 🛡️ DEFENSIVE: Ensure pageTransitions array exists
        if (!baseline.pageTransitions) {
          baseline.pageTransitions = [];
        }

        if (baseline.pagesVisited.length > 1) {
          baseline.pageTransitions.push({
            from: baseline.pagesVisited[baseline.pagesVisited.length - 2],
            to: currentPage,
            timestamp: timestamp
          });
        }
      }
    }

    // 🦅 Update activity metrics
    baseline.actionCount = (baseline.actionCount || 0) + 1;
    baseline.totalActiveTime = timestamp - baseline.collectionStartTime;

    // 🛡️ DEFENSIVE: Ensure idlePeriods array exists
    if (!baseline.idlePeriods) {
      baseline.idlePeriods = [];
    }

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
      const prev = movements[i - 2];
      const curr = movements[i - 1];
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
      intervals.push(keyPressTimes[i] - keyPressTimes[i - 1]);
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
      intervals.push(clickTimestamps[i] - clickTimestamps[i - 1]);
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

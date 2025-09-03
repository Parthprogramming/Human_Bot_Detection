class GlobalBehavioralTracker {
  constructor() {
    if (window.globalBehavioralTrackerInstance) {
      console.warn('⚠️ Multiple GlobalBehavioralTracker instances detected!');
      console.warn('Existing instance:', window.globalBehavioralTrackerInstance);
      console.warn('New instance:', this);
    }
    window.globalBehavioralTrackerInstance = this;
    let currentPage = null;

    this.setCurrentPage = (pageName) => {
      console.log(`📄 Setting current page: ${pageName}`);
      currentPage = pageName;
    };

    

    this.isInitialized = false;
    this.sessionId = null;
    this.trackingStartTime = null;
    this.lastSaveTime = 0;
    this.saveInterval = 2000; 
    this.backendInterval = 1000; 
    this.isTracking = false;
    this.lastNavigationTime = Date.now();
    this.urlCheckInterval = null;

   
    this.eventListeners = [];
    this.backendIntervalId = null;
    this.userLifecycleState = 'anonymous'; 
    this.userId = null;
    this.signupTimestamp = null;
    this.loginTimestamp = null;
    this.dashboardEntryTime = null;
    this.logoutTimestamp = null;
    this.baselineTimerId = null;

    this.STORAGE_KEY = 'global_behavioral_data';
    this.SESSION_KEY = 'global_behavioral_session';

   
    this.behavioralData = {
      sessionId: null,
      trackingStartTime: null,
      pageLoadTime: null,


      isCollectingBaseline: false,
      baselineCollectionStartTime: null,
     
      baselineCompleted: false,
      continuousTransmissionStarted: false, 
      baselineBehaviorData: null,
      baselineTimerId: null, 
      
      cursorMovements: [],
      cursorSpeeds: [],
      cursorAcceleration: [],
      cursorCurvature: [],
      keyPressTimes: [],
      keyHoldTimes: [],
      clickTimestamps: [],
      scrollSpeeds: [],
      scrollChanges: 0,
      idleTime: 0,
      pasteDetected: false,
      
      
      lastKeyPress: null,
      lastKeyDown: {},
      lastMouseMove: null,
      lastClickTime: null,
      lastUpdateTime: Date.now(), 
      lastActionTime: Date.now(),
      actionCount: 0,
      
      
      mouseJitter: [],
      microPauses: [],
      hesitationTimes: [],
      
      
      keyboardPatterns: [],
      suspiciousPatterns: [],
      postPasteActivity: {
        keypressAfterPaste: 0
      },
      
    
      deviceFingerprint: null,
      canvasMetrics: {
        winding: null,
        geometryLength: 0,
        textLength: 0,
        hash: null
      },
      missingCanvasFingerprint: true,
      unusualScreenResolution: {
        width_height: "0x0",
        inner_width: 0,
        device_pixel_ratio: 0,
        is_unusual: false,
        spoofedMismatch: false,
        aspectRatio: 0,
      },
      gpuInfo: {
        vendor: 'Unknown',
        model: 'Unknown'
      },
      
      timingMetrics: {
        trackingStartTime: null,
        domContentLoaded: null,
        pageLoadComplete: null,
        navigationStart: null,
        firstPaint: null,
        mouseMovementFrequency: 0,
        keyPressFrequency: 0,
        clickFrequency: 0,
        pageLoadTime: null,
        timeToFirstClick: 0,
        lastKeyPress: null,
        lastMouseMove: null,
        lastClick: null
      },
      
      currentPage: null,
      
      honeypotValue: "",
      TabKeyCount: 0,
      

    };


    if (typeof window !== 'undefined') {
      this.init();
    }

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.init());
    } else {
      setTimeout(() => this.init(), 0);
    }
  }

  init() {
    if (this.isInitialized) return;

    this.loadUserLifecycleState();

    if (!this.sessionId) {
      this.createNewSession();
    }
    
    window.globalBehavioralTrackerInstance = this;
    localStorage.removeItem('behavioral_session_id');
    localStorage.removeItem('behavioral_data');

    this.createNewSession();

    this.collectDeviceFingerprint();

    this.startGlobalTracking();

    this.setupPeriodicSaving();

    this.setupUnloadHandler();

    this.setupNavigationDetection();


    this.startImmediateBaselineCollection();

    this.isInitialized = true;
  }

  loadSession() {
    try {
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

    

    if (this.baselineTimerId) {
      clearTimeout(this.baselineTimerId);
      this.baselineTimerId = null;
    }
    window.globalBehavioralTrackerInstance = this;


    if (this.backendIntervalId) {
      clearInterval(this.backendIntervalId);
      this.backendIntervalId = null;
    }

    localStorage.setItem(this.SESSION_KEY, this.sessionId);
    this.saveToStorage();

    console.log('🔄 Complete fresh behavioral session created:', this.sessionId);
    console.log('🧹 All behavioral data has been reset for new session');
  }

  handleUserSignup(userId, signupData = {}) {
    console.log('📝 USER SIGNUP: Starting behavioral tracking for new user');
    
    this.userId = userId;
    this.userLifecycleState = 'signed_up';
    this.signupTimestamp = Date.now();
    
    // Update behavioral data
    this.behavioralData.userId = userId;
    this.behavioralData.userLifecycleState = 'signed_up';
    this.behavioralData.signupTimestamp = this.signupTimestamp;
    this.behavioralData.trackingStartTime = this.signupTimestamp;
    
    // Start global tracking immediately after signup
    this.startGlobalTracking();
    this.setupPeriodicSaving();
    
    // Save lifecycle state
    this.saveUserLifecycleState();
    
    console.log('✅ Behavioral tracking started for new user:', userId);
    console.log('⏰ Tracking start time:', new Date(this.signupTimestamp).toLocaleString());
    
    // Emit signup event
    window.dispatchEvent(new CustomEvent('userSignupTracking', {
      detail: {
        userId: this.userId,
        sessionId: this.sessionId,
        signupTimestamp: this.signupTimestamp,
        signupData: signupData
      }
    }));
    
    return {
      userId: this.userId,
      sessionId: this.sessionId,
      trackingStarted: true,
      state: this.userLifecycleState
    };
  }

 handleDashboardEntry(userId) {
  console.log('🏠 DASHBOARD ENTRY: User entered main dashboard - starting immediate transmission');
  
  if (this.userId && this.userId !== userId) {
    console.warn('⚠️ User ID mismatch during dashboard entry');
  }
  
  this.userId = userId;
  this.userLifecycleState = 'logged_in';
  this.loginTimestamp = Date.now();
  this.dashboardEntryTime = Date.now();
  
  this.behavioralData.userId = userId;
  this.behavioralData.userLifecycleState = 'logged_in';
  this.behavioralData.loginTimestamp = this.loginTimestamp;
  this.behavioralData.dashboardEntryTime = this.dashboardEntryTime;
  this.behavioralData.baselineCollectionActive = true;
  
  this.resetBehavioralArraysForBaseline();
  
  if (!this.isTracking) {
    this.startGlobalTracking();
    this.setupPeriodicSaving();
  }
  
  // START IMMEDIATE TRANSMISSION - NO 20 SECOND WAIT
  this.startContinuousTransmission();
  
  this.saveUserLifecycleState();
  
  window.dispatchEvent(new CustomEvent('dashboardEntryTracking', {
    detail: {
      userId: this.userId,
      sessionId: this.sessionId,
      dashboardEntryTime: this.dashboardEntryTime,
      immediateTransmission: true
    }
  }));
  
  return {
    userId: this.userId,
    sessionId: this.sessionId,
    transmissionStarted: true,
    state: this.userLifecycleState
  };
}


  handleUserLogout() {
    console.log('🚪 USER LOGOUT: Finalizing baseline behavior collection');
    
    this.logoutTimestamp = Date.now();
    this.userLifecycleState = 'baseline_complete';
    
    // Update behavioral data
    this.behavioralData.logoutTimestamp = this.logoutTimestamp;
    this.behavioralData.userLifecycleState = 'baseline_complete';
    this.behavioralData.baselineCollectionActive = false;
    
    // Calculate total baseline duration
    const baselineDuration = this.dashboardEntryTime ? 
      (this.logoutTimestamp - this.dashboardEntryTime) : 
      (this.logoutTimestamp - this.signupTimestamp);
    
    console.log('📊 Baseline behavior collection completed');
    console.log('⏱️ Total baseline duration:', (baselineDuration / 1000 / 60).toFixed(2), 'minutes');
    console.log('🎯 Total actions captured:', this.behavioralData.actionCount);
    
    // Send final baseline data to backend
    this.sendImmediateBaselineToBackend().then((result) => {
      console.log('✅ Final baseline data sent to backend');
      
      // Emit logout event
      window.dispatchEvent(new CustomEvent('userLogoutTracking', {
        detail: {
          userId: this.userId,
          sessionId: this.sessionId,
          logoutTimestamp: this.logoutTimestamp,
          baselineDuration: baselineDuration,
          totalActions: this.behavioralData.actionCount,
          baselineData: this.getBehavioralData(),
          backendResult: result
        }
      }));
    }).catch((error) => {
      console.error('❌ Failed to send final baseline data:', error);
      
      // Emit logout event with error
      window.dispatchEvent(new CustomEvent('userLogoutTracking', {
        detail: {
          userId: this.userId,
          sessionId: this.sessionId,
          logoutTimestamp: this.logoutTimestamp,
          baselineDuration: baselineDuration,
          totalActions: this.behavioralData.actionCount,
          error: error.message
        }
      }));
    });
    
    // Stop tracking and transmission
    this.stopTracking();
    this.stopContinuousTransmission();
    
    // Save final lifecycle state
    this.saveUserLifecycleState();
    
    return {
      userId: this.userId,
      sessionId: this.sessionId,
      baselineCompleted: true,
      baselineDuration: baselineDuration,
      totalActions: this.behavioralData.actionCount,
      state: this.userLifecycleState
    };
  }

  resetBehavioralArraysForBaseline() {
    console.log('🔄 Resetting behavioral arrays for baseline collection');
    
    // Reset all behavioral tracking arrays
    this.behavioralData.cursorMovements = [];
    this.behavioralData.cursorSpeeds = [];
    this.behavioralData.cursorAcceleration = [];
    this.behavioralData.cursorCurvature = [];
    this.behavioralData.cursorAngles = [];
    this.behavioralData.keyPressTimes = [];
    this.behavioralData.keyHoldTimes = [];
    this.behavioralData.clickTimestamps = [];
    this.behavioralData.scrollSpeeds = [];
    this.behavioralData.mouseJitter = [];
    this.behavioralData.microPauses = [];
    this.behavioralData.hesitationTimes = [];
    this.behavioralData.suspiciousPatterns = [];
    
    // Reset counters
    this.behavioralData.scrollChanges = 0;
    this.behavioralData.idleTime = 0;
    this.behavioralData.actionCount = 0;
    this.behavioralData.TabKeyCount = 0;
    
    // Reset flags
    this.behavioralData.pasteDetected = false;
    
    // Reset timing
    this.behavioralData.lastActionTime = Date.now();
    this.behavioralData.lastUpdateTime = Date.now();
    
    console.log('✅ Behavioral arrays reset for fresh baseline collection');
  }

  saveUserLifecycleState() {
    const lifecycleState = {
      userId: this.userId,
      sessionId: this.sessionId,
      userLifecycleState: this.userLifecycleState,
      signupTimestamp: this.signupTimestamp,
      loginTimestamp: this.loginTimestamp,
      dashboardEntryTime: this.dashboardEntryTime,
      logoutTimestamp: this.logoutTimestamp,
      savedAt: Date.now()
    };
    
    try {
      localStorage.setItem(this.USER_LIFECYCLE_KEY, JSON.stringify(lifecycleState));
    } catch (error) {
      console.error('Error saving lifecycle state:', error);
    }
  }

  loadUserLifecycleState() {
    try {
      const saved = localStorage.getItem(this.USER_LIFECYCLE_KEY);
      if (saved) {
        const lifecycleState = JSON.parse(saved);
        
        this.userId = lifecycleState.userId;
        this.sessionId = lifecycleState.sessionId;
        this.userLifecycleState = lifecycleState.userLifecycleState;
        this.signupTimestamp = lifecycleState.signupTimestamp;
        this.loginTimestamp = lifecycleState.loginTimestamp;
        this.dashboardEntryTime = lifecycleState.dashboardEntryTime;
        this.logoutTimestamp = lifecycleState.logoutTimestamp;
        
        // Update behavioral data with loaded state
        this.behavioralData.userId = this.userId;
        this.behavioralData.sessionId = this.sessionId;
        this.behavioralData.userLifecycleState = this.userLifecycleState;
        this.behavioralData.signupTimestamp = this.signupTimestamp;
        this.behavioralData.loginTimestamp = this.loginTimestamp;
        this.behavioralData.dashboardEntryTime = this.dashboardEntryTime;
        this.behavioralData.logoutTimestamp = this.logoutTimestamp;
        
        console.log('📁 Loaded lifecycle state:', lifecycleState.userLifecycleState);
      }
    } catch (error) {
      console.error('Error loading lifecycle state:', error);
    }
  }

  getUserLifecycleInfo() {
    return {
      userId: this.userId,
      sessionId: this.sessionId,
      state: this.userLifecycleState,
      signupTimestamp: this.signupTimestamp,
      loginTimestamp: this.loginTimestamp,
      dashboardEntryTime: this.dashboardEntryTime,
      logoutTimestamp: this.logoutTimestamp,
      isBaselineActive: this.behavioralData.baselineCollectionActive,
      trackingDuration: this.dashboardEntryTime ? 
        (Date.now() - this.dashboardEntryTime) : 
        (this.signupTimestamp ? (Date.now() - this.signupTimestamp) : 0),
      totalActions: this.behavioralData.actionCount
    };
  }
  

  saveSession() {
    this.saveToStorage();
  }

  forceResetSession() {

    localStorage.removeItem(this.SESSION_KEY);
    localStorage.removeItem(this.STORAGE_KEY);

    if (this.backendIntervalId) {
      clearInterval(this.backendIntervalId);
      this.backendIntervalId = null;
    }
  }


  ensureArraysInitialized() {
    const requiredArrays = [
      'cursorMovements', 'cursorSpeeds', 'cursorAcceleration', 'cursorCurvature',
      'keyPressTimes', 'keyHoldTimes', 'clickTimestamps', 'scrollSpeeds',
      'mouseJitter', 'microPauses', 'hesitationTimes', 'keyboardPatterns', 'suspiciousPatterns'
    ];

    requiredArrays.forEach(arrayName => {
      if (!Array.isArray(this.behavioralData[arrayName])) {
        this.behavioralData[arrayName] = [];
        console.warn(`🛡️ Initialized missing array: ${arrayName}`);
      }
    });

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

    const array = new Uint8Array(16);
    if (window.crypto && window.crypto.getRandomValues) {
      window.crypto.getRandomValues(array);
    } else {
      for (let i = 0; i < array.length; i++) {
        array[i] = Math.floor(Math.random() * 256);
      }
    }

    const randomString = Array.from(array, byte => byte.toString(36).padStart(2, '0')).join('').substring(0, 12);

    const userAgent = navigator.userAgent || '';
    const screen = `${window.screen.width}x${window.screen.height}`;
    const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    const language = navigator.language || 'en';

    const browserData = `${userAgent}${screen}${timezone}${language}`;
    let fingerprint = 0;
    for (let i = 0; i < browserData.length; i++) {
      fingerprint = ((fingerprint << 5) - fingerprint + browserData.charCodeAt(i)) & 0xffffffff;
    }
    const fingerprintHex = Math.abs(fingerprint).toString(36).substring(0, 8);

    const performanceNow = performance.now().toString().replace('.', '');
    const entropy = performanceNow.substring(-6) + Math.random().toString(36).substring(2, 8);

    return `${timestamp}-${randomString}-${fingerprintHex}-${entropy}`;
  }

  startGlobalTracking() {
    if (this.isTracking) return;

    this.isTracking = true;

    const handleMouseMove = (event) => {
      this.trackMouseMovement(event);
    };

    const handleKeyDown = (event) => {
      this.trackKeyDown(event);
    };

    const handleKeyUp = (event) => {
      this.trackKeyUp(event);
    };

    const handleClick = (event) => {
      this.trackClick(event);
    };

    const handleScroll = (event) => {
      this.trackScroll(event);
    };

    const handlePaste = (event) => {
      this.trackPaste(event);
    };

    this.addEventListener(document, 'mousemove', handleMouseMove);
    this.addEventListener(document, 'keydown', handleKeyDown);
    this.addEventListener(document, 'keyup', handleKeyUp);
    this.addEventListener(document, 'click', handleClick);
    this.addEventListener(window, 'scroll', handleScroll);
    this.addEventListener(document, 'paste', handlePaste);

  }

  addEventListeners() {
    // Mouse movement tracking
    const handleMouseMove = (event) => this.trackMouseMove(event);
    document.addEventListener('mousemove', handleMouseMove, { passive: true });
    this.eventListeners.push({ element: document, event: 'mousemove', handler: handleMouseMove });
    
    // Keyboard tracking
    const handleKeyDown = (event) => this.trackKeyDown(event);
    const handleKeyUp = (event) => this.trackKeyUp(event);
    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('keyup', handleKeyUp);
    this.eventListeners.push({ element: document, event: 'keydown', handler: handleKeyDown });
    this.eventListeners.push({ element: document, event: 'keyup', handler: handleKeyUp });
    
    // Click tracking
    const handleClick = (event) => this.trackClick(event);
    document.addEventListener('click', handleClick, true);
    this.eventListeners.push({ element: document, event: 'click', handler: handleClick });
    
    // Scroll tracking
    const handleScroll = (event) => this.trackScroll(event);
    window.addEventListener('scroll', handleScroll, { passive: true });
    this.eventListeners.push({ element: window, event: 'scroll', handler: handleScroll });
    
    // Paste tracking
    const handlePaste = (event) => this.trackPaste(event);
    document.addEventListener('paste', handlePaste);
    this.eventListeners.push({ element: document, event: 'paste', handler: handlePaste });
    
    console.log('👂 Event listeners added for behavioral tracking');
  }

  stopTracking() {
    if (!this.isTracking) return;

    console.log('🛑 Stopping behavioral tracking...');

    this.eventListeners.forEach(({ element, event, handler }) => {
      try {
        element.removeEventListener(event, handler);
      } catch (error) {
        console.warn('Warning removing event listener:', error);
      }
    });

    this.eventListeners = [];

    if (this.urlCheckInterval) {
      clearInterval(this.urlCheckInterval);
      this.urlCheckInterval = null;
    }

    if (this.saveIntervalId) {
      clearInterval(this.saveIntervalId);
      this.saveIntervalId = null;
    }

    this.isTracking = false;

  }

  addEventListener(element, event, handler) {
    element.addEventListener(event, handler);
    this.eventListeners.push({ element, event, handler });
  }

  collectDeviceFingerprint() {
    try {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      ctx.textBaseline = 'top';
      ctx.font = '14px Arial';
      ctx.fillText('Device fingerprint test 🎯', 2, 2);
      const canvasFingerprint = canvas.toDataURL();

      this.behavioralData.deviceFingerprint = this.createHashFromString(
        navigator.userAgent + window.screen.width + window.screen.height + canvasFingerprint
      );

      this.behavioralData.canvasMetrics = {
        winding: ctx.isPointInPath ? 'supported' : 'not_supported',
        geometryLength: canvasFingerprint.length,
        textLength: navigator.userAgent.length,
        canvasFingerprint: canvasFingerprint.substring(0, 100) // First 100 chars
      };

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

      const screenInfo = {
        width_height: `${window.screen.width}x${window.screen.height}`,
        inner_width: window.innerWidth,
        device_pixel_ratio: window.devicePixelRatio || 1,
        aspect_ratio: (window.screen.width / window.screen.height).toFixed(2)
      };

      const commonResolutions = ['1920x1080', '1366x768', '1536x864', '1440x900', '1280x720'];
      const isUnusual = !commonResolutions.includes(screenInfo.width_height);

      this.behavioralData.unusualScreenResolution = {
        ...screenInfo,
        is_unusual: isUnusual,
        spoofedMismatch: Math.abs(window.innerWidth - window.screen.width) > 100, // Detect potential spoofing
        aspectRatio: parseFloat(screenInfo.aspect_ratio)
      };

      this.behavioralData.evasionSignals = {
        webdriver: navigator.webdriver || false,
        automation: window.chrome && window.chrome.runtime && window.chrome.runtime.onConnect,
        phantom: window.callPhantom || window._phantom,
        selenium: window.selenium || document.$cdc_asdjflasutopfhvcZLmcfl_,

        languages_mismatch: navigator.language !== navigator.languages[0],
        plugins_empty: navigator.plugins.length === 0,
        webgl_disabled: !gl,

        performance_now_precision: performance.now() % 1 === 0, // Perfect milliseconds = suspicious

        headless_chrome: navigator.userAgent.includes('HeadlessChrome'),
        automation_keywords: /PhantomJS|Selenium|WebDriver|ChromeDriver/.test(navigator.userAgent)
      };

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
        lastKeyPress: null,
        lastMouseMove: null,
        lastClick: null,
        pageLoadTime: performance.timing ?
          (performance.timing.loadEventEnd - performance.timing.navigationStart) : 1200,
        timeToFirstClick: 0 
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



  createHashFromString(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; 
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



    this.ensureArraysInitialized();
    

    const previousLastUpdateTime = this.behavioralData.lastUpdateTime;
    this.behavioralData.lastUpdateTime = now;

    if (this.behavioralData.isCollectingBaseline) {
      this.recordBaselineEvent('mouseMove', event, now);
    }

    const timeSinceLastUpdate = now - this.behavioralData.lastUpdateTime;
    let isThrottled = false;

    if (timeSinceLastUpdate < 50) {
      isThrottled = true;
    if (this.behavioralData.lastMouseMove) {
        const dx = newPoint.x - this.behavioralData.lastMouseMove.x;
        const dy = newPoint.y - this.behavioralData.lastMouseMove.y;
        const dt = (timeSinceLastUpdate / 1000);
        
        if (dt > 0) {
          const distance = Math.sqrt(dx * dx + dy * dy);
          const speed = distance / dt;
          
          if (distance < 10 && speed > 50 && timeSinceLastUpdate < 100) {
            console.log('Throttled jitter detected:', { distance, speed, dt: timeSinceLastUpdate });
            this.behavioralData.mouseJitter.push({
              timestamp: now,
              distance: distance,
              speed: speed,
              coordinates: {x: newPoint.x, y: newPoint.y},
              type: 'throttled_jitter'
            });
          }
        }
      }
    }

    if (previousLastUpdateTime) {
      const timeSinceLastUpdate = now - previousLastUpdateTime;
      
      console.log('🕰️ Checking for hesitation/micropause:', { 
        timeSinceLastUpdate, 
        isThrottled, 
        previousLastUpdateTime: previousLastUpdateTime,
        lastMouseMove: this.behavioralData.lastMouseMove 
      });

      if (timeSinceLastUpdate > 200 && timeSinceLastUpdate < 2000) {
        console.log('✅ Hesitation detected:', { duration: timeSinceLastUpdate, timestamp: now });
        console.log('Before push - hesitationTimes length:', this.behavioralData.hesitationTimes?.length || 0);
        this.behavioralData.hesitationTimes.push({
          duration: timeSinceLastUpdate,
          timestamp: now,
          beforeAction: 'mouseMove'
        });
        console.log('After push - hesitationTimes length:', this.behavioralData.hesitationTimes?.length || 0);
        console.log('Current hesitationTimes array:', this.behavioralData.hesitationTimes);
      }

      if (timeSinceLastUpdate > 50 && timeSinceLastUpdate < 200) {
        console.log('✅ Micropause detected:', { duration: timeSinceLastUpdate, timestamp: now });
        console.log('Before push - microPauses length:', this.behavioralData.microPauses?.length || 0);
        this.behavioralData.microPauses.push({
          duration: timeSinceLastUpdate,
          timestamp: now,
          beforeAction: 'mouseMove'
        });
        console.log('After push - microPauses length:', this.behavioralData.microPauses?.length || 0);
        console.log('Current microPauses array:', this.behavioralData.microPauses);
      }
    } else {
      console.log('⚠️ No previousLastUpdateTime available for hesitation/micropause detection');
    }

    this.behavioralData.cursorMovements = [
      ...this.behavioralData.cursorMovements.slice(-499), 
      newPoint
    ];

    if (this.behavioralData.lastMouseMove) {
      const dx = newPoint.x - this.behavioralData.lastMouseMove.x;
      const dy = newPoint.y - this.behavioralData.lastMouseMove.y;
      const dt = (now - this.behavioralData.lastMouseMove.timestamp) / 1000;

      if (dt > 0) {
        const distance = Math.sqrt(dx * dx + dy * dy);
        const speed = distance / dt;

        console.log('Mouse movement metrics:', { distance, speed, dt });

        if (speed > 0 && speed < 5000) { 
          this.behavioralData.cursorSpeeds = [
            ...this.behavioralData.cursorSpeeds.slice(-99),
            speed
          ];
          this.behavioralData.latestSpeed = speed;

          if (this.behavioralData.cursorSpeeds.length > 1) {
            const prevSpeed = this.behavioralData.cursorSpeeds[this.behavioralData.cursorSpeeds.length - 2];
            const acceleration = (speed - prevSpeed) / dt;
            this.behavioralData.cursorAcceleration.push(acceleration);
          }

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

          if (distance < 8 && speed > 80) {
            console.log('Classic jitter detected:', { distance, speed, coordinates: { x: newPoint.x, y: newPoint.y } });
            this.behavioralData.mouseJitter.push({
              timestamp: now,
              distance: distance,
              speed: speed,
              coordinates: {x: newPoint.x, y: newPoint.y},
              type: 'classic_jitter'
            });
          }
          
          if (distance < 3 && speed > 30) {
            console.log('Micro-jitter detected:', { distance, speed, coordinates: { x: newPoint.x, y: newPoint.y } });
            this.behavioralData.mouseJitter.push({
              timestamp: now,
              distance: distance,
              speed: speed,
              coordinates: {x: newPoint.x, y: newPoint.y},
              type: 'micro_jitter'
            });
          }
          
          if (this.behavioralData.cursorMovements.length > 3) {
            const prevMovement = this.behavioralData.cursorMovements[this.behavioralData.cursorMovements.length - 2];
            const prevPrevMovement = this.behavioralData.cursorMovements[this.behavioralData.cursorMovements.length - 3];
            
            if (prevMovement && prevPrevMovement) {
              const prevDx = prevMovement.x - prevPrevMovement.x;
              const prevDy = prevMovement.y - prevPrevMovement.y;
              const prevDistance = Math.sqrt(prevDx * prevDx + prevDy * prevDy);
              
              const directionChange = Math.abs(dx * prevDx + dy * prevDy);
              if (directionChange < 0 && distance < 6 && prevDistance < 6 && speed > 60) {
                console.log('Direction reversal jitter detected:', { distance, speed, directionChange });
                this.behavioralData.mouseJitter.push({
                  timestamp: now,
                  distance: distance,
                  speed: speed,
                  coordinates: {x: newPoint.x, y: newPoint.y},
                  type: 'direction_reversal_jitter',
                  directionChange: directionChange
                });
              }
            }
          }
        }
      }
    }

    this.behavioralData.timingMetrics.lastMouseMove = now;
    this.behavioralData.timingMetrics.mouseMovementFrequency = 
      (this.behavioralData.timingMetrics.mouseMovementFrequency || 0) + 1;

    this.behavioralData.lastMouseMove = newPoint;
    this.behavioralData.actionCount++;
    this.behavioralData.lastActionTime = now;
  }

  trackKeyDown(event) {
    const now = Date.now();
    
    this.behavioralData.lastKeyDown[event.key] = now;
    
    this.behavioralData.keyPressTimes = [
      ...this.behavioralData.keyPressTimes.slice(-99),
      now
    ];
    
    if (this.behavioralData.lastKeyPress) {
      const timeSinceLastKeyPress = now - this.behavioralData.lastKeyPress;
      
      if (timeSinceLastKeyPress > 50 && timeSinceLastKeyPress < 200) {
        console.log('✅ Keyboard micropause detected:', { duration: timeSinceLastKeyPress, timestamp: now, key: event.key });
        console.log('Before push - microPauses length:', this.behavioralData.microPauses?.length || 0);
        this.behavioralData.microPauses.push({
          duration: timeSinceLastKeyPress,
          timestamp: now,
          beforeAction: 'keyPress',
          key: event.key
        });
        console.log('After push - microPauses length:', this.behavioralData.microPauses?.length || 0);
        console.log('Current microPauses array:', this.behavioralData.microPauses);
      }
    }
    
    this.behavioralData.timingMetrics.lastKeyPress = now;
    this.behavioralData.timingMetrics.keyPressFrequency = 
      (this.behavioralData.timingMetrics.keyPressFrequency || 0) + 1;
    
    this.behavioralData.lastKeyPress = now;
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

    if (this.behavioralData.timingMetrics.timeToFirstClick === 0) {
      this.behavioralData.timingMetrics.timeToFirstClick = now - this.behavioralData.trackingStartTime;
    }

    if (this.behavioralData.isCollectingBaseline) {
      this.recordBaselineEvent('click', event, now);
    }

    if (this.behavioralData.lastClickTime) {
      const timeSinceLastClick = now - this.behavioralData.lastClickTime;
      
      console.log('🕰️ Checking for click hesitation and micropause:', { timeSinceLastClick, lastClickTime: this.behavioralData.lastClickTime });

      if (timeSinceLastClick > 500 && timeSinceLastClick < 5000) {
        console.log('✅ Click hesitation detected:', { duration: timeSinceLastClick, timestamp: now });
        console.log('Before push - hesitationTimes length:', this.behavioralData.hesitationTimes?.length || 0);
        this.behavioralData.hesitationTimes.push({
          duration: timeSinceLastClick,
          timestamp: now,
          beforeAction: 'click',
          coordinates: { x: event.clientX, y: event.clientY }
        });
        console.log('After push - hesitationTimes length:', this.behavioralData.hesitationTimes?.length || 0);
        console.log('Current hesitationTimes array:', this.behavioralData.hesitationTimes);
      }
      
      if (timeSinceLastClick > 50 && timeSinceLastClick < 200) {
        console.log('✅ Click micropause detected:', { duration: timeSinceLastClick, timestamp: now });
        console.log('Before push - microPauses length:', this.behavioralData.microPauses?.length || 0);
        this.behavioralData.microPauses.push({
          duration: timeSinceLastClick,
          timestamp: now,
          beforeAction: 'click',
          coordinates: { x: event.clientX, y: event.clientY }
        });
        console.log('After push - microPauses length:', this.behavioralData.microPauses?.length || 0);
        console.log('Current microPauses array:', this.behavioralData.microPauses);
      }
    } else {
      console.log('⚠️ No lastClickTime available for click hesitation/micropause detection');
    }

    this.behavioralData.clickTimestamps = [
      ...this.behavioralData.clickTimestamps.slice(-99),
      now
    ];

    if (this.behavioralData.lastClickTime) {
      const interval = now - this.behavioralData.lastClickTime;
      this.behavioralData.clickTimes = [
        ...this.behavioralData.clickTimes.slice(-99),
        interval
      ];

      if (this.behavioralData.clickTimes.length > 3) {
        const recentIntervals = this.behavioralData.clickTimes.slice(-5);
        const avgInterval = recentIntervals.reduce((sum, int) => sum + int, 0) / recentIntervals.length;
        const variance = recentIntervals.reduce((sum, int) => sum + Math.pow(int - avgInterval, 2), 0) / recentIntervals.length;

        if (variance < 50 && avgInterval < 1000) {
          this.behavioralData.suspiciousPatterns.push({
            type: 'mechanical_clicking',
            timestamp: now,
            metrics: { avgInterval, variance }
          });
        }
      }
    }

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

    if (this.behavioralData.isCollectingBaseline) {
      this.recordBaselineEvent('scroll', event, now);
    }

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


  updateCrossPageMetrics() {

    const now = Date.now();
    if (this.behavioralData.timingMetrics) {
      this.behavioralData.timingMetrics.lastUpdateTime = now;
    }

  }

  setupPeriodicSaving() {
    setInterval(() => {
      this.saveToStorage();
    }, this.saveInterval);

  }

  saveToStorage() {
    try {
      this.updateCrossPageMetrics();


      const now = Date.now();
      const timeSinceLastAction = now - this.behavioralData.lastActionTime;

      if (timeSinceLastAction > 2000) {
        this.behavioralData.idleTime += Math.min(timeSinceLastAction, 30000); 
      }

      if (this.behavioralData.timingMetrics) {
        this.behavioralData.timingMetrics.lastUpdateTime = now;
      }

      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.behavioralData));
      this.lastSaveTime = Date.now();

    } catch (error) {
      console.error('Error saving behavioral data:', error);
    }
  }

  async sendToBackend() {
  try {
    console.log('📊 DEBUG: sendToBackend called', {
      timestamp: new Date().toISOString(),
      sessionId: this.sessionId,
      backendIntervalId: this.backendIntervalId
    });

    // REMOVED: Baseline collection checks - now sends data immediately
    
    const rollingWindowData = this.createRollingWindows();
    const convertedBehavioralData = this.convertToBackendFormat();

    console.log('📤 Sending behavioral payload to backend...', {
      sessionId: this.sessionId,
      dataPoints: Object.keys(convertedBehavioralData).length,
      actionCount: convertedBehavioralData.action_count,
      rollingWindows: rollingWindowData.windows.length
    });

    const response = await fetch('http://127.0.0.1:8000/user/behavioral-analysis/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: this.sessionId,
        user_id: this.userId,
        signup_timestamp: this.signupTimestamp,
        dashboard_entry_time: this.dashboardEntryTime,
        logout_timestamp: this.logoutTimestamp,
        behavioral_data: {
          ...convertedBehavioralData,
          timestamp: Date.now(),
          currentPage: this.behavioralData.currentPage || 'unknown',
          rollingWindows: rollingWindowData.windows,
          windowMetadata: rollingWindowData.metadata,
          immediateMode: true // Flag to indicate immediate transmission
        }
      })
    });

    if (response.ok) {
      const result = await response.json();
      console.log('📊 Behavioral analysis result:', {
        status: result.user_auth_status,
        authorized: result.is_authorized,
        riskScore: result.risk_score,
        recommendation: result.recommendation
      });

      this.behavioralData.lastAnalysisResult = result;
      this.behavioralData.lastAnalysisTime = Date.now();

      if (!result.is_authorized) {
        console.warn('🚨 UNAUTHORIZED USER DETECTED!');
        this.showAuthenticationMessage(result.recommendation || 'Behavioral patterns do not match authorized user');
        this.handleUnauthorizedUser(result);
      }

      window.dispatchEvent(new CustomEvent('behavioralAnalysis', {
        detail: result
      }));
    } else {
      console.warn('Backend behavioral analysis failed:', response.status, response.statusText);
    }
  } catch (error) {
    console.warn('Could not send behavioral data to backend:', error.message);
  }
}

  async sendBaselineToBackend() {
    if (!this.userId) {
      throw new Error('No user ID available for baseline storage');
    }
    
    console.log('📤 Sending baseline behavior data to backend');
    
    try {
      const convertedData = this.convertToBackendFormat();
      
      const payload = {
        session_id: this.sessionId,
        user_id: this.userId,
        signup_timestamp: this.signupTimestamp,
        dashboard_entry_time: this.dashboardEntryTime,
        logout_timestamp: this.logoutTimestamp,
        baseline_duration: this.dashboardEntryTime ? 
          (this.logoutTimestamp - this.dashboardEntryTime) : 
          (this.logoutTimestamp - this.signupTimestamp),
        baseline_data: convertedData
      };
      
      const response = await fetch('http://127.0.0.1:8000/user/store-baseline-behavior/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
      });
      
      if (response.ok) {
        const result = await response.json();
        console.log('✅ Baseline data stored successfully');
        return result;
      } else {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }
    } catch (error) {
      console.error('❌ Failed to send baseline data:', error);
      throw error;
    }
  }

  convertToBackendFormat() {
    try {
      const totalTime = Date.now() - (this.behavioralData.trackingStartTime || Date.now());
      const clickIntervals = this.calculateClickIntervals();
      const suspiciousFeatureRatio = this.calculateSuspiciousFeatureRatio();
      const averageSpeed = this.calculateAverageSpeed();
      const maxSpeed = this.calculateMaxSpeed();
      const cursorAngleVariance = this.calculateCursorAngleVariance();
      const cursorEntropy = this.calculateCursorEntropy();

      const keyboardPatterns = this.analyzeKeyboardPatterns();
      const suspiciousPatterns = this.detectSuspiciousPatterns();
      const humanIndicators = this.detectHumanIndicators();
      const botIndicators = this.detectBotIndicators();

      const humanScore = this.calculateHumanScore();
      const botScore = 1 - humanScore;

      const isAutomatedBrowser = this.detectAutomatedBrowser();
      const evasionSignals = this.detectEvasionSignals();

      const deviceFingerprint = this.generateDeviceFingerprint();
      const canvasMetrics = this.getCanvasMetrics();
      const gpuInfo = this.getGPUInfo();
      const screenResolution = this.getScreenResolution();

      const backendData = {
        cursor_movements: (this.behavioralData.cursorMovements || []).map(point => ({ x: point.x, y: point.y, timestamp: Date.now() })),
        key_press_times: this.behavioralData.keyPressTimes || [],
        key_hold_times: this.behavioralData.keyHoldTimes || [],
        click_timestamps: this.behavioralData.clickTimestamps || [],
        click_intervals: clickIntervals,
        cursor_speeds: this.behavioralData.cursorSpeeds || [],
        cursor_acceleration: this.behavioralData.cursorAcceleration || [],
        cursor_curvature: this.behavioralData.cursorCurvature || [],

        paste_detected: this.behavioralData.pasteDetected || false,
        total_time: Math.floor(totalTime),

        classification: humanScore > 0.6 ? "Human" : (botScore > 0.6 ? "Bot" : "Unknown"),
        human_score: parseFloat(humanScore.toFixed(2)),
        bot_score: parseFloat(botScore.toFixed(2)),

        human_indicators: humanIndicators,
        bot_indicators: botIndicators,

        bot_fingerprint_score: parseFloat((botScore * 0.1).toFixed(2)),
        suspicious_flag: suspiciousPatterns.length > 0 || botScore > 0.7,
        suspicious_feature_ratio: parseFloat(suspiciousFeatureRatio.toFixed(2)),

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

        action_count: this.behavioralData.actionCount || 0,
        is_automated_browser: isAutomatedBrowser,
        cursor_entropy: parseFloat(cursorEntropy.toFixed(2)),
        scroll_speeds: this.behavioralData.scrollSpeeds || [],
        scroll_changes: this.behavioralData.scrollChanges || 0,
        idle_time: this.behavioralData.idleTime || 0,

        honeypot_value: this.behavioralData.honeypotValue || "",
        tabkeycount: this.behavioralData.TabKeyCount || 0,
        cursorAngleVariance: parseFloat(cursorAngleVariance.toFixed(3)),
        mouseJitter: (() => {
          const jitter = this.behavioralData.mouseJitter || [];
          console.log('🔍 Processing mouseJitter for backend:', {
            originalLength: jitter.length,
            jitterData: jitter,
            mappedData: jitter.map(j => parseFloat((j.distance || 0).toFixed(3)))
          });
          return jitter.map(j => parseFloat((j.distance || 0).toFixed(3)));
        })(),
        micropause: (() => {
          const micropauses = this.behavioralData.microPauses || [];
          console.log('🔍 Processing microPauses for backend:', {
            originalLength: micropauses.length,
            micropauseData: micropauses,
            mappedData: micropauses.map(p => p.duration || 0)
          });
          return micropauses.map(p => p.duration || 0);
        })(),
        hesitation: (() => {
          const hesitations = this.behavioralData.hesitationTimes || [];
          console.log('🔍 Processing hesitationTimes for backend:', {
            originalLength: hesitations.length,
            hesitationData: hesitations,
            mappedData: hesitations.map(h => h.duration || 0)
          });
          return hesitations.map(h => h.duration || 0);
        })(),

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
    // Simplified keyboard pattern analysis - only essential patterns
    const patterns = [];
    const keyTimes = this.behavioralData.keyPressTimes || [];

    if (keyTimes.length > 1) {
      // Basic typing rhythm analysis
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
    }

    return patterns;
  }

  detectSuspiciousPatterns() {
    // Simplified suspicious pattern detection - only essential patterns
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

    return patterns;
  }

  detectHumanIndicators() {
    const indicators = [];

    // Natural hesitation
    const hesitations = this.behavioralData.hesitationTimes || [];
    if (hesitations.length > 0) {
      indicators.push("natural_hesitation");
    }

    
    const movements = this.behavioralData.cursorMovements || [];
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
      }
    });

    return indicators;
  }

  calculateHumanScore() {
    let score = 0.5; 

    const humanIndicators = this.detectHumanIndicators();
    const botIndicators = this.detectBotIndicators();

    score += humanIndicators.length * 0.1;

    score -= botIndicators.length * 0.15;

    return Math.max(0, Math.min(1, score));
  }

  detectAutomatedBrowser() {
    const botIndicators = this.detectBotIndicators();
    const suspiciousPatterns = this.detectSuspiciousPatterns();

    const hasWebDriver = navigator.webdriver || window.webdriver;

    return hasWebDriver || botIndicators.length > 2 || suspiciousPatterns.length > 3;
  }

  detectEvasionSignals() {
    return {
      headless_mode: navigator.webdriver === true,
      webdriver_detected: !!navigator.webdriver
    };
  }

  generateDeviceFingerprint() {
    const components = [
      navigator.userAgent,
      window.screen.width + 'x' + window.screen.height,
      navigator.platform
    ];

    let hash = 0;
    const str = components.join('|');
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; 
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
      this.updateCrossPageMetrics();
      this.saveToLocalStorage();
    };

    window.addEventListener('beforeunload', handleUnload);
    window.addEventListener('pagehide', handleUnload);
  }

  setupNavigationDetection() {
    console.log('🌐 Setting up navigation detection for URL changes...');

    this.currentUrl = window.location.href;
    this.lastNavigationTime = Date.now();

    const handlePopState = (event) => {
      console.log('🔄 POPSTATE detected - URL changed manually or via browser navigation');
      this.handleUrlChange('popstate', window.location.href);
    };

    const handleHashChange = (event) => {
      console.log('🔄 HASHCHANGE detected - Fragment identifier changed');
      this.handleUrlChange('hashchange', window.location.href);
    };

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

    this.urlCheckInterval = setInterval(() => {
      const currentUrl = window.location.href;
      if (currentUrl !== this.currentUrl) {
        console.log('🔄 URL CHANGE detected via periodic check');
        console.log(`Previous: ${this.currentUrl}`);
        console.log(`Current: ${currentUrl}`);
        this.handleUrlChange('manual_check', currentUrl);
      }
    }, 500); 

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

  }

  handleDashboardEntryImmediate(userId) {
  console.log('🏠 DASHBOARD ENTRY: Starting immediate behavioral transmission');
  
  this.userId = userId;
  this.userLifecycleState = 'logged_in';
  this.loginTimestamp = Date.now();
  this.dashboardEntryTime = Date.now();
  
  // Update behavioral data
  this.behavioralData.userId = userId;
  this.behavioralData.userLifecycleState = 'logged_in';
  this.behavioralData.loginTimestamp = this.loginTimestamp;
  this.behavioralData.dashboardEntryTime = this.dashboardEntryTime;

  
  
  // Reset arrays for fresh dashboard session
  this.resetBehavioralArraysForBaseline();
  
  // Ensure tracking is active
  if (!this.isTracking) {
    this.startGlobalTracking();
    this.setupPeriodicSaving();
  }
  
  // Start immediate continuous transmission - no delays
  this.startImmediateContinuousTransmission();
  
  this.saveUserLifecycleState();
  
  return {
    userId: this.userId,
    sessionId: this.sessionId,
    immediateTransmissionStarted: true,
    state: this.userLifecycleState
  };
}



startImmediateContinuousTransmission() {
  // Stop any existing transmission
  if (this.backendIntervalId) {
    clearInterval(this.backendIntervalId);
    this.backendIntervalId = null;
  }
  
  // Mark transmission as started
  this.behavioralData.continuousTransmissionStarted = true;
  
  console.log('🚀 Starting immediate continuous transmission on dashboard entry');
  
  // Send first payload immediately
  this.sendToBackend().then(() => {
    console.log('✅ First behavioral payload sent immediately');
  }).catch((error) => {
    console.warn('⚠️ First payload failed, continuing transmission:', error);
  });
  
  // Start continuous transmission every 1 second
  this.backendIntervalId = setInterval(() => {
    this.sendToBackend();
  }, this.backendInterval);
  
  console.log('✅ Immediate continuous transmission active (every 1 second)');
}

  handleUrlChange(changeType, newUrl) {
    try {
      const now = Date.now();
      const timeSinceLastNav = now - this.lastNavigationTime;

      const isDifferentPage = this.isDifferentPage(this.currentUrl, newUrl);
      const isSignificantNavigation = timeSinceLastNav > 1000;

      if (isDifferentPage && isSignificantNavigation) {
        console.log('🔄 RESETTING BEHAVIORAL DATA due to page navigation');
        this.resetBehavioralDataForNewPage(changeType, newUrl);
      } else {
        console.log('⏭️ Skipping reset - same page or rapid navigation');
      }

      this.currentUrl = newUrl;
      this.lastNavigationTime = now;

    } catch (error) {
      console.error('❌ Error handling URL change:', error);
    }
  }

  isDifferentPage(oldUrl, newUrl) {
    try {
      if (!oldUrl || !newUrl) return true;

      const oldParsed = new URL(oldUrl);
      const newParsed = new URL(newUrl);

      if (oldParsed.hostname !== newParsed.hostname) return true;

      if (oldParsed.pathname !== newParsed.pathname) return true;

      if (oldParsed.search !== newParsed.search) return true;

      return false;

    } catch (error) {
      console.error('❌ Error comparing URLs:', error);
      return true;
    }
  }

  resetBehavioralDataForNewPage(navigationType, newUrl) {
  try {
    console.log('🔄 RESETTING BEHAVIORAL DATA FOR NEW PAGE');

    const wasBackendTransmissionActive = this.backendIntervalId !== null;
    
    this.stopTracking();

    // Clear old data
    localStorage.removeItem('behavioral_data_auth_session');
    // ... other localStorage.removeItem calls ...

    // Reset behavioral arrays
    this.behavioralData.cursorMovements = [];
    this.behavioralData.cursorSpeeds = [];
    // ... other array resets ...

    this.behavioralData.actionCount = 0;
    this.behavioralData.currentPage = newUrl;
    this.behavioralData.pageLoadTime = Date.now();

    this.startGlobalTracking();
    this.setupPeriodicSaving();

    // START TRANSMISSION IMMEDIATELY - NO BASELINE WAIT
    if (this.userId && this.userLifecycleState === 'logged_in') {
      console.log('🚀 Starting immediate transmission for new page...');
      this.startContinuousTransmission();
    }

  } catch (error) {
    console.error('❌ Error resetting behavioral data:', error);
  }
}
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


  clearSession() {
    console.log('🧹 Starting session clear - resetting all behavioral data...');
    console.log('Before clear - microPauses length:', this.behavioralData.microPauses?.length || 0);
    console.log('Before clear - hesitationTimes length:', this.behavioralData.hesitationTimes?.length || 0);
    console.log('Before clear - mouseJitter length:', this.behavioralData.mouseJitter?.length || 0);
    
    this.removeAllEventListeners();

    if (this.backendIntervalId) {
      clearInterval(this.backendIntervalId);
      this.backendIntervalId = null;
      console.log('🛑 Cleared backend interval');
    }

    localStorage.removeItem(this.STORAGE_KEY);
    localStorage.removeItem(this.SESSION_KEY);

    this.behavioralData = {
      sessionId: null,
      trackingStartTime: null,
      pageLoadTime: null,

      isCollectingBaseline: false,
      baselineCollectionStartTime: null,
      baselineCompleted: false,
      baselineBehaviorData: null,

      cursorMovements: [],
      cursorSpeeds: [],
      cursorAcceleration: [],
      cursorCurvature: [],
      keyPressTimes: [],
      keyHoldTimes: [],
      clickTimestamps: [],
      scrollSpeeds: [],
      scrollChanges: 0,
      idleTime: 0,
      pasteDetected: false,
      lastKeyPress: null,
      lastKeyDown: {},
      lastMouseMove: null,
      lastClickTime: null,
      lastUpdateTime: Date.now(), 
      lastActionTime: Date.now(),
      actionCount: 0,
      mouseJitter: [],
      microPauses: [],
      hesitationTimes: [],
      keyboardPatterns: [],
      suspiciousPatterns: [],
      postPasteActivity: {
        keypressAfterPaste: 0
      },
      deviceFingerprint: null,
      canvasMetrics: {
        winding: null,
        geometryLength: 0,
        textLength: 0,
        hash: null
      },
      missingCanvasFingerprint: true,
      unusualScreenResolution: {
        width_height: "0x0",
        inner_width: 0,
        device_pixel_ratio: 0,
        is_unusual: false,
        spoofedMismatch: false,
        aspectRatio: 0,
      },
      gpuInfo: {
        vendor: 'Unknown',
        model: 'Unknown'
      },
      timingMetrics: {
        trackingStartTime: null,
        domContentLoaded: null,
        pageLoadComplete: null,
        navigationStart: null,
        firstPaint: null,
        mouseMovementFrequency: 0,
        keyPressFrequency: 0,
        clickFrequency: 0,
        pageLoadTime: null,
        timeToFirstClick: 0,
        lastKeyPress: null,
        lastMouseMove: null,
        lastClick: null
      },
      currentPage: null,
      honeypotValue: "",
      TabKeyCount: 0
    };

    this.isTracking = false;

  }

  forceResetSession() {
    console.log('🔄 Force resetting behavioral session...');
    this.clearSession();
    this.createNewSession();
    console.log('✅ Session force reset complete');
  }

  updateBehavioralData(updates) {
    this.behavioralData = { ...this.behavioralData, ...updates };
  }


   startImmediateBaselineCollection() {
  console.log('📊 Skipping baseline collection - starting immediate transmission');
  
  // Set baseline as immediately completed
  this.behavioralData.isCollectingBaseline = false;
  this.behavioralData.baselineCompleted = true;
  this.behavioralData.continuousTransmissionStarted = false;
  
  // Start transmission immediately without any delay
  this.startContinuousTransmission();
  
  return 0; // No duration, immediate start
}

  completeImmediateBaselineCollection() {
    if (!this.behavioralData.isCollectingBaseline) {
      console.log('⚠️ Baseline already completed or not collecting');
      return;
    }

    if (this.baselineTimerId) {
      clearTimeout(this.baselineTimerId);
      this.baselineTimerId = null;
    }
    this.behavioralData.baselineTimerId = null;

    this.behavioralData.isCollectingBaseline = false;
    this.behavioralData.baselineCompleted = true;
    this.behavioralData.baselineBehaviorData.collectionEndTime = Date.now();
    this.behavioralData.baselineBehaviorData.baselineQuality = 'completed';

    const collectionDuration = this.behavioralData.baselineBehaviorData.collectionEndTime -
      this.behavioralData.baselineBehaviorData.collectionStartTime;

    console.log(`⏰ IMMEDIATE BASELINE: Collection completed in ${collectionDuration / 1000} seconds`);
    console.log(`📊 Current page: ${this.behavioralData.currentPage || 'unknown'} (collection ran across all pages)`);

    localStorage.setItem('global_baseline_completed', JSON.stringify({
      completedAt: Date.now(),
      sessionId: this.sessionId,
      duration: collectionDuration,
      trigger: 'url_manual_entry_immediate',
      completedOnPage: this.behavioralData.currentPage || 'unknown'
    }));

    const baselineStats = this.validateImmediateBaselineData();
    this.behavioralData.baselineBehaviorData.naturalBehaviorScore = baselineStats.qualityScore;

    console.log(`📊 BASELINE QUALITY: Score ${baselineStats.qualityScore.toFixed(2)}, ${baselineStats.metrics.totalInteractions} total interactions`);

    this.sendImmediateBaselineToBackend().then((result) => {
      console.log('✅ IMMEDIATE BASELINE: Sent to backend successfully');
      console.log('🔄 READY: System now ready for continuous behavioral analysis');
      console.log('📡 STARTING CONTINUOUS TRANSMISSION: Now sending behavior data every 1 second');

      this.startContinuousTransmission();

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

      if (!this.backendIntervalId) {
        this.startContinuousTransmission();
        console.log('🚀 CONTINUOUS TRANSMISSION: Started despite baseline error');
      }

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

    let qualityScore = 0;
    if (metrics.totalInteractions > 0) qualityScore += 0.3;
    if (metrics.mouseMovements > 5) qualityScore += 0.3;
    if (metrics.keyPresses > 0) qualityScore += 0.2;
    if (metrics.clicks > 0) qualityScore += 0.2;


    return { qualityScore, metrics };
  }

  async sendImmediateBaselineToBackend() {
    const baselineData = this.behavioralData.baselineBehaviorData;
    if (!baselineData) {
      throw new Error('No baseline data to send');
    }


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

  completeBackgroundBaselineCollection() {
    if (!this.behavioralData.isCollectingBaseline) {
      return;
    }

    if (this.baselineTimerId) {
      clearTimeout(this.baselineTimerId);
      this.baselineTimerId = null;
    }
    this.behavioralData.baselineTimerId = null;

    this.behavioralData.isCollectingBaseline = false;
    this.behavioralData.baselineCompleted = true;
    this.behavioralData.baselineBehaviorData.collectionEndTime = Date.now();

    const baselineStats = this.validateBaselineData();

    this.behavioralData.baselineBehaviorData.overallBehaviorProfile = this.generateComprehensiveBaselineProfile();

    this.sendImmediateBaselineToBackend().then((result) => {
      this.startContinuousTransmission();

      window.dispatchEvent(new CustomEvent('backgroundBaselineCompleted', {
        detail: {
          baselineData: this.behavioralData.baselineBehaviorData,
          sessionId: this.sessionId,
          profileType: 'comprehensive_eagle_eye',
          backendResult: result
        }
      }));
    }).catch((error) => {
      this.startContinuousTransmission();

      window.dispatchEvent(new CustomEvent('backgroundBaselineCompleted', {
        detail: {
          baselineData: this.behavioralData.baselineBehaviorData,
          sessionId: this.sessionId,
          error: error.message
        }
      }));
    });
  }

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

    const minMouseMovements = 10; 
    const minTotalActions = 15;   

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

  generateComprehensiveBaselineProfile() {
    if (!this.behavioralData.baselineBehaviorData) return null;

    const baseline = this.behavioralData.baselineBehaviorData;
    const totalDuration = baseline.collectionEndTime - baseline.collectionStartTime;


    return {
      mouseProfile: {
        totalMovements: baseline.cursorMovements.length,
        avgSpeed: baseline.cursorSpeeds.length > 0 ?
          baseline.cursorSpeeds.reduce((a, b) => a + b, 0) / baseline.cursorSpeeds.length : 0,
        speedVariance: this.calculateVariance(baseline.cursorSpeeds),
        movementEntropy: this.calculatePathEntropy(baseline.cursorMovements),
        hoverPatterns: baseline.hoverPatterns.length
      },

      keyboardProfile: {
        totalKeyPresses: baseline.keyPressTimes.length,
        typingRhythm: this.calculateTypingRhythm(baseline.keyPressTimes),
        keySequencePatterns: baseline.keySequences.length,
        avgKeyInterval: this.calculateAvgKeyInterval(baseline.keyPressTimes)
      },

      clickProfile: {
        totalClicks: baseline.clickTimestamps.length,
        clickFrequency: baseline.clickTimestamps.length / (totalDuration / 1000),
        doubleClickPatterns: baseline.doubleClickIntervals.length,
        clickRhythm: this.calculateClickRhythm(baseline.clickTimestamps)
      },

      scrollProfile: {
        totalScrolls: baseline.scrollSpeeds.length,
        avgScrollSpeed: baseline.scrollSpeeds.length > 0 ?
          baseline.scrollSpeeds.reduce((a, b) => a + b, 0) / baseline.scrollSpeeds.length : 0,
        scrollPatterns: baseline.scrollPatterns.length,
        scrollVariance: this.calculateVariance(baseline.scrollSpeeds)
      },

      navigationProfile: {
        pagesVisited: baseline.pagesVisited.length,
        pageTransitions: baseline.pageTransitions.length,
        avgTimePerPage: baseline.timePerPage.length > 0 ?
          baseline.timePerPage.reduce((a, b) => a + b, 0) / baseline.timePerPage.length : 0,
        navigationPatterns: baseline.navigationPatterns.length
      },

      activityProfile: {
        totalActions: baseline.actionCount,
        actionsPerSecond: baseline.actionCount / (totalDuration / 1000),
        activeTime: baseline.totalActiveTime,
        idlePeriods: baseline.idlePeriods.length,
        overallActivityLevel: this.calculateActivityLevel(baseline)
      },

      collectionMeta: {
        duration: totalDuration,
        startTime: baseline.collectionStartTime,
        endTime: baseline.collectionEndTime,
        profileType: 'comprehensive_eagle_eye',
        dataQualityScore: this.calculateDataQualityScore(baseline)
      }
    };
  }

startContinuousTransmission() {
  if (this.behavioralData.continuousTransmissionStarted) {
    console.log('⚠️ Transmission already active');
    return;
  }

  if (this.backendIntervalId) {
    console.log('⚠️ Backend interval already exists');
    return;
  }
  
  this.behavioralData.continuousTransmissionStarted = true;

  // Send first payload immediately
  this.sendToBackend();

  // Start continuous transmission every 1 second
  this.backendIntervalId = setInterval(() => {
    this.sendToBackend();
  }, this.backendInterval);

  console.log('✅ Continuous transmission started immediately (every 1 second)');
}

// Call this method when user reaches main dashboard
initiateDashboardBehavioralTracking(userId) {
  if (!window.globalBehavioralTrackerInstance) {
    console.error('❌ Global behavioral tracker not initialized');
    return false;
  }
  
  console.log('🎯 Initiating dashboard behavioral tracking for user:', userId);
  
  // Set current page to dashboard
  window.globalBehavioralTrackerInstance.setCurrentPage('main_dashboard');
  
  // Start immediate dashboard tracking and transmission
  const result = window.globalBehavioralTrackerInstance.handleDashboardEntryImmediate(userId);
  
  console.log('✅ Dashboard behavioral tracking initiated:', result);
  
  return result;
}

  stopContinuousTransmission() {
    if (this.backendIntervalId) {
      clearInterval(this.backendIntervalId);
      this.backendIntervalId = null;
      console.log('⏹️ Continuous transmission stopped');
    }
  }

  ensureBackendTransmission() {
    if (!this.backendIntervalId) {
      console.log('🔧 Backend transmission not active, starting...');
      this.startContinuousTransmission();
    } else {
      console.log('✅ Backend transmission is active');
    }
  }

  trackEvent(eventType, eventData) {
    const timestamp = Date.now();

    this.ensureArraysInitialized();

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

    this.behavioralData.lastActionTime = timestamp;
    this.behavioralData.actionCount++;

    if (timestamp - this.lastSaveTime > this.saveInterval) {
      this.saveToStorage();
      this.lastSaveTime = timestamp;
    }
  }

  recordBaselineEvent(eventType, eventData, timestamp) {
    if (!this.behavioralData.isCollectingBaseline) {
      return; 
    }

    if (!this.behavioralData.baselineBehaviorData) {
      console.error('🚨 BASELINE ERROR: baselineBehaviorData is null but isCollectingBaseline is true');
      return;
    }


    const baseline = this.behavioralData.baselineBehaviorData;
    const currentPage = this.behavioralData.currentPage || 'unknown';

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

          if (baseline.cursorMovements.length > 1) {
            const prev = baseline.cursorMovements[baseline.cursorMovements.length - 2];
            const distance = Math.sqrt(
              Math.pow(movement.x - prev.x, 2) + Math.pow(movement.y - prev.y, 2)
            );
            const timeDiff = (timestamp - prev.timestamp) / 1000;
            const speed = timeDiff > 0 ? distance / timeDiff : 0;

            baseline.cursorSpeeds.push(speed);

            baseline.cursorPaths.push({
              from: { x: prev.x, y: prev.y },
              to: { x: movement.x, y: movement.y },
              distance: distance,
              speed: speed,
              page: currentPage,
              timestamp: timestamp
            });
          }

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

        if (baseline.keyPressTimes.length > 1) {
          const prev = baseline.keyPressTimes[baseline.keyPressTimes.length - 2];
          const interval = timestamp - prev;
          baseline.typingRhythm.push(interval);
        }

        baseline.keySequences.push({
          key: eventData.key || 'unknown',
          timestamp: timestamp,
          page: currentPage
        });
        break;

      case 'click':
      case 'buttonClick':
        baseline.clickTimestamps.push(timestamp);

        if (baseline.clickTimestamps.length > 1) {
          const prev = baseline.clickTimestamps[baseline.clickTimestamps.length - 2];
          const interval = timestamp - prev;

          if (interval < 500) { 
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

    if (currentPage) {
      if (!baseline.pagesVisited) {
        baseline.pagesVisited = [currentPage];
        console.warn('🚨 Fixed missing pagesVisited array in baseline data');
      }

      if (!baseline.pagesVisited.includes(currentPage)) {
        baseline.pagesVisited.push(currentPage);

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

    baseline.actionCount = (baseline.actionCount || 0) + 1;
    baseline.totalActiveTime = timestamp - baseline.collectionStartTime;

    if (!baseline.idlePeriods) {
      baseline.idlePeriods = [];
    }

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

  calculateVariance(values) {
    if (values.length === 0) return 0;
    const mean = values.reduce((a, b) => a + b, 0) / values.length;
    const variance = values.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / values.length;
    return variance;
  }

  calculatePathEntropy(movements) {
    if (movements.length < 2) return 0;
    let directionChanges = 0;
    for (let i = 2; i < movements.length; i++) {
      const prev = movements[i - 2];
      const curr = movements[i - 1];
      const next = movements[i];

      const angle1 = Math.atan2(curr.y - prev.y, curr.x - prev.x);
      const angle2 = Math.atan2(next.y - curr.y, next.x - curr.x);
      const angleDiff = Math.abs(angle2 - angle1);

      if (angleDiff > Math.PI / 4) directionChanges++;
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

const globalBehavioralTracker = new GlobalBehavioralTracker();

export default globalBehavioralTracker;

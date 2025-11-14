class GlobalBehavioralTracker {
  constructor(config = {}) {

   
    this.config = {
      dashboardPatterns: config.dashboardPatterns || [],
      apiEndpoints: {
        baselineStorage: config.apiEndpoints?.baselineStorage || null,
        realtimeAnalysis: config.apiEndpoints?.realtimeAnalysis || null,
      },
      logoutButtonSelectors: config.logoutButtonSelectors || [
        'button[onclick*="logout"]',
        'a[href*="logout"]',
        '.logout-button',
        '#logout-btn',
        '[data-action="logout"]'
      ],
      logoutButtonTexts: config.logoutButtonTexts || ['logout', 'log out', 'sign out'],
      apiHeaders: config.apiHeaders || {},
      includeCredentials: config.includeCredentials !== undefined ? config.includeCredentials : true,
      enableConsoleLogging: config.enableConsoleLogging !== undefined ? config.enableConsoleLogging : true,
      transmissionInterval: config.transmissionInterval || 1000,
      saveInterval: config.saveInterval || 2000,
      
      // NEW: Storage keys configuration
      storageKeys: {
        data: config.storageKeys?.data || 'global_behavioral_data',
        session: config.storageKeys?.session || 'global_behavioral_session',
        lifecycle: config.storageKeys?.lifecycle || 'user_lifecycle_state'
      },
      
      // NEW: Event names configuration
      events: {
        signup: config.events?.signup || 'userSignupTracking',
        logout: config.events?.logout || 'userLogoutTracking',
        dashboardEntry: config.events?.dashboardEntry || 'dashboardEntryTracking'
      },
      
      // NEW: Feature toggles
      features: {
        trackMouse: config.features?.trackMouse !== undefined ? config.features.trackMouse : true,
        trackKeyboard: config.features?.trackKeyboard !== undefined ? config.features.trackKeyboard : true,
        trackClicks: config.features?.trackClicks !== undefined ? config.features.trackClicks : true,
        trackScroll: config.features?.trackScroll !== undefined ? config.features.trackScroll : true,
        trackPaste: config.features?.trackPaste !== undefined ? config.features.trackPaste : true,
        deviceFingerprinting: config.features?.deviceFingerprinting !== undefined ? config.features.deviceFingerprinting : true
      },
      
      // NEW: Lifecycle hooks
      hooks: {
        beforeInit: config.hooks?.beforeInit || null,
        afterInit: config.hooks?.afterInit || null,
        beforeSend: config.hooks?.beforeSend || null,
        afterSend: config.hooks?.afterSend || null
      },
      
      // NEW: Error handling
      onError: config.onError || null,
      onTransmissionError: config.onTransmissionError || null,
      
      // NEW: Page name resolver
      pageNameResolver: config.pageNameResolver || null
   
  }
    
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

    this.dashboardUrl = null;
    this.dashboardReached = false;
    this.isOnMainDashboard = false;
    this.transmissionActive = false;
    this.auth_type = false;
    this.isRegistrationPhase = false; 
    this.baselineCollectionActive = false; 
    this.registrationStartTime = null;
    this.dashboardEntryTime = null;
    
    this.eventListeners = [];
    this.backendIntervalId = null;
    this.userLifecycleState = 'anonymous'; 
    this.userId = null;
    this.signupTimestamp = null;
    this.loginTimestamp = null;
    this.logoutTimestamp = null;
    this.baselineTimerId = null;
 this.STORAGE_KEY = this.config.storageKeys.data;
this.SESSION_KEY = this.config.storageKeys.session;
this.USER_LIFECYCLE_KEY = this.config.storageKeys.lifecycle;
    this.behavioralData = {
      sessionId: null,
      trackingStartTime: null,
      pageLoadTime: null,


      isRegistrationPhase: false,
      registrationStartTime: null,
      baselineCollectionActive: false,
      baselineStartTime: null,
      baselineEndTime: null, 
      auth_type: false,
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

  log(level, message, data = null) {
    if (!this.config.enableConsoleLogging) return;
    
    if (data !== null) {
      console[level](message, data);
    } else {
      console[level](message);
    }
  }


  getSessionStats() {
  const now = Date.now();

  return {
    sessionId: this.sessionId || null,
    currentPage: this.currentPage || null,
    actionCount: this.behavioralData?.actionCount || 0,
    lastActionTime: this.behavioralData?.lastActionTime || null,
    sessionDuration: this.sessionStart ? Math.round((now - this.sessionStart) / 1000) : 0, // in seconds
    cursorMovements: (this.behavioralData?.cursorMovements || []).length,
    keyPresses: (this.behavioralData?.keyPressTimes || []).length,
    clicks: (this.behavioralData?.clickTimestamps || []).length,
    scrollEvents: (this.behavioralData?.scrollSpeeds || []).length,
    pasteDetected: this.behavioralData?.pasteDetected || false,
    isRegistrationPhase: this.behavioralData?.isRegistrationPhase || false,
    baselineCollectionActive: this.behavioralData?.baselineCollectionActive || false,
  };
}

  init() {
    if (this.isInitialized) return;

    if (this.config.hooks.beforeInit) {
      try {
        this.config.hooks.beforeInit(this);
      } catch (error) {
        this.log('error', '❌ Error in beforeInit hook:', error);
      }
    }

    const currentAuthType = this.auth_type;
    this.loadUserLifecycleState();

    this.isInitialized = true;
    
    if (currentAuthType !== false && this.auth_type !== currentAuthType) {
      console.log('🔒 Preserving explicitly set auth_type:', currentAuthType, 'over loaded value:', this.auth_type);
      this.auth_type = currentAuthType;
      this.behavioralData.auth_type = currentAuthType;
    }

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

    this.isInitialized = true;

    if (this.config.hooks.afterInit) {
      try {
        this.config.hooks.afterInit(this);
      } catch (error) {
        this.log('error', '❌ Error in afterInit hook:', error);
      }
    }
  }
  isMainDashboardUrl() {
    if (this.config.dashboardPatterns.length === 0) {
      if (this.config.enableConsoleLogging) {
        console.warn('⚠️ No dashboard patterns configured. Assuming current page is valid.');
      }
      return true; // Default to true if no patterns specified
    }
    const currentUrl = window.location.href;
    console.log('🔍 Checking dashboard URL:', currentUrl);
    
    if (this.config.enableConsoleLogging) {
      console.log('🔍 Checking dashboard URL:', currentUrl);
    }
    
    
    const matches = this.config.dashboardPatterns.some(pattern => {
      if (pattern instanceof RegExp) {
        return pattern.test(currentUrl);
      }
      return currentUrl.includes(pattern);
    });
    
    if (this.config.enableConsoleLogging) {
    console.log('🔍 Dashboard URL check:', { currentUrl, matches });
  }
  
  return matches;
  }


  createNewSession() {
    // Generate completely new session ID
    this.sessionId = this.generateSessionId();
    this.trackingStartTime = Date.now();

    this.behavioralData = {
      sessionId: this.sessionId,
      trackingStartTime: this.trackingStartTime,
      pageLoadTime: Date.now(),

      isRegistrationPhase: false,
      registrationStartTime: null,
      baselineCollectionActive: false,
      baselineStartTime: null,
      baselineEndTime: null,

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

    

    this.sessionId = this.generateSessionId();
    this.trackingStartTime = Date.now();

    this.behavioralData.sessionId = this.sessionId;
    this.behavioralData.trackingStartTime = this.trackingStartTime;
    this.behavioralData.pageLoadTime = Date.now();

    localStorage.setItem(this.SESSION_KEY, this.sessionId);
    this.saveToStorage();

    console.log('📄 New behavioral session created:', this.sessionId)
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
    window.dispatchEvent(new CustomEvent(this.config.events.signup, {
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

  stopContinuousTransmission() {
    if (this.backendIntervalId) {
      clearInterval(this.backendIntervalId);
      this.backendIntervalId = null;
      this.transmissionActive = false;
      console.log('🛑 Continuous transmission stopped');
    }
  }

  startBaselineCollection(userId) {
    // Force initialization if not done
    if (!this.isInitialized) {
      this.init();
    }

    // Set registration user flags immediately
    this.auth_type = true;
    this.userId = userId;
    this.baselineCollectionActive = true;
    this.isRegistrationPhase = true;
    this.dashboardEntryTime = Date.now();
    
    // Ensure behavioral data object exists
    if (!this.behavioralData) {
      this.behavioralData = {};
    }
    
    // Set up behavioral data for baseline collection
    this.behavioralData.auth_type = true;
    this.behavioralData.userId = userId;
    this.behavioralData.baselineCollectionActive = true;
    this.behavioralData.baselineStartTime = Date.now();
    this.behavioralData.isRegistrationPhase = true;
    this.behavioralData.dashboardEntryTime = this.dashboardEntryTime;
    this.behavioralData.currentPage = 'main_dashboard';
    this.behavioralData.actionCount = 0;
    
    // CRITICAL: Enable data collection flag for tracking functions
    this.behavioralData.isCollectingBaseline = true;
    
    this.behavioralData.baselineBehaviorData = {
      cursorMovements: [],
      cursorSpeeds: [],
      cursorPaths: [],
      hoverPatterns: [],
      keyPressTimes: [],
      keySequences: [],
      typingRhythm: [],
      clickTimestamps: [],
      clickPatterns: [],
      doubleClickIntervals: [],
      scrollSpeeds: [],
      scrollDirections: [],
      scrollPatterns: [],
      sessionId: this.sessionId,
      userId: userId,
      startTime: Date.now(),
      currentPage: 'main_dashboard'
    };
    
    // Initialize behavioral arrays
    this.ensureArraysInitialized();
    
    // Force restart tracking to ensure event listeners are attached
    this.isTracking = false;
    this.startGlobalTracking();
    
    // Stop any continuous transmission (registration users collect silently)
    this.stopContinuousTransmission();
    
    return this.behavioralData.baselineBehaviorData;
  }

  startRegistrationPhase(userId) {
    
    // Stop any existing transmission first (critical!)
    this.stopContinuousTransmission();
    
    // Set up initial registration state
    this.userId = userId;
    this.userLifecycleState = 'registering';
    this.isRegistrationPhase = true;
    this.registrationStartTime = Date.now();
    this.auth_type = true; 
    
    // Update behavioral data for registration context
    this.behavioralData.userId = userId;
    this.behavioralData.userLifecycleState = 'registering';
    this.behavioralData.isRegistrationPhase = true;
    this.behavioralData.registrationStartTime = this.registrationStartTime;
    this.behavioralData.auth_type = true; // CRITICAL: Mark as registration user
    
    // FLOW STEP 2->3: Use dedicated baseline collection function
    const baselineResult = this.startBaselineCollection(userId);
    
    // Save state and set up logout listener
    this.saveUserLifecycleState();


    console.log('� Baseline collection status:', baselineResult);
    
    return {
      userId: this.userId,
      sessionId: this.sessionId,
      registrationStarted: true,
      state: this.userLifecycleState,
      silentMode: true,
      baselineCollectionActive: true,
      auth_type: true,
      baselineResult: baselineResult,
      flowStep: 'registration_phase_complete'
    };
  }

  handleDirectLogin(userId) {
    console.log('🔐 DIRECT LOGIN: User logging in directly (not from registration)');
    
    this.userId = userId;
    this.userLifecycleState = 'logged_in';
    this.loginTimestamp = Date.now();
    this.auth_type = false; // CRITICAL: Mark as direct login user
    
    this.behavioralData.userId = userId;
    this.behavioralData.userLifecycleState = 'logged_in';
    this.behavioralData.loginTimestamp = this.loginTimestamp;
    this.behavioralData.auth_type = false; // CRITICAL: Mark as direct login user
    
    // Start tracking
    if (!this.isTracking) {
      this.startGlobalTracking();
      this.setupPeriodicSaving();
    }
    
    this.saveUserLifecycleState();
    
    console.log('🚀 DIRECT LOGIN USER: auth_type set to FALSE - Will use real-time transmission');
    
    return {
      userId: this.userId,
      sessionId: this.sessionId,
      loginStarted: true,
      state: this.userLifecycleState,
      auth_type: false
    };
  }
  handleDashboardEntry(userId) {
    console.log('🏠 DASHBOARD ENTRY: User successfully reached dashboard');
    console.log('🔍 Current auth_type:', this.auth_type);
    console.log('🔍 Current behavioralData.auth_type:', this.behavioralData.auth_type);
    console.log('🌐 Current URL:', window.location.href);
    
    const isDashboardUrl = this.isMainDashboardUrl();
    console.log('🔍 URL Check Result:', {
      currentUrl: window.location.href,
      isDashboardUrl: isDashboardUrl,
      expectedPattern: 'http://localhost:3000/auth-user or /auth-user'
    });
    
    if (!isDashboardUrl) {
      console.warn('⚠️ Not on main dashboard URL - BLOCKING DASHBOARD ENTRY!');
      console.warn('💡 Consider updating isMainDashboardUrl() to match actual dashboard URL');
      console.warn('🚨 FORCING DASHBOARD ENTRY FOR REGISTRATION USER (auth_type=true)');
      
      // Force allow registration users even if URL doesn't match
      if (this.auth_type === true) {
        console.log('🔓 FORCE ALLOWING: Registration user detected, bypassing URL check');
      } else {
        return { error: 'Not on main dashboard', currentUrl: window.location.href };
      }
    }
    
    if (this.userId && this.userId !== userId) {
      this.log('warn', '⚠️ User ID mismatch during dashboard entry');
    }

    const isRegistrationUser = (this.auth_type === true) || 
                              (this.userLifecycleState === 'registering') || 
                              (this.isRegistrationPhase === true);
    
    console.log('🔍 DECISION: isRegistrationUser =', isRegistrationUser);
    
    if (isRegistrationUser) {
this.log('log', '📊 FLOW STEP 1: handleDashboardEntry calling startRegistrationPhase');
      
      // FLOW STEP 1->2: Call startRegistrationPhase which will handle baseline collection
      const registrationResult = this.startRegistrationPhase(userId);
      
      // FLOW STEP 5: Set up dashboard properties after registration phase setup
      this.setupDashboardProperties(userId);
      
      console.log('✅ FLOW STEP 5 COMPLETE: Registration phase and dashboard setup done');
      console.log('📊 Registration result from startRegistrationPhase:', registrationResult);
      
      // FLOW STEP 6: Send baseline data to backend via required API
      console.log('� Sending baseline data to backend...');
      // Make the HTTP call asynchronous to avoid blocking dashboard navigation
      this.sendDataToBackend(registrationResult)
        .then(result => {
          console.log('✅ Baseline data sent successfully:', result);
        })
        .catch(error => {
          console.error('❌ Failed to send baseline data:', error);
          // Don't block UI for network errors
        });
      
      return {
        sessionId: this.sessionId,
        dashboardEntryTime: this.dashboardEntryTime,
        baselineCollectionStarted: true,
        silentMode: true,
        status: 'registration_flow_complete',
        auth_type: true,
        userType: 'registration',
        registrationResult: registrationResult,
        flowStep: 'completed'
      };
      
    } else {
      console.log('🚀 DIRECT LOGIN USER PATH: Starting real-time transmission');
      this.handleDirectLogin(userId);
      
      // Set dashboard entry properties for direct login users
      this.userId = userId;
      this.userLifecycleState = 'logged_in';
      this.loginTimestamp = Date.now();
      this.isOnMainDashboard = true;
      this.dashboardReached = true;
      this.dashboardEntryTime = Date.now();
      this.dashboardUrl = window.location.href;
      
      // Reset behavioral data for fresh baseline collection
      
      // Start baseline collection for direct login users
      this.baselineCollectionActive = true;
      this.behavioralData.baselineCollectionActive = true;
      this.behavioralData.baselineStartTime = Date.now();
      
      // Update behavioral data with dashboard entry info
      this.behavioralData.userId = userId;
      this.behavioralData.userLifecycleState = 'logged_in';
      this.behavioralData.loginTimestamp = this.loginTimestamp;
      this.behavioralData.dashboardEntryTime = this.dashboardEntryTime;
      this.behavioralData.currentPage = 'main_dashboard';
      this.behavioralData.dashboardUrl = this.dashboardUrl;
      
      // Ensure tracking is active
      if (!this.isTracking) {
        this.startGlobalTracking();
        this.setupPeriodicSaving();
      }
      
      // Start continuous transmission for direct login users
      this.startContinuousTransmission();
      this.saveUserLifecycleState();
      
      return {
        sessionId: this.sessionId,
        dashboardEntryTime: this.dashboardEntryTime,
        baselineCollectionStarted: true,
        silentMode: false,
        status: 'active_transmission',
        auth_type: false,
        userType: 'direct_login'
      };
    }
  }
  saveUserLifecycleState() {
  const lifecycleState = {
    userId: this.userId,
    sessionId: this.sessionId,
    userLifecycleState: this.userLifecycleState,
    isRegistrationPhase: this.isRegistrationPhase,
    registrationStartTime: this.registrationStartTime,
    loginTimestamp: this.loginTimestamp,
    dashboardEntryTime: this.dashboardEntryTime,
    logoutTimestamp: this.logoutTimestamp,
    baselineCollectionActive: this.baselineCollectionActive,
    auth_type: this.auth_type, // Make sure this is saved
    savedAt: Date.now()
  };
  
  try {
    localStorage.setItem(this.USER_LIFECYCLE_KEY, JSON.stringify(lifecycleState));
    console.log('💾 Saved lifecycle state with auth_type:', this.auth_type);
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
        this.isRegistrationPhase = lifecycleState.isRegistrationPhase;
        this.registrationStartTime = lifecycleState.registrationStartTime;
        this.loginTimestamp = lifecycleState.loginTimestamp;
        this.dashboardEntryTime = lifecycleState.dashboardEntryTime;
        this.logoutTimestamp = lifecycleState.logoutTimestamp;
        this.baselineCollectionActive = lifecycleState.baselineCollectionActive;
        
        // CRITICAL FIX: Properly restore auth_type with explicit check
        if (lifecycleState.auth_type !== undefined) {
          this.auth_type = lifecycleState.auth_type;
          console.log('📋 Restored auth_type from storage:', this.auth_type);
        } else {
          // Default to false if not found (direct login behavior)
          this.auth_type = false;
          console.warn('⚠️ No auth_type in saved state - defaulting to false');
        }
        
        // Update behavioral data with loaded state
        this.behavioralData.userId = this.userId;
        this.behavioralData.sessionId = this.sessionId;
        this.behavioralData.userLifecycleState = this.userLifecycleState;
        this.behavioralData.isRegistrationPhase = this.isRegistrationPhase;
        this.behavioralData.registrationStartTime = this.registrationStartTime;
        this.behavioralData.loginTimestamp = this.loginTimestamp;
        this.behavioralData.dashboardEntryTime = this.dashboardEntryTime;
        this.behavioralData.logoutTimestamp = this.logoutTimestamp;
        this.behavioralData.baselineCollectionActive = this.baselineCollectionActive;
        this.behavioralData.auth_type = this.auth_type; // ENSURE behavioral data matches
        
        console.log('📋 Loaded lifecycle state:', {
          userLifecycleState: lifecycleState.userLifecycleState,
          auth_type: this.auth_type,
          isRegistrationPhase: this.isRegistrationPhase
        });
      } else {
        // No saved state - set defaults
        this.auth_type = false;
        console.log('📋 No saved lifecycle state - defaulting auth_type to false');
      }
    } catch (error) {
      console.error('Error loading lifecycle state:', error);
      this.auth_type = false; // Default fallback
    }
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
      }
    });

    const requiredObjects = [
      'lastKeyDown', 'postPasteActivity', 'canvasMetrics', 'unusualScreenResolution',
      'gpuInfo', 'timingMetrics', 'crossPageMetrics'
    ];

    requiredObjects.forEach(objName => {
      if (typeof this.behavioralData[objName] !== 'object' || this.behavioralData[objName] === null) {
        this.behavioralData[objName] = {};
      }
    });
  }

  generateSessionId() {
    const timestamp = Date.now().toString(36);
    const array = new Uint8Array(16);
    if (window.crypto && window.crypto.getRandomValues) {
      window.crypto.getRandomValues(array);
    } else {
      for (let i = 0; i < array.length; i++) {
        array[i] = Math.floor(Math.random() * 256);
      }
    }
    const randomString = Array.from(array, byte => byte.toString(36).padStart(2, '0')).join('').substring(0, 12);
    return `${timestamp}-${randomString}`;
  }


  startGlobalTracking() {
    if (this.isTracking) return;

    this.isTracking = true;

    if (this.config.features.trackMouse) {
      const handleMouseMove = (event) => this.trackMouseMovement(event);
      this.addEventListener(document, 'mousemove', handleMouseMove);
    }
    
    if (this.config.features.trackKeyboard) {
      const handleKeyDown = (event) => this.trackKeyDown(event);
      const handleKeyUp = (event) => this.trackKeyUp(event);
      this.addEventListener(document, 'keydown', handleKeyDown);
      this.addEventListener(document, 'keyup', handleKeyUp);
    }
    
    if (this.config.features.trackClicks) {
      const handleClick = (event) => this.trackClick(event);
      this.addEventListener(document, 'click', handleClick);
    }
    
    if (this.config.features.trackScroll) {
      const handleScroll = (event) => this.trackScroll(event);
      this.addEventListener(window, 'scroll', handleScroll);
    }
    
    if (this.config.features.trackPaste) {
      const handlePaste = (event) => this.trackPaste(event);
      this.addEventListener(document, 'paste', handlePaste);
    }

    const handleMouseMove = (event) => this.trackMouseMovement(event);
    const handleKeyDown = (event) => this.trackKeyDown(event);
    const handleKeyUp = (event) => this.trackKeyUp(event);
    const handleClick = (event) => this.trackClick(event);
    const handleScroll = (event) => this.trackScroll(event);
    const handlePaste = (event) => this.trackPaste(event);

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
        canvasFingerprint: canvasFingerprint.substring(0, 100)
      };

      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      if (gl) {
        const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
        this.behavioralData.gpuInfo = {
          gpu_name: debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : 'unknown',
          vendor: debugInfo ? gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) : 'unknown',
          renderer: gl.getParameter(gl.RENDERER),
          webgl_info: gl.getParameter(gl.VERSION)
        };
      } else {
        this.behavioralData.missingCanvasFingerprint = true;
        this.behavioralData.gpuInfo = {
          gpu_name: 'webgl_not_supported',
          vendor: 'unknown',
          renderer: 'unknown',
          webgl_info: 'not_available'
        };
      }

      console.log('🔍 Device fingerprinting completed');

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

    // PRIORITY: Handle baseline collection for registration users
    if (this.behavioralData.isCollectingBaseline && this.auth_type === true) {
      // Also record to main behavioral data for registration users
      this.behavioralData.cursorMovements.push(newPoint);
      this.behavioralData.actionCount = (this.behavioralData.actionCount || 0) + 1;
      return; // Exit early for registration users to avoid double processing
    }

    // Regular processing for direct login users
    if (this.auth_type === false) {

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
    } // Close the if (this.auth_type === false) conditional
  }

  trackKeyDown(event) {
    const now = Date.now();
    
    // PRIORITY: Handle baseline collection for registration users
    if (this.behavioralData.isCollectingBaseline && this.auth_type === true) {
      // Also record to main behavioral data
      this.behavioralData.lastKeyDown[event.key] = now;
      this.behavioralData.keyPressTimes.push(now);
      this.behavioralData.actionCount = (this.behavioralData.actionCount || 0) + 1;
      this.behavioralData.lastActionTime = now;
      return;
    }

    // Regular processing for direct login users
    if (this.auth_type === false) {
      this.behavioralData.lastKeyDown[event.key] = now;
      
      this.behavioralData.keyPressTimes = [
        ...this.behavioralData.keyPressTimes.slice(-99),
        now
      ];
      
      this.behavioralData.lastKeyPress = now;
      this.behavioralData.actionCount++;
      this.behavioralData.lastActionTime = now;

      if (event.key === 'Tab') {
        this.behavioralData.TabKeyCount++;
      }
    }
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

    // PRIORITY: Handle baseline collection for registration users
    if (this.behavioralData.isCollectingBaseline && this.auth_type === true) {
      // Also record to main behavioral data
      this.behavioralData.clickTimestamps.push(now);
      this.behavioralData.actionCount = (this.behavioralData.actionCount || 0) + 1;
      this.behavioralData.lastActionTime = now;
      return;
    }

    // Regular processing for direct login users
    if (this.auth_type === false) {
      this.behavioralData.clickTimestamps = [
        ...this.behavioralData.clickTimestamps.slice(-99),
        now
      ];

      this.behavioralData.lastClickTime = now;
      this.behavioralData.actionCount++;
      this.behavioralData.lastActionTime = now;
    }
  }

  trackScroll(event) {
    const now = Date.now();

    // PRIORITY: Handle baseline collection for registration users
    if (this.behavioralData.isCollectingBaseline && this.auth_type === true) {
      this.behavioralData.actionCount = (this.behavioralData.actionCount || 0) + 1;
      this.behavioralData.lastActionTime = now;
      return;
    }

    // Regular processing for direct login users  
    if (this.auth_type === false) {
      this.behavioralData.scrollChanges++;

      const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
      const timeDiff = now - (this.behavioralData.lastScrollTime || now);
      const scrollDiff = Math.abs(scrollTop - (this.behavioralData.lastScroll || 0));

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
  }

   setCurrentPage(pageName) {
    const now = Date.now();
    const previousPage = this.behavioralData.currentPage;

    if (!this.behavioralData.pageHistory) {
      this.behavioralData.pageHistory = [];
    }

    if (previousPage && previousPage !== pageName) {
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
  }, this.config?.saveInterval || this.saveInterval);
}
  saveToStorage() {
    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.behavioralData));
    } catch (error) {
      console.error('Error saving behavioral data:', error);
    }
  }

  
  async sendDataToBackend(registrationResult) {
    console.log('📤 IMMEDIATE BASELINE SEND: Sending registration baseline data to backend');
    console.log('🎯 Registration result:', registrationResult);
    
    if (!this.userId) {
      console.error('❌ No user ID available for baseline storage');
      return { error: 'No user ID' };
    }
    
    try {
      // Prepare current baseline data for immediate transmission
      const currentBaselineData = {
        sessionId: this.sessionId,
        userId: this.userId,
        
        // Time tracking from registration result
        registrationStartTime: registrationResult.registrationStartTime || this.registrationStartTime,
        dashboardEntryTime: registrationResult.dashboardEntryTime || this.dashboardEntryTime,
        baselineStartTime: registrationResult.baselineResult?.baselineStartTime || Date.now(),
        currentTimestamp: Date.now(),
        
        // Current behavioral data (may be empty at start)
        cursorMovements: this.behavioralData.cursorMovements || [],
        cursorSpeeds: this.behavioralData.cursorSpeeds || [],
        cursorAcceleration: this.behavioralData.cursorAcceleration || [],
        cursorCurvature: this.behavioralData.cursorCurvature || [],
        keyPressTimes: this.behavioralData.keyPressTimes || [],
        keyHoldTimes: this.behavioralData.keyHoldTimes || [],
        clickTimestamps: this.behavioralData.clickTimestamps || [],
        scrollSpeeds: this.behavioralData.scrollSpeeds || [],
        
        // Advanced metrics
        mouseJitter: this.behavioralData.mouseJitter || [],
        microPauses: this.behavioralData.microPauses || [],
        hesitationTimes: this.behavioralData.hesitationTimes || [],
        suspiciousPatterns: this.behavioralData.suspiciousPatterns || [],
        keyboardPatterns: this.behavioralData.keyboardPatterns || [],
        
        // Activity metrics
        scrollChanges: this.behavioralData.scrollChanges || 0,
        idleTime: this.behavioralData.idleTime || 0,
        pasteDetected: this.behavioralData.pasteDetected || false,
        actionCount: this.behavioralData.actionCount || 0,
        TabKeyCount: this.behavioralData.TabKeyCount || 0,
        
        // Device and fingerprinting info
        deviceFingerprint: this.behavioralData.deviceFingerprint || '0',
        canvasMetrics: this.behavioralData.canvasMetrics || {},
        gpuInfo: this.behavioralData.gpuInfo || {},
        unusualScreenResolution: this.behavioralData.unusualScreenResolution || {},
        missingCanvasFingerprint: this.behavioralData.missingCanvasFingerprint || false,
        
        // Page tracking
        currentPage: this.behavioralData.currentPage || 'main_dashboard',
        pageHistory: this.behavioralData.pageHistory || [],
        
        // Post-paste activity tracking
        postPasteActivity: this.behavioralData.postPasteActivity || { keypressAfterPaste: 0 },
        
        // Timing metrics
        timingMetrics: this.behavioralData.timingMetrics || {},
        
        // Authentication context
        auth_type: this.auth_type,
        userLifecycleState: this.userLifecycleState,
        isRegistrationPhase: this.isRegistrationPhase,
        baselineCollectionActive: this.baselineCollectionActive
      };
      
      const payload = {
        session_id: this.sessionId,
        user_id: this.userId,
        baseline_data: currentBaselineData,
        collection_trigger: 'immediate_after_registration',
        collection_duration: Date.now() - (registrationResult.baselineResult?.baselineStartTime || Date.now()),
        baseline_type: 'registration_immediate_baseline',
        auth_type: this.auth_type,
        total_actions: this.behavioralData.actionCount || 0,
        registration_start_time: this.registrationStartTime,
        dashboard_entry_time: this.dashboardEntryTime,
        immediate_send_time: Date.now(),
        registration_result: registrationResult
      };
      
      console.log('📊 IMMEDIATE baseline payload summary:', {
        sessionId: this.sessionId,
        userId: this.userId,
        collectionDuration: payload.collection_duration,
        totalActions: payload.total_actions,
        trigger: payload.collection_trigger,
        dataPoints: {
          cursorMovements: currentBaselineData.cursorMovements.length,
          keyPresses: currentBaselineData.keyPressTimes.length,
          clicks: currentBaselineData.clickTimestamps.length,
          scrollEvents: currentBaselineData.scrollSpeeds.length,
          jitterEvents: currentBaselineData.mouseJitter.length,
          hesitations: currentBaselineData.hesitationTimes.length,
          microPauses: currentBaselineData.microPauses.length
        }
      });
      
      
      if (!this.config.apiEndpoints.baselineStorage) {
        console.warn('⚠️ No baseline storage endpoint configured');
        return { warning: 'No endpoint configured', payload };
      }

      const response = await fetch(this.config.apiEndpoints.baselineStorage, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(this.config.apiHeaders || {})
        },
        body: JSON.stringify(payload),
        credentials: this.config.includeCredentials ? 'include' : 'same-origin'
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const result = await response.json();
      
      if (this.config.enableConsoleLogging) {
        console.log('✅ Baseline data sent successfully:', result);
      }
      
      return result;
      
    } catch (error) {
      console.error('❌ Network error sending immediate baseline data:', {
        message: error.message,
        name: error.name,
        stack: error.stack
      });
      
      throw error;
    }
  }

  setupDashboardProperties(userId) {
    console.log('🏠 Setting up dashboard properties for user:', userId);
    
    // Set dashboard entry properties
    this.userId = userId;
    this.userLifecycleState = 'logged_in';
    this.loginTimestamp = Date.now();
    this.isOnMainDashboard = true;
    this.dashboardReached = true;
    this.dashboardEntryTime = Date.now();
    this.dashboardUrl = window.location.href;
    
    // Update behavioral data with dashboard entry info
    this.behavioralData.userId = userId;
    this.behavioralData.userLifecycleState = 'logged_in';
    this.behavioralData.loginTimestamp = this.loginTimestamp;
    this.behavioralData.dashboardEntryTime = this.dashboardEntryTime;
    this.behavioralData.currentPage = 'main_dashboard';
    this.behavioralData.dashboardUrl = this.dashboardUrl;
    
    console.log('✅ Dashboard properties configured');
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
      this.saveToStorage();
    };
    window.addEventListener('beforeunload', handleUnload);
    window.addEventListener('pagehide', handleUnload);
  }

  setupNavigationDetection() {
    this.currentUrl = window.location.href;
    
    const handlePopState = () => {
      this.handleUrlChange('popstate', window.location.href);
    };

    const handleHashChange = () => {
      this.handleUrlChange('hashchange', window.location.href);
    };

    const handleVisibilityChange = () => {
      if (!document.hidden) {
        const currentUrl = window.location.href;
        if (currentUrl !== this.currentUrl) {
          this.handleUrlChange('visibility_change', currentUrl);
        }
      }
    };

    // 6️⃣ Listen for focus events (when user clicks on browser tab)
    const handleFocus = () => {
      const currentUrl = window.location.href;
      if (currentUrl !== this.currentUrl) {
        console.log('📄 URL CHANGE detected on focus');
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

  
  

  
  

  



  handleUrlChange(changeType, newUrl) {
    try {
      const now = Date.now();
      const timeSinceLastNav = now - this.lastNavigationTime;

      console.log('📄 URL Change detected:', {
        changeType,
        newUrl,
        isMainDashboard: this.isMainDashboardUrl(),
        wasOnDashboard: this.isOnMainDashboard
      });

      const nowOnDashboard = newUrl.includes('/auth-user');
      const wasOnDashboard = this.isOnMainDashboard;

      // Check if user just entered the main dashboard
      if (!wasOnDashboard && nowOnDashboard) {
        console.log('🏠 DASHBOARD ENTRY DETECTED via URL change!');
        this.handleDashboardEntry(this.userId);
      }
      
      // Check if user left the dashboard
      if (wasOnDashboard && !nowOnDashboard) {
        console.log('🚪 Left dashboard');
        this.isOnMainDashboard = false;
      }

      this.currentUrl = newUrl;
      this.lastNavigationTime = now;

    } catch (error) {
      console.error('❌ Error handling URL change:', error);
    }
  }



  updateCurrentPage(newUrl) {
    const now = Date.now();
    const previousPage = this.behavioralData.currentPage;
    
    // Extract page name from URL
    let pageName = 'unknown';
    try {
      const url = new URL(newUrl);
      pageName = url.pathname.split('/').filter(p => p).join('_') || 'home';
    } catch (error) {
      console.warn('Could not parse URL for page name:', error);
    }
    
    this.behavioralData.currentPage = pageName;
    this.behavioralData.pageLoadTime = now;
    
    console.log(`📄 Page updated: ${previousPage} → ${pageName}`);
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
    return { ...this.behavioralData };
  }


  clearSession() {
    console.log('🧹 Clearing behavioral session...');
    
    this.stopTracking();

    localStorage.removeItem(this.STORAGE_KEY);
    localStorage.removeItem(this.SESSION_KEY);
    localStorage.removeItem(this.USER_LIFECYCLE_KEY);

    // Reset all state
    this.isRegistrationPhase = false;
    this.baselineCollectionActive = false;
    this.registrationStartTime = null;
    this.dashboardEntryTime = null;
    this.logoutTimestamp = null;
    this.userId = null;
    this.userLifecycleState = 'anonymous';
    
    // Reset behavioral data
    this.behavioralData = {
      sessionId: null,
      trackingStartTime: null,
      pageLoadTime: null,
      isRegistrationPhase: false,
      registrationStartTime: null,
      baselineCollectionActive: false,
      baselineStartTime: null,
      baselineEndTime: null,
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
      postPasteActivity: { keypressAfterPaste: 0 },
      deviceFingerprint: null,
      canvasMetrics: { winding: null, geometryLength: 0, textLength: 0, hash: null },
      missingCanvasFingerprint: true,
      unusualScreenResolution: {
        width_height: "0x0", inner_width: 0, device_pixel_ratio: 0,
        is_unusual: false, spoofedMismatch: false, aspectRatio: 0,
      },
      gpuInfo: { vendor: 'Unknown', model: 'Unknown' },
      timingMetrics: {
        trackingStartTime: null, domContentLoaded: null, pageLoadComplete: null,
        navigationStart: null, firstPaint: null, mouseMovementFrequency: 0,
        keyPressFrequency: 0, clickFrequency: 0, pageLoadTime: null,
        timeToFirstClick: 0, lastKeyPress: null, lastMouseMove: null, lastClick: null
      },
      currentPage: null,
      honeypotValue: "",
      TabKeyCount: 0
    };

    this.isTracking = false;
    console.log('✅ Session cleared successfully');
  }



  handleUserLogout() {
    console.log('🚪 USER LOGOUT: Processing logout and baseline data');
    
    const logoutTime = Date.now();
    this.logoutTimestamp = logoutTime;
    
    // Update behavioral data with logout info
    this.behavioralData.logoutTimestamp = logoutTime;
    this.behavioralData.baselineEndTime = logoutTime;
    
    // Calculate session duration
    const sessionDuration = this.dashboardEntryTime ? 
      (logoutTime - this.dashboardEntryTime) : 0;
    
    console.log('📊 Session completed:', {
      sessionDuration: sessionDuration,
      totalActions: this.behavioralData.actionCount,
      auth_type: this.auth_type,
      userId: this.userId,
      dataPoints: {
        cursorMovements: this.behavioralData.cursorMovements.length,
        keyPresses: this.behavioralData.keyPressTimes.length,
        clicks: this.behavioralData.clickTimestamps.length,
        scrollEvents: this.behavioralData.scrollSpeeds.length
      }
    });
    
    // Stop behavioral data collection
    this.baselineCollectionActive = false;
    this.behavioralData.baselineCollectionActive = false;
    
    // Stop transmission if active (for direct login users)
    this.stopContinuousTransmission();
    
    // CRITICAL: Only send baseline data for registration users
    if (this.auth_type === true && this.behavioralData.actionCount > 0) {
      console.log('📤 REGISTRATION USER LOGOUT: Sending baseline data to backend');
      console.log('🎯 Target endpoint: (baseline storage)');
      console.log('📊 Data collected during silent baseline collection period');
      console.log('📊 Final baseline data summary:', {
        sessionId: this.sessionId,
        userId: this.userId,
        auth_type: this.auth_type,
        actionCount: this.behavioralData.actionCount,
        collectionDuration: sessionDuration,
        dataPoints: {
          cursorMovements: this.behavioralData.cursorMovements?.length || 0,
          keyPresses: this.behavioralData.keyPressTimes?.length || 0,
          clicks: this.behavioralData.clickTimestamps?.length || 0,
          scrollEvents: this.behavioralData.scrollSpeeds?.length || 0,
          mouseJitter: this.behavioralData.mouseJitter?.length || 0,
          hesitations: this.behavioralData.hesitationTimes?.length || 0,
          microPauses: this.behavioralData.microPauses?.length || 0
        }
      });
      
      return this.sendDataToBackend()
        .then((result) => {
          console.log('✅ Baseline data sent successfully:', result);
          
          // Emit logout event with success
          window.dispatchEvent(new CustomEvent('userLogoutTracking', {
            detail: {
              sessionId: this.sessionId,
              logoutTime: logoutTime,
              sessionDuration: sessionDuration,
              totalActions: this.behavioralData.actionCount,
              baselineCollected: true,
              baselineSent: true,
              dataCollected: true,
              auth_type: this.auth_type,
              success: true
            }
          }));
          
          return {
            sessionId: this.sessionId,
            logoutTime: logoutTime,
            sessionDuration: sessionDuration,
            dataCollected: true,
            baselineSent: true,
            auth_type: this.auth_type,
            success: true
          };
        })
        .catch((error) => {
          console.error('❌ Failed to send baseline data:', error);
          
          // Emit logout event with error
          window.dispatchEvent(new CustomEvent(this.config.events.logout, {
            detail: {
              sessionId: this.sessionId,
              logoutTime: logoutTime,
              sessionDuration: sessionDuration,
              totalActions: this.behavioralData.actionCount,
              baselineCollected: true,
              baselineSent: false,
              dataCollected: true,
              auth_type: this.auth_type,
              success: false,
              error: error.message
            }
          }));
          
          return {
            sessionId: this.sessionId,
            logoutTime: logoutTime,
            sessionDuration: sessionDuration,
            dataCollected: true,
            baselineSent: false,
            auth_type: this.auth_type,
            success: false,
            error: error.message
          };
        });
    } else if (this.auth_type === false) {
      console.log('🔄 DIRECT LOGIN USER: No baseline data to send (was using real-time analysis)');
    } else {
      console.warn('⚠️ No behavioral data collected or auth_type not set');
    }
    
    // Update lifecycle state
    this.userLifecycleState = 'logged_out';
    this.saveUserLifecycleState();
    
    // Emit logout event for non-registration users
    window.dispatchEvent(new CustomEvent('userLogoutTracking', {
      detail: {
        sessionId: this.sessionId,
        logoutTime: logoutTime,
        sessionDuration: sessionDuration,
        totalActions: this.behavioralData.actionCount,
        baselineCollected: false,
        baselineSent: false,
        dataCollected: this.behavioralData.actionCount > 0,
        auth_type: this.auth_type,
        success: true
      }
    }));
    
    return {
      sessionId: this.sessionId,
      logoutTime: logoutTime,
      sessionDuration: sessionDuration,
      dataCollected: this.behavioralData.actionCount > 0,
      baselineSent: false,
      auth_type: this.auth_type,
      success: true
    };
  }

 

  // Debug method to check current status
  getCollectionStatus() {
    return {
      auth_type: this.auth_type,
      isRegistrationPhase: this.isRegistrationPhase,
      baselineCollectionActive: this.baselineCollectionActive,
      isTracking: this.isTracking,
      transmissionActive: this.transmissionActive,
      userId: this.userId,
      sessionId: this.sessionId,
      actionCount: this.behavioralData?.actionCount || 0,
      dataPoints: {
        cursorMovements: this.behavioralData?.cursorMovements?.length || 0,
        keyPresses: this.behavioralData?.keyPressTimes?.length || 0,
        clicks: this.behavioralData?.clickTimestamps?.length || 0,
        scrollEvents: this.behavioralData?.scrollSpeeds?.length || 0
      },
      userLifecycleState: this.userLifecycleState,
      dashboardEntryTime: this.dashboardEntryTime
    };
  }



  trackEvent(eventType, eventData) {
    const timestamp = Date.now();

    this.ensureArraysInitialized();

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
            const timeDiff = (timestamp - prev.timestamp) / 1000;
            const speed = timeDiff > 0 ? distance / timeDiff : 0;

            this.behavioralData.cursorSpeeds.push(speed);
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


  forceResetSession() {
    console.log('🔄 Force resetting behavioral session...');
    this.clearSession();
    this.createNewSession();
    console.log('✅ Session force reset complete');
  }

  
startContinuousTransmission() {
    
    // CRITICAL GUARD 1: Block transmission for registration users (auth_type = true)
    if (this.auth_type === true) {
      console.log('🔇 REGISTRATION USER (auth_type=true): BLOCKING continuous transmission');
      return { blocked: true, reason: 'registration_user' };
    }

    if (this.userLifecycleState === 'registering' || this.isRegistrationPhase) {
      console.log('🔇 User in registration phase - BLOCKING transmission');
      return { blocked: true, reason: 'registration_phase' };
    }
      
    if (!this.isMainDashboardUrl()) {
      console.log('⚠️ Not on main dashboard - transmission not started');
      return { blocked: true, reason: 'not_on_dashboard' };
    }
      
    if (this.transmissionActive) {
      console.log('⚠️ Transmission already active');
      return { blocked: false, reason: 'already_active' };
    }

    if (this.backendIntervalId) {
      console.log('⚠️ Backend interval already exists - clearing first');
      clearInterval(this.backendIntervalId);
      this.backendIntervalId = null;
    }
    
    // Only set transmissionActive to true if all guards pass
    this.transmissionActive = true;

    
    // Send first payload immediately
    this.sendToBackend().then((result) => {
      if (result && result.blocked) {
        console.log('⚠️ First payload was blocked:', result.reason);
        this.stopContinuousTransmission();
        return;
      }
      console.log('✅ First behavioral payload sent successfully');
    }).catch((error) => {
      console.warn('⚠️ First payload failed, continuing transmission:', error);
    });

    // Start continuous transmission
    this.backendIntervalId = setInterval(() => {
      if (this.isMainDashboardUrl() && this.isOnMainDashboard) {
        this.sendToBackend().then((result) => {
          if (result && result.blocked) {
            console.log('🛑 Transmission blocked:', result.reason);
            this.stopContinuousTransmission();
          }
        }).catch(error => {
          console.warn('⚠️ Backend transmission failed:', error.message);
        });
      } else {
        console.log('⚠️ No longer on dashboard - stopping transmission');
        this.stopContinuousTransmission();
      }
    }, this.config?.transmissionInterval || this.backendInterval);

    console.log('✅ Continuous transmission started (every 1 second)');
    return { blocked: false, started: true };
  }

  async sendToBackend() {
  // CRITICAL GUARD: Block for registration users
  if (this.auth_type === true) {
    return { blocked: true, reason: 'registration_user' };
  }

  if (!this.config.apiEndpoints.realtimeAnalysis) {
    if (this.config.enableConsoleLogging) {
      console.warn('⚠️ No real-time analysis endpoint configured');
    }
    return { blocked: true, reason: 'no_endpoint_configured' };
  }

  try {
    const behavioralData = this.convertToBackendFormat();
    
    const payload = {
      session_id: this.sessionId,
      user_id: this.userId,
      behavioral_data: behavioralData,
      timestamp: Date.now(),
      auth_type: this.auth_type
    };

    const response = await fetch(this.config.apiEndpoints.realtimeAnalysis, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(this.config.apiHeaders || {})
      },
      body: JSON.stringify(payload),
      credentials: this.config.includeCredentials ? 'include' : 'same-origin'
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const result = await response.json();
    
    if (this.config.enableConsoleLogging) {
      console.log('✅ Real-time data sent:', result);
    }

    return result;

  } catch (error) {
    if (this.config.enableConsoleLogging) {
      console.error('❌ Real-time transmission error:', error);
    }
    throw error;
  }
}




  calculateVariance(values) {
    if (values.length === 0) return 0;
    const mean = values.reduce((a, b) => a + b, 0) / values.length;
    const variance = values.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / values.length;
    return variance;
  }

  showAuthenticationMessage(message = 'Authentication Required') {
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
        ">Unusual behavioral patterns detected. Please verify your identity.</p>
        <button onclick="this.parentElement.parentElement.remove()" style="
          background: #e74c3c;
          color: white;
          border: none;
          padding: 12px 24px;
          border-radius: 6px;
          font-size: 16px;
          cursor: pointer;
          transition: background 0.3s;
        ">
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

  

  // Method for React components to call when user logs out
  
  // Test method for registration user flow
  

  // Debug method to check current status
  getCollectionStatus() {
    return {
      auth_type: this.auth_type,
      isRegistrationPhase: this.isRegistrationPhase,
      baselineCollectionActive: this.baselineCollectionActive,
      isTracking: this.isTracking,
      transmissionActive: this.transmissionActive,
      userId: this.userId,
      sessionId: this.sessionId,
      actionCount: this.behavioralData?.actionCount || 0,
      dataPoints: {
        cursorMovements: this.behavioralData?.cursorMovements?.length || 0,
        keyPresses: this.behavioralData?.keyPressTimes?.length || 0,
        clicks: this.behavioralData?.clickTimestamps?.length || 0,
        scrollEvents: this.behavioralData?.scrollSpeeds?.length || 0
      },
      userLifecycleState: this.userLifecycleState,
      dashboardEntryTime: this.dashboardEntryTime
    };
  }

  // TEST FUNCTION - Call from browser console
 
}
// Factory function for creating configured instances
let __GBT_INSTANCE__ = null;

export function initGlobalBehaviorTracker(config = {}) {
  if (!__GBT_INSTANCE__) {
    __GBT_INSTANCE__ = new GlobalBehavioralTracker(config);
  }
  return __GBT_INSTANCE__;
}

export function getGlobalBehaviorTracker() {
  if (!__GBT_INSTANCE__) {
    console.warn('⚠️ GlobalBehaviorTracker not initialized. Call initGlobalBehaviorTracker() first.');
  }
  return __GBT_INSTANCE__;
}

// Default instance for backward compatibility
const globalBehavioralTracker = new GlobalBehavioralTracker();

// Expose globally for console testing
if (typeof window !== 'undefined') {
  window.globalBehavioralTracker = globalBehavioralTracker;
  window.initGlobalBehaviorTracker = initGlobalBehaviorTracker;
  window.getGlobalBehaviorTracker = getGlobalBehaviorTracker;
}

export default globalBehavioralTracker;
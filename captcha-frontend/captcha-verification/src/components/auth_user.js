import { useState, useEffect, useRef, useMemo, use } from "react";
import FingerprintJS from "@fingerprintjs/fingerprintjs";
import { useNavigate } from 'react-router-dom';
import "./captcha-form.css";



const Authenticate_user = () => {
  const prevpoint = useRef(null);
  const [usaiId, setUsaiId] = useState("");
  const [cursorMovements, setCursorMovements] = useState([]);
  const [cursorSpeeds, setCursorSpeeds] = useState([]);
  const [cursorAcceleration, setCursorAcceleration] = useState([]);
  const [cursorJitter, setCursorJitter] = useState([]);
  const [keyPressTimes, setKeyPressTimes] = useState([]);
  const [cursorCurvature, setCursorCurvature] = useState([]);
  const [keyHoldTimes, setKeyHoldTimes] = useState([]);
  const [clickTimes, setClickTimes] = useState([]);
  const [scrollSpeeds, setScrollSpeeds] = useState([]);
  const [scrollChanges, setScrollChanges] = useState(0);
  const [idleTime, setIdleTime] = useState(0);
  const [pasteDetected, setPasteDetected] = useState(false);
  const [message, setMessage] = useState("");
  const [honeypot, setHoneypot] = useState("");
  const [isBlocked, setIsBlocked] = useState(false);
  const [clickTimestamps, setClickTimestamps] = useState([]);
  const [lastKeyPress, setLastKeyPress] = useState(null);
  const [lastKeyDown, setLastKeyDown] = useState({});
  const [lastMouseMove, setLastMouseMove] = useState(null);
  const [lastClickTime, setLastClickTime] = useState(null);
  const [lastScroll, setLastScroll] = useState(0);
  const [latestSpeed, setLatestSpeed] = useState(0);
  const [allSpeeds, setAllSpeeds] = useState([]);
  const [lastUpdateTime, setLastUpdateTime] = useState(0);
  const [lastScrollTime, setLastScrollTime] = useState(Date.now());
  const [pasteTimestamp, setPasteTimestamp] = useState(null);
  const [cursorEntropy, setCursorEntropy] = useState(0);
  const [botFingerprintScore, setBotFingerprintScore] = useState(null);
  const [pageLoadTime, setPageLoadTime] = useState(null);
  const [submitTime, setSubmitTime] = useState(null);
  const [TabKeyCount, setTabkeycount] = useState(0);
  const [cursorAngles, setCursorAngles] = useState([]);

  const navigate = useNavigate();

  const goToHttpBotPage = () => {
    navigate('/http-bot-check');
  };


  const [postPasteActivity, setPostPasteActivity] = useState({
    keyPresses: 0,
    mouseMoves: 0,
    clicks: 0,
    timeToFirstAction: null,
    timeToLastAction: null,
    actionsAfterPaste: [],
    clipboardContent: null,
  });

  const [mouseTrajectory, setMouseTrajectory] = useState([]);
  const [keyboardPatterns, setKeyboardPatterns] = useState([]);
  const [deviceInfo, setDeviceInfo] = useState({});
  const [isAutomatedBrowser, setIsAutomatedBrowser] = useState(false);
  const [lastActionTime, setLastActionTime] = useState(Date.now());
  const [actionCount, setActionCount] = useState(0);
  const [suspiciousPatterns, setSuspiciousPatterns] = useState([]);
  const [botDetectionResults, setBotDetectionResults] = useState(null);


  const [mouseJitter, setMouseJitter] = useState([]); 
  const [microPauses, setMicroPauses] = useState([]); 
  const [hesitationTimes, setHesitationTimes] = useState([]);
  const [lastHoverStart, setLastHoverStart] = useState(null);
  const [deviceFingerprint, setDeviceFingerprint] = useState(null);

  const [canvasMetrics, setCanvasMetrics] = useState({
    winding: null,
    geometryLength: 0,
    textLength: 0,
  });

  const [missingCanvasFingerprint, setMissingCanvasFingerprint] =
    useState(true);
  const [audio_fp_entropy_low, setaudio_fp_entropy_low] = useState(null);
  const [evasionSignals, setEvasionSignals] = useState({});
  const [unusualScreenResolution, setUnusualScreenResolution] = useState({
    width_height: "0x0",
    inner_width: 0,
    device_pixel_ratio: 0,
    is_unusual: false,
    spoofedMismatch: false,
    aspectRatio: 0,
  });

  const [gpuInfo, setGpuInfo] = useState({
    gpu_name: null,
    vendor: null,
    renderer: null,
    webgl_info: null,
    capabilities: null,
    extensions: [],
    driver_info: null,
    graphics_api: null
  });

  const [gpublacklist, setgpublacklist] = useState({
    gpu_name_blacklisted: false,
    gpu_name: null,
  });

  const [timingMetrics, setTimingMetrics] = useState({});
  const [cursorMicroJitter, setCursorMicroJitter] = useState(0);
  const [pathEntropy, setPathEntropy] = useState(0);
  const [accelerationVariance, setAccelerationVariance] = useState(0);
  const [fittsDeviationScore, setFittsDeviationScore] = useState(0);
  const [idleResumeAngularJerk, setIdleResumeAngularJerk] = useState(0);
  const [thermalHoverNoise, setThermalHoverNoise] = useState(0);
  const [hoverPositions, setHoverPositions] = useState([]);

  function getWebGLFingerprint() {
    const canvas = document.createElement("canvas");
    const gl =
      canvas.getContext("webgl") || canvas.getContext("experimental-webgl");
    if (!gl) return { error: "No WebGL context" };

 
    const extensions = gl.getSupportedExtensions() || [];
    // Collect precision info
    const vertexFloat = gl.getShaderPrecisionFormat(
      gl.VERTEX_SHADER,
      gl.HIGH_FLOAT
    );
    const fragmentFloat = gl.getShaderPrecisionFormat(
      gl.FRAGMENT_SHADER,
      gl.HIGH_FLOAT
    );
    // Collect max texture size
    const maxTextureSize = gl.getParameter(gl.MAX_TEXTURE_SIZE);
    // Collect max renderbuffer size
    const maxRenderbufferSize = gl.getParameter(gl.MAX_RENDERBUFFER_SIZE);
    // Collect anti-aliasing info
    const antialias = gl.getContextAttributes().antialias;
    // Collect max vertex attribs
    const maxVertexAttribs = gl.getParameter(gl.MAX_VERTEX_ATTRIBS);
    // Collect max varying vectors
    const maxVaryingVectors = gl.getParameter(gl.MAX_VARYING_VECTORS);
    // Collect max vertex uniform vectors
    const maxVertexUniformVectors = gl.getParameter(
      gl.MAX_VERTEX_UNIFORM_VECTORS
    );
    // Collect max fragment uniform vectors
    const maxFragmentUniformVectors = gl.getParameter(
      gl.MAX_FRAGMENT_UNIFORM_VECTORS
    );

    // Timing test: render a large texture
    let timing = null;
    try {
      const start = performance.now();
      const testTex = gl.createTexture();
      gl.bindTexture(gl.TEXTURE_2D, testTex);
      gl.texImage2D(
        gl.TEXTURE_2D,
        0,
        gl.RGBA,
        1024,
        1024,
        0,
        gl.RGBA,
        gl.UNSIGNED_BYTE,
        null
      );
      gl.clear(gl.COLOR_BUFFER_BIT);
      gl.deleteTexture(testTex);
      timing = performance.now() - start;
    } catch (e) {
      timing = null;
    }

    return {
      extensions,
      vertexFloat,
      fragmentFloat,
      maxTextureSize,
      maxRenderbufferSize,
      antialias,
      maxVertexAttribs,
      maxVaryingVectors,
      maxVertexUniformVectors,
      maxFragmentUniformVectors,
      timing,
    };
  }

  useEffect(() => {
    const detectUnusualScreenResolution = () => {
      const width = window.screen.width;
      const height = window.screen.height;
      const innerWidth = window.innerWidth;
      const dpr = window.devicePixelRatio || 1;
      const aspectRatio = width / height;
      const spoofedMismatch = Math.abs(innerWidth - width) > 150;

      const reasons = [];

      if (width < 800 || height < 600) {
        reasons.push("🪟 Resolution too small (<800x600)");
      }

      if (aspectRatio < 1.2 || aspectRatio > 2.1) {
        reasons.push(`🧮 Unusual aspect ratio: ${aspectRatio.toFixed(2)}`);
      }

      if (spoofedMismatch) {
        reasons.push(
          `🕳️ Large mismatch between screen.width (${width}) and innerWidth (${innerWidth})`
        );
      }

      // 🔁 REMOVE overly strict 100px alignment check
      // Optionally: only trigger if BOTH dimensions are weird AND it's a small screen
      if (
        width % 100 !== 0 &&
        height % 100 !== 0 &&
        (width < 1000 || height < 800)
      ) {
        reasons.push(
          "📐 Weird screen size and misaligned to 100px (possible bot)"
        );
      }

      if (dpr < 1 || dpr > 3) {
        reasons.push(`🔍 Suspicious devicePixelRatio: ${dpr}`);
      }

      const isUnusual = reasons.length > 0;

      setUnusualScreenResolution({
        width_height: `${width}x${height}`,
        inner_width: innerWidth,
        device_pixel_ratio: dpr,
        is_unusual: isUnusual,
        spoofedMismatch,
        aspectRatio,
      });
    };

    detectUnusualScreenResolution();
  }, []);

  // Add this near the top, with your other useEffects
useEffect(() => {
  const handleMouseMoveHover = (e) => {
    const target = e.target;
    if (
      target.tagName === "INPUT" ||
      target.tagName === "BUTTON" ||
      target.id?.includes("input") ||
      target.id?.includes("btn")
    ) {
      setHoverPositions((prev) => [
        ...prev.slice(-99),
        { x: e.clientX, y: e.clientY, t: Date.now() }
      ]);
    }
  };
  document.addEventListener("mousemove", handleMouseMoveHover, true);
  return () => {
    document.removeEventListener("mousemove", handleMouseMoveHover, true);
  };
}, []);

// Add this to calculate thermalHoverNoise
useEffect(() => {
  if (hoverPositions.length > 5) {
    const xs = hoverPositions.map((p) => p.x);
    const ys = hoverPositions.map((p) => p.y);
    const mean = (arr) => arr.reduce((a, b) => a + b, 0) / arr.length;
    const stddev = (arr) => {
      const m = mean(arr);
      return Math.sqrt(arr.reduce((a, b) => a + Math.pow(b - m, 2), 0) / arr.length);
    };
    const noise = (stddev(xs) + stddev(ys)) / 2;
    setThermalHoverNoise(noise);
  } else {
    setThermalHoverNoise(0);
  }
}, [hoverPositions]);

  useEffect(() => {
  function detectCanvasSupport() {
  try {
    if (!window.HTMLCanvasElement) {
      setMissingCanvasFingerprint(true);
      return;
    }
    const canvas = document.createElement('canvas');
    if (!canvas) {
      setMissingCanvasFingerprint(true);
      return;
    }
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      setMissingCanvasFingerprint(true);
      return;
    }
    canvas.width = 200;
    canvas.height = 200;
    ctx.fillStyle = '#f60';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#069';
    ctx.font = '15px Arial';
    ctx.fillText('Canvas Fingerprint Test', 4, 45);
    ctx.strokeStyle = 'rgba(102, 204, 0, 0.7)';
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.lineTo(100, 100);
    ctx.stroke();

    let imageData;
    try {
      imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    } catch (err) {
      setMissingCanvasFingerprint(true);
      return;
    }
    if (!imageData || !imageData.data || imageData.data.length === 0) {
      setMissingCanvasFingerprint(true);
      return;
    }
    // Check for low pixel variance (all pixels same or all black)
    const data = imageData.data;
    const firstPixel = data[0];
    const allSame = data.every(v => v === firstPixel);
    const allZero = data.every(v => v === 0);
    if (allSame || allZero) {
      setMissingCanvasFingerprint(true);
      return;
    }
    // Check pixel entropy
    const counts = {};
    data.forEach(v => { counts[v] = (counts[v] || 0) + 1; });
    const probs = Object.values(counts).map(c => c / data.length);
    const entropy = -probs.reduce((sum, p) => sum + (p > 0 ? p * Math.log2(p) : 0), 0);
    if (entropy < 1.5) { // Very low entropy = blocked or fake
      setMissingCanvasFingerprint(true);
      return;
    }
    // Data URL check
    const dataUrl = canvas.toDataURL();
    if (!dataUrl || dataUrl.length < 100) {
      setMissingCanvasFingerprint(true);
      return;
    }
    setMissingCanvasFingerprint(false);
    setCanvasMetrics({
      width: canvas.width,
      height: canvas.height,
      totalPixels: data.length,
      entropy: entropy.toFixed(2),
      dataHash: Array.from(data.slice(0, 100)).join(',')
    });
  } catch (error) {
    setMissingCanvasFingerprint(true);
  }
}
  detectCanvasSupport();
}, []);

 

  useEffect(() => {
      const signals = {};
  
      // 1. DevTools Detection
      signals.devtoolsOpen = false;
      const threshold = 160;
      if (window.outerWidth - window.innerWidth > threshold || window.outerHeight - window.innerHeight > threshold) {
        signals.devtoolsOpen = true;
      }
      // Debugger trap
      let debuggerTriggered = false;
      try {
        const start = performance.now();
      
        const end = performance.now();
        debuggerTriggered = end - start > 100;
      } catch (e) {}
      signals.debuggerTrap = debuggerTriggered;
  
      // 2. Navigator Spoofing
      signals.navigatorSpoofed = false;
      const spoofProps = [
        'webdriver', 'languages', 'plugins', 'platform', 'userAgent', 'vendor', 'hardwareConcurrency', 'deviceMemory'
      ];
      spoofProps.forEach(prop => {
        if (navigator[prop] === undefined || navigator[prop] === null) signals.navigatorSpoofed = true;
      });
      if (navigator.webdriver) signals.navigatorSpoofed = true;
  
      // 3. Canvas Fingerprinting Resistance
      signals.canvasResistant = false;
      try {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = 'red';
        ctx.fillRect(0, 0, 10, 10);
        const data = canvas.toDataURL();
        if (!data || data.length < 100) signals.canvasResistant = true;
      } catch (e) { signals.canvasResistant = true; }
  
      // 4. Fake WebGL / Extension Trap
      signals.fakeWebGL = false;
      try {
        const canvas = document.createElement('canvas');
        const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
        if (!gl) signals.fakeWebGL = true;
        else {
          const ext = gl.getSupportedExtensions();
          if (!ext || ext.length < 5) signals.fakeWebGL = true;
          if (ext && ext.includes('WEBGL_debug_renderer_info') === false) signals.fakeWebGL = true;
        }
      } catch (e) { signals.fakeWebGL = true; }
  
      // 5. User-Agent Anomalies
      signals.uaAnomaly = false;
      const ua = navigator.userAgent;
      if (!ua || ua.length < 20 || /Headless|Phantom|Puppeteer|Selenium|Playwright/i.test(ua)) signals.uaAnomaly = true;
      if (/Linux.*Android/.test(ua) && !/Mobile/.test(ua)) signals.uaAnomaly = true;
  
      // 6. Plugin/Fonts/Features Check
      signals.pluginsMissing = navigator.plugins && navigator.plugins.length === 0;
      signals.fontsMissing = false;
      try {
        const testFont = 'Comic Sans MS';
        const span = document.createElement('span');
        span.style.fontFamily = testFont;
        span.innerText = 'test';
        document.body.appendChild(span);
        const fontUsed = window.getComputedStyle(span).fontFamily;
        if (!fontUsed || fontUsed.indexOf(testFont) === -1) signals.fontsMissing = true;
        document.body.removeChild(span);
      } catch (e) { signals.fontsMissing = true; }
      signals.featuresMissing = !('geolocation' in navigator) || !('mediaDevices' in navigator);
  
      // 7. JavaScript Timing Inconsistencies
      signals.timingInconsistent = false;
      let evalTime = 0;
      try {
        const start = performance.now();
        for (let i = 0; i < 1e5; i++) { Math.sqrt(i); }
        evalTime = performance.now() - start;
        if (evalTime < 1 || evalTime > 100) signals.timingInconsistent = true;
      } catch (e) { signals.timingInconsistent = true; }
  
      // 8. Replay Attack Detection (simple: identical mouse/key patterns)
      signals.replayAttack = false;
      // Compute summary metrics
      function stddev(arr) {
        if (arr.length < 2) return 0;
        const mean = arr.reduce((a, b) => a + b, 0) / arr.length;
        const variance = arr.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / arr.length;
        return Math.sqrt(variance);
      }
      function shannonEntropy(arr) {
        if (!arr.length) return 0;
        const counts = {};
        arr.forEach(v => { counts[v] = (counts[v] || 0) + 1; });
        const probs = Object.values(counts).map(c => c / arr.length);
        return -probs.reduce((sum, p) => sum + (p > 0 ? p * Math.log2(p) : 0), 0);
      }
      if (cursorMovements.length > 10) {
        // cursorMicroJitter
        const deltas = [];
        for (let i = 1; i < cursorMovements.length; i++) {
          const dx = cursorMovements[i].x - cursorMovements[i - 1].x;
          const dy = cursorMovements[i].y - cursorMovements[i - 1].y;
          deltas.push(Math.sqrt(dx * dx + dy * dy));
        }
        const microJitter = stddev(deltas);
        setCursorMicroJitter(microJitter);
        // pathEntropy
        const angles = [];
        for (let i = 1; i < cursorMovements.length; i++) {
          const dx = cursorMovements[i].x - cursorMovements[i - 1].x;
          const dy = cursorMovements[i].y - cursorMovements[i - 1].y;
          angles.push(Math.atan2(dy, dx).toFixed(2));
        }
        const entropy = shannonEntropy(angles);
        setPathEntropy(entropy);
        // accelerationVariance
        const speeds = [];
        for (let i = 1; i < cursorMovements.length; i++) {
          const dt = (cursorMovements[i].t - cursorMovements[i - 1].t) / 1000;
          const dx = cursorMovements[i].x - cursorMovements[i - 1].x;
          const dy = cursorMovements[i].y - cursorMovements[i - 1].y;
          speeds.push(Math.sqrt(dx * dx + dy * dy) / (dt || 1));
        }
        const accels = [];
        for (let i = 1; i < speeds.length; i++) {
          const dt = (cursorMovements[i].t - cursorMovements[i - 1].t) / 1000;
          accels.push((speeds[i] - speeds[i - 1]) / (dt || 1));
        }
        const accelVar = stddev(accels);
        setAccelerationVariance(accelVar);
        // fittsDeviationScore
        const fittsScores = [];
        for (let i = 1; i < cursorMovements.length; i++) {
          const dt = (cursorMovements[i].t - cursorMovements[i - 1].t) / 1000;
          const dx = cursorMovements[i].x - cursorMovements[i - 1].x;
          const dy = cursorMovements[i].y - cursorMovements[i - 1].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          const predicted = Math.log2(dist / 50 + 1);
          fittsScores.push(Math.abs(dt - predicted));
        }
        const fittsDev = stddev(fittsScores);
        setFittsDeviationScore(fittsDev);
        // idleResumeAngularJerk
        let idleJerk = 0;
        if (cursorAngles.length > 5) {
          const jerks = [];
          for (let i = 1; i < cursorAngles.length; i++) {
            jerks.push(Math.abs(cursorAngles[i] - cursorAngles[i - 1]));
          }
          idleJerk = stddev(jerks);
          setIdleResumeAngularJerk(idleJerk);
        }
        // thermalHoverNoise
        let thermalNoise = 0;
        if (hoverPositions.length > 5) {
          const xs = hoverPositions.map(p => p.x);
          const ys = hoverPositions.map(p => p.y);
          thermalNoise = (stddev(xs) + stddev(ys)) / 2;
          setThermalHoverNoise(thermalNoise);
        }
        // Add metrics to evasionSignals
        signals.cursorMicroJitter = microJitter;
        signals.pathEntropy = entropy;
        signals.accelerationVariance = accelVar;
        signals.fittsDeviationScore = fittsDev;
        signals.idleResumeAngularJerk = idleJerk;
        signals.thermalHoverNoise = thermalNoise;
      }
      setEvasionSignals(signals);
    }, [cursorMovements, cursorAngles, hoverPositions]);
  

  useEffect(() => {
    const detectGPUInfo = () => {
      try {
        const canvas = document.createElement("canvas");
        const gl = canvas.getContext("webgl2") || 
                  canvas.getContext("webgl") || 
                  canvas.getContext("experimental-webgl");

        if (!gl) {
          setGpuInfo({
            gpu_name: "WebGL not supported",
            vendor: "Not available",
            renderer: "Not available",
            webgl_info: { version: "Not supported", context_type: "None" },
            capabilities: null,
            extensions: [],
            driver_info: "Not available",
            graphics_api: "None"
          });
          return;
        }

        const debugInfo = gl.getExtension("WEBGL_debug_renderer_info");
        
        // Get detailed GPU information whether or not we have debug info
        const contextAttributes = gl.getContextAttributes();
        const params = {
          vendor: gl.getParameter(gl.VENDOR),
          renderer: gl.getParameter(gl.RENDERER),
          version: gl.getParameter(gl.VERSION),
          shadingLanguageVersion: gl.getParameter(gl.SHADING_LANGUAGE_VERSION)
        };

        // Get advanced capabilities
        const capabilities = {
          ...contextAttributes,
          maxTextureSize: gl.getParameter(gl.MAX_TEXTURE_SIZE),
          maxViewportDims: gl.getParameter(gl.MAX_VIEWPORT_DIMS),
          maxTextureUnits: gl.getParameter(gl.MAX_TEXTURE_IMAGE_UNITS),
          maxVertexAttribs: gl.getParameter(gl.MAX_VERTEX_ATTRIBS),
          maxVaryingVectors: gl.getParameter(gl.MAX_VARYING_VECTORS),
          maxVertexUniformVectors: gl.getParameter(gl.MAX_VERTEX_UNIFORM_VECTORS),
          maxFragmentUniformVectors: gl.getParameter(gl.MAX_FRAGMENT_UNIFORM_VECTORS)
        };

        let renderer, vendor;
        
        if (debugInfo) {
          renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
          vendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
        } else {
          renderer = params.renderer;
          vendor = params.vendor;
        }

        // Get all available extensions and capabilities
        const extensions = gl.getSupportedExtensions() || [];
        
        // Enhanced WebGL capabilities analysis
        const performanceMetrics = {};
        
        // Use Promise.all to handle all measurements
        Promise.all([
          measureRenderPerformance(gl),
          measureOperationConsistency(gl),
          measureFrameVariability(gl)
        ]).then(([renderTiming, consistencyScore, frameVariability]) => {
          performanceMetrics.renderTiming = renderTiming;
          performanceMetrics.consistencyScore = consistencyScore;
          performanceMetrics.frameVariability = frameVariability;
          
          // Update GPU info with the new metrics
          setGpuInfo(currentInfo => ({
            ...currentInfo,
            performance_metrics: performanceMetrics
          }));
        });

        // Get WebGL version and context type info
        const webgl_info = {
          version: params.version,
          context_type: gl instanceof WebGL2RenderingContext ? "WebGL 2.0" : "WebGL 1.0",
          shading_version: params.shadingLanguageVersion
        };

        // Set comprehensive GPU info with performance characteristics
        setGpuInfo({
          gpu_name: renderer || "Limited information available",
          vendor: vendor || params.vendor || "Limited access",
          renderer: renderer || params.renderer || "Limited access",
          webgl_info: webgl_info,
          capabilities: capabilities,
          extensions: extensions,
          driver_info: params.version,
          graphics_api: gl instanceof WebGL2RenderingContext ? "WebGL 2.0" : "WebGL 1.0",
          performance_metrics: performanceMetrics
        });

      } catch (error) {
        console.error("Error gathering GPU information:", error);
        setGpuInfo({
          gpu_name: "Error detecting GPU",
          vendor: "Error",
          renderer: "Error",
          webgl_info: { version: "Error", context_type: "Error" },
          capabilities: null,
          extensions: [],
          driver_info: "Error",
          graphics_api: "Error",
          performance_metrics: null
        });
      }
    };

    // Helper function to measure render timing consistency
    const measureRenderPerformance = async (gl) => {
      const samples = 10;
      const timings = [];
      
      for (let i = 0; i < samples; i++) {
        const start = performance.now();
        // Perform a standard rendering operation
        const testTex = gl.createTexture();
        gl.bindTexture(gl.TEXTURE_2D, testTex);
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 256, 256, 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
        gl.clear(gl.COLOR_BUFFER_BIT);
        await new Promise(resolve => setTimeout(resolve, 16)); // simulate frame timing
        gl.deleteTexture(testTex);
        timings.push(performance.now() - start);
      }
      
      return {
        averageTiming: timings.reduce((a, b) => a + b, 0) / samples,
        variability: calculateVariability(timings),
        pattern: analyzeTimingPattern(timings)
      };
    };

    // Helper function to measure operation consistency
    const measureOperationConsistency = async (gl) => {
      const operations = [];
      for (let i = 0; i < 5; i++) {
        const start = performance.now();
        // Perform different GL operations
        gl.clear(gl.COLOR_BUFFER_BIT);
        gl.flush();
        await new Promise(resolve => setTimeout(resolve, 16));
        operations.push(performance.now() - start);
      }
      return {
        consistency: calculateVariability(operations),
        naturalVariation: hasNaturalVariation(operations)
      };
    };

    // Helper function to measure frame timing variability
    const measureFrameVariability = async (gl) => {
      const frameTimings = [];
      for (let i = 0; i < 10; i++) {
        const start = performance.now();
        gl.clear(gl.COLOR_BUFFER_BIT);
        await new Promise(resolve => requestAnimationFrame(resolve));
        frameTimings.push(performance.now() - start);
      }
      return {
        averageFrameTime: frameTimings.reduce((a, b) => a + b, 0) / frameTimings.length,
        frameTimeVariability: calculateVariability(frameTimings)
      };
    };

    // Helper function to calculate variability
    const calculateVariability = (numbers) => {
      const avg = numbers.reduce((a, b) => a + b, 0) / numbers.length;
      const variance = numbers.reduce((a, b) => a + Math.pow(b - avg, 2), 0) / numbers.length;
      return Math.sqrt(variance);
    };

    // Helper function to check for natural variation in timings
    const hasNaturalVariation = (numbers) => {
      const variability = calculateVariability(numbers);
      const avg = numbers.reduce((a, b) => a + b, 0) / numbers.length;
      return variability > avg * 0.1; // Natural operations should have some variation
    };

    // Helper function to analyze timing patterns
    const analyzeTimingPattern = (timings) => {
      // Check for suspiciously consistent patterns
      const diffs = timings.slice(1).map((t, i) => Math.abs(t - timings[i]));
      const tooConsistent = diffs.every(d => d < 0.1);
      const tooRegular = diffs.every(d => Math.abs(d - diffs[0]) < 0.1);
      
      return {
        hasNaturalVariation: !tooConsistent && !tooRegular,
        consistency: diffs.reduce((a, b) => a + b, 0) / diffs.length
      };
    };

    detectGPUInfo();
  }, []);

  useEffect(() => {
    const handleMouseMoveangle = (e) => {
      const currentPoint = { x: e.clientX, y: e.clientY };

      if (prevpoint.current) {
        const dx = currentPoint.x - prevpoint.current.x;
        const dy = currentPoint.y - prevpoint.current.y;

        // Calculate angle

        const angleRad = Math.atan2(dy, dx);
        const angleDeg = (angleRad * 180) / Math.PI;
        const normalized = (angleDeg + 360) % 360;

        setCursorAngles((prev) => [...prev.slice(-50), normalized]);
      }

      prevpoint.current = currentPoint;
    };

    document.addEventListener("mousemove", handleMouseMoveangle);

    return () => {
      document.removeEventListener("mousemove", handleMouseMoveangle);
    };
  }, []);

  const handleTabKey = (event) => {
    if (event.key === "Tab") {
      setTabkeycount((prev) => prev + 1);
    }
  };

  const calculateCursorEntropy = (movements) => {
    if (movements.length < 3) return 0;

    const angles = [];
    for (let i = 1; i < movements.length; i++) {
      const dx = movements[i].x - movements[i - 1].x;
      const dy = movements[i].y - movements[i - 1].y;
      const angle = (Math.atan2(dy, dx) * 180) / Math.PI;
      angles.push((angle + 360) % 360); // Normalize to 0–360
    }

    const bins = new Array(8).fill(0);
    const binSize = 360 / bins.length;

    angles.forEach((angle) => {
      const binIndex = Math.floor(angle / binSize);
      bins[binIndex]++;
    });

    const total = bins.reduce((a, b) => a + b, 0);
    const probabilities = bins.map((count) =>
      count === 0 ? 0 : count / total
    );
    const entropy = -probabilities.reduce(
      (sum, p) => sum + (p > 0 ? p * Math.log2(p) : 0),
      0
    );

    return entropy.toFixed(3);
  };

  const handlePaste = (event) => {
    setPasteDetected(true);
    const pasteTime = Date.now();
    setPasteTimestamp(pasteTime);

    // Get clipboard content
    const clipboardContent = event.clipboardData.getData("text");

    setPostPasteActivity({
      keyPresses: 0,
      mouseMoves: 0,
      clicks: 0,
      timeToFirstAction: null,
      timeToLastAction: null,
      actionsAfterPaste: [],
      clipboardContent: clipboardContent,
    });
  };

  // Add this new function to track post-paste actions
  const trackPostPasteAction = (actionType) => {
    const now = Date.now();
    setPostPasteActivity((prev) => {
      const newActions = [
        ...prev.actionsAfterPaste,
        { type: actionType, timestamp: now },
      ];
      const timeToFirst = prev.timeToFirstAction || now - pasteTimestamp;
      const timeToLast = now - pasteTimestamp;

      return {
        ...prev,
        [actionType]: prev[actionType] + 1,
        timeToFirstAction: timeToFirst,
        timeToLastAction: timeToLast,
        actionsAfterPaste: newActions,
      };
    });
  };

  useEffect(() => {
    let idleTimer;
    document.addEventListener("paste", handlePaste);

    return () => document.removeEventListener("paste", handlePaste);
  }, []);

  useEffect(() => {
    const handleUserActivity = () => {
      // idleTime(0);
      setIdleTime(Date.now());
    };

    // List of events that count as activity
    const events = ["mousemove", "keydown", "keypress", "scroll", "click"];
    events.forEach((event) =>
      document.addEventListener(event, handleUserActivity)
    );

    // Interval to increment idleTime every second if user is idle
    const interval = setInterval(() => {
      if (Date.now() - setIdleTime >= 1000) {
        setIdleTime((prev) => prev + 1);
      }
    }, 1000);

    return () => {
      events.forEach((event) =>
        document.removeEventListener(event, handleUserActivity)
      );
      clearInterval(interval);
    };
  }, [setIdleTime]);

  useEffect(() => {
    setPageLoadTime(Date.now());

    // Timing & Latency Analysis
    const metrics = {};
    // 1. Navigation Timing
    if (window.performance && window.performance.timing) {
      const t = window.performance.timing;
      metrics.ttfb = t.responseStart - t.requestStart;
      metrics.domInteractive = t.domInteractive - t.navigationStart;
      metrics.domContentLoaded = t.domContentLoadedEventEnd - t.navigationStart;
      metrics.loadTime = t.loadEventEnd - t.navigationStart;
    }

    // 2. Resource Timing (XHR/Fetch)
    const testUrl = window.location.origin + '/favicon.ico';
    const fetchStart = performance.now();
    fetch(testUrl)
      .then(res => res.blob())
      .then(() => {
        const fetchEnd = performance.now();
        metrics.xhrFetchTime = fetchEnd - fetchStart;
        metrics.rtt = metrics.xhrFetchTime; // Approximate RTT
        setTimingMetrics(prev => ({ ...prev, ...metrics }));
      })
      .catch(() => {
        setTimingMetrics(prev => ({ ...prev, ...metrics }));
      });

    // 3. Jitter Calculation (variation in repeated fetch)
    const jitterSamples = [];
    let jitterCount = 0;
    const measureJitter = () => {
      const start = performance.now();
      fetch(testUrl)
        .then(res => res.blob())
        .then(() => {
          const end = performance.now();
          jitterSamples.push(end - start);
          jitterCount++;
          if (jitterCount < 5) {
            measureJitter();
          } else {
            const mean = jitterSamples.reduce((a, b) => a + b, 0) / jitterSamples.length;
            const variance = jitterSamples.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / jitterSamples.length;
            metrics.jitter = Math.sqrt(variance).toFixed(2);
            setTimingMetrics(prev => ({ ...prev, ...metrics }));
          }
        });
    };
    measureJitter();

    // 4. Clock Skew / Drift Detection
    setTimeout(() => {
      const dateNow = Date.now();
      const perfNow = performance.now();
      metrics.clockSkew = Math.abs(dateNow - (window.performance.timing.navigationStart + perfNow));
      setTimingMetrics(prev => ({ ...prev, ...metrics }));
    }, 2000);

    // 5. Eval/Math Timing
    setTimeout(() => {
      const mathStart = performance.now();
      let dummy = 0;
      for (let i = 0; i < 1e6; i++) {
        dummy += Math.sqrt(i) * Math.sin(i);
      }
      const mathEnd = performance.now();
      metrics.evalMathTiming = (mathEnd - mathStart).toFixed(2);
      setTimingMetrics(prev => ({ ...prev, ...metrics }));
    }, 1000);
  }, []);

  useEffect(() => {
    if (cursorMovements.length > 0) {
      console.log("Updated Cursor Movements:", [...cursorMovements]); // Ensures fresh movements are logged
    }
  }, [cursorMovements]);

 

  function detectStealthBot(result) {
    // Initialize state variables first
    let gpu_name_blacklisted = false;
    let matchedTerm = null;
    let isStealthBot = false;
    let advancedSuspicious = false;

    // Get renderer and WebGL info
    const renderer = result.components?.webGL?.value?.renderer || "unknown";
    const lowerRenderer = renderer.toLowerCase();
    const webglFingerprint = getWebGLFingerprint();

    // Enhanced check for automation-specific patterns in WebGL extensions
    const extensionPatterns = {
      suspicious: [
        "WEBGL_debug_shaders",
        "WEBGL_lose_context",
        "WEBGL_multi_draw",
        "EXT_disjoint_timer_query",
        "EXT_disjoint_timer_query_webgl2",
        "WEBGL_debug_renderer_info",
        "WEBGL_compressed_texture_s3tc",
        "WEBGL_compressed_texture_etc1",
        "WEBGL_compressed_texture_pvrtc",
      ],
      automation: [
        "WEBGL_color_buffer_float",
        "EXT_color_buffer_float",
        "EXT_float_blend",
        "EXT_texture_filter_anisotropic",
      ],
    };
    const extensions = webglFingerprint.extensions || [];

    // Known bot entropy values (common in automation tools)
    const knownBotEntropyValues = [5.129283016944964, 5.129283, 5.12928];

    // Whitelist of legitimate ANGLE renderer strings
    const LEGIT_ANGLE_WHITELIST = [
      "angle (intel, intel(r) iris(r) xe graphics (0x0000a7a1) direct3d11 vs_5_0 ps_5_0, d3d11)",
      "angle (intel, intel(r) uhd graphics (0x0000a7a1) direct3d11 vs_5_0 ps_5_0, d3d11)",
      "angle (nvidia, nvidia geforce gtx 1050 (0x1c81) direct3d11 vs_5_0 ps_5_0, d3d11)",
      "angle (amd, amd radeon rx 580 (0x67df) direct3d11 vs_5_0 ps_5_0, d3d11)",
    ];

    let rendererSuspicious = false;
    if (renderer && renderer !== "unknown" && renderer !== "") {
      // First check against blacklist with improved logic
      

      // Stronger ANGLE renderer detection
      if (lowerRenderer.includes("angle (") && !rendererSuspicious) {
        // If not in whitelist, flag as suspicious
        const isLegitAngle = LEGIT_ANGLE_WHITELIST.some(
          (legit) => lowerRenderer === legit
        );
        if (!isLegitAngle) {
          rendererSuspicious = true;
          matchedTerm = "ANGLE renderer not whitelisted";
        }
      }
    } else {
      rendererSuspicious = true;
      matchedTerm = "unknown/empty renderer";

      // Additional checks for distinguishing real browsers from automation when renderer is unknown
      const extensionPatterns = {
        // Core WebGL extensions that should be present in real browsers
        required: [
          "WEBGL_debug_renderer_info",
          "EXT_texture_filter_anisotropic",
          "WEBGL_compressed_texture_s3tc",
          "WEBGL_depth_texture",
        ],
        // Extensions that are suspicious if ALL are present (common in automation)
        suspicious: [
          "WEBGL_debug_shaders",
          "WEBGL_lose_context",
          "WEBGL_multi_draw",
          "EXT_disjoint_timer_query",
        ],
      };

      const extensions = webglFingerprint.extensions || [];
      const hasAllRequired = extensionPatterns.required.every((ext) =>
        extensions.includes(ext)
      );
      const hasAllSuspicious = extensionPatterns.suspicious.every((ext) =>
        extensions.includes(ext)
      );

      // Check for suspiciously perfect WebGL capabilities
      const perfectCapabilities =
        webglFingerprint.maxTextureSize === 16384 &&
        webglFingerprint.maxRenderbufferSize === 16384 &&
        webglFingerprint.maxVertexAttribs === 16 &&
        webglFingerprint.maxVaryingVectors === 30 &&
        webglFingerprint.maxVertexUniformVectors === 4096 &&
        webglFingerprint.maxFragmentUniformVectors === 1024;

      // If we have unknown renderer but everything else looks too perfect, it's suspicious
      if (hasAllRequired && hasAllSuspicious && perfectCapabilities) {
        advancedSuspicious = true;
        matchedTerm = "unknown renderer with suspicious WebGL pattern";
      }
    }

    const extEntropy = (() => {
      const ext = webglFingerprint.extensions || [];
      if (!ext.length) return 0;
      const map = {};
      ext.forEach((e) => {
        map[e] = (map[e] || 0) + 1;
      });
      let entropy = 0;
      const len = ext.length;
      for (const k in map) {
        const p = map[k] / len;
        entropy -= p * Math.log2(p);
      }
      return entropy;
    })();

    // 2. Check for suspiciously low max texture size, renderbuffer size, vertex attribs, etc.
    const suspiciousWebGL =
      (webglFingerprint.maxTextureSize &&
        webglFingerprint.maxTextureSize < 2048) ||
      (webglFingerprint.maxRenderbufferSize &&
        webglFingerprint.maxRenderbufferSize < 2048) ||
      (webglFingerprint.maxVertexAttribs &&
        webglFingerprint.maxVertexAttribs < 8) ||
      (webglFingerprint.maxVaryingVectors &&
        webglFingerprint.maxVaryingVectors < 8) ||
      (webglFingerprint.maxVertexUniformVectors &&
        webglFingerprint.maxVertexUniformVectors < 128) ||
      (webglFingerprint.maxFragmentUniformVectors &&
        webglFingerprint.maxFragmentUniformVectors < 64);

    // 3. Timing test: if rendering is very slow, likely software/virtualized
    const suspiciousTiming =
      webglFingerprint.timing !== null && webglFingerprint.timing > 30;

    // 4. Low entropy in extensions/features (bots often have generic/short lists)
    const suspiciousEntropy = extEntropy < 2.5;

    // 5. Check for missing anti-aliasing (bots often disable)
    const suspiciousAntialias = webglFingerprint.antialias === false;

    // 6. Check for generic/empty precision info
    const suspiciousPrecision =
      (webglFingerprint.vertexFloat &&
        webglFingerprint.vertexFloat.precision < 16) ||
      (webglFingerprint.fragmentFloat &&
        webglFingerprint.fragmentFloat.precision < 16);
    if (
      suspiciousWebGL ||
      suspiciousTiming ||
      suspiciousEntropy ||
      suspiciousAntialias ||
      suspiciousPrecision
    ) {
      advancedSuspicious = true;
      matchedTerm = matchedTerm
        ? matchedTerm + " + WebGL anomaly"
        : "WebGL anomaly";
    }

    // Stealth fingerprint flags
    const webdriverFlag = navigator.webdriver === true;
    const pluginMissing = navigator.plugins.length === 0;
    const langMissing = navigator.languages.length === 0;
    const hasChromeRuntime = !!(window.chrome && window.chrome.runtime);

    // Advanced stealth checks for undetected_chromedriver and similar tools
    const suspiciousEnvChecks = [
      !(
        navigator.permissions &&
        typeof navigator.permissions.query === "function"
      ),
      !("Notification" in window),
      !("localStorage" in window && "sessionStorage" in window),
      !("ontouchstart" in window),
      !document.createElement("canvas").getContext("webgl2"),
      !("RTCPeerConnection" in window),
      !("AudioContext" in window || "webkitAudioContext" in window),
      !("getBattery" in navigator),
      !hasChromeRuntime,
      !navigator.userAgent.includes("Chrome"),
      navigator.userAgent.includes("Headless"),
      navigator.userAgent.includes("Puppeteer"),
      navigator.userAgent.includes("Selenium"),
      navigator.userAgent.includes("HeadlessChrome"),
      !(navigator.deviceMemory > 0),
      !(navigator.hardwareConcurrency > 0),
      pluginMissing,
      langMissing,
      webdriverFlag,
    ];

    // If ANGLE renderer and any suspicious environment feature, mark as suspicious
    let envSuspicious = false;
    if (
      lowerRenderer.includes("angle (") &&
      suspiciousEnvChecks.filter(Boolean).length > 0
    ) {
      envSuspicious = true;
      matchedTerm = "ANGLE + suspicious environment";
    }

    // Enhanced canvas/audio entropy check with more strict patterns
    let entropyLow = null;
    if (result.components?.audio && result.components.audio.value) {
      const noise = result.components.audio.value.noise || "";
      const seed = result.components.audio.value.seed || "";
      const noiseLength = noise.length;
      const seedLength = seed.length;

      // Check for repeating patterns that are common in automated browsers
      const hasRepeatingPattern = (str) => {
        if (str.length < 4) return false;
        const patterns = str.match(/(.+?)\1+/g) || [];
        return patterns.some(p => p.length > str.length / 2);
      };

      // Check for sequential patterns (common in automation)
      const hasSequentialPattern = (str) => {
        const seq = "0123456789abcdefghijklmnopqrstuvwxyz";
        return seq.includes(str.toLowerCase()) || seq.split('').reverse().join('').includes(str.toLowerCase());
      };

      function calculateEntropy(str) {
        if (!str || str.length === 0) return 0;
        const map = {};
        for (let i = 0; i < str.length; i++) {
          map[str[i]] = (map[str[i]] || 0) + 1;
        }
        let entropy = 0;
        const len = str.length;
        for (const k in map) {
          const p = map[k] / len;
          entropy -= p * Math.log2(p);
        }
        return entropy;
      }
      const noiseEntropy = calculateEntropy(noise);
      if (noiseLength === 0 && seedLength === 0) {
        entropyLow = true; // No audio data is suspicious
      } else {
        const suspiciousPatterns = [
          noiseLength < 20 || noiseLength > 1000, // Abnormal noise length
          seedLength < 10 || seedLength > 500,    // Abnormal seed length
          noiseEntropy < 3.5,                     // Low entropy
          noiseEntropy === 5.129283016944964,     // Known bot entropy value
          /^([0-9])\1+$/.test(noise),            // Repeating numbers
          /^([a-zA-Z])\1+$/.test(noise),         // Repeating letters
          hasRepeatingPattern(noise),             // Complex repeating patterns
          hasSequentialPattern(noise),            // Sequential patterns
          noise === seed,                         // Identical noise and seed
          Math.abs(noiseEntropy - seedLength) < 0.0001, // Suspiciously precise relationship
          /^[0-9]+$/.test(noise) || /^[a-zA-Z]+$/.test(noise), // Only numbers or only letters
        ];
        
        entropyLow = suspiciousPatterns.filter(Boolean).length >= 2; // Require multiple suspicious patterns
      }
      if (entropyLow && lowerRenderer.includes("angle (")) {
        gpu_name_blacklisted = true;
        matchedTerm = "ANGLE + low audio entropy";
      }
    }    

    // Check for artificial precision patterns first
    const precisionTooUniform =
      webglFingerprint.vertexFloat &&
      webglFingerprint.fragmentFloat &&
      webglFingerprint.vertexFloat.precision ===
        webglFingerprint.fragmentFloat.precision &&
      webglFingerprint.vertexFloat.rangeMin ===
        webglFingerprint.fragmentFloat.rangeMin &&
      webglFingerprint.vertexFloat.rangeMax ===
        webglFingerprint.fragmentFloat.rangeMax;

    const perfectCapabilities =
      (webglFingerprint.maxTextureSize === 16384 ||
        webglFingerprint.maxTextureSize === 8192) &&
      (webglFingerprint.maxRenderbufferSize === 16384 ||
        webglFingerprint.maxRenderbufferSize === 8192) &&
      webglFingerprint.maxVertexAttribs >= 15 &&
      webglFingerprint.maxVaryingVectors >= 29 &&
      webglFingerprint.maxVertexUniformVectors >= 4095 &&
      webglFingerprint.maxFragmentUniformVectors >= 1023;

    const tooConsistent =
      extensions.length >= 25 && 
      extensionPatterns.automation.every((ext) => extensions.includes(ext)) && 
      perfectCapabilities && // Has perfect or near-perfect capabilities
      Math.abs(webglFingerprint.timing - 0.15) < 0.05;

    const webGLRisk = [
      perfectCapabilities && tooConsistent, // Too perfect setup
      precisionTooUniform && extensions.length >= 25, 
      suspiciousWebGL || suspiciousTiming, // Basic WebGL anomalies
      suspiciousAntialias && extensions.length > 20, // Suspicious antialiasing config
    ].filter(Boolean).length;

    

    // Using the already declared extensionPatterns and extensions variables

    // More sophisticated capability pattern detection
    

    // Check for exact matching of known automation patterns
    const hasAllSuspicious = extensionPatterns.suspicious.every((ext) =>
      extensions.includes(ext)
    );

    // Check for suspiciously consistent capabilities (too perfect)
     // Suspiciously consistent timing

    const suspiciousEnvScore = suspiciousEnvChecks.filter(Boolean).length;

    // Final bot decision with weighted signals
    let suspiciousCount = 0;

    // Only count unknown renderer as suspicious if other signals are present
    if (rendererSuspicious) {
      if (renderer === "unknown" || renderer === "") {
        // Check if WebGL features look legitimate
        const hasLegitWebGLFeatures =
          !suspiciousWebGL &&
          !suspiciousTiming &&
          !suspiciousEntropy &&
          !suspiciousAntialias &&
          !suspiciousPrecision &&
          extEntropy > 4.5; // High entropy indicates real GPU

        if (!hasLegitWebGLFeatures) {
          suspiciousCount += 1.0; // Reduced from 1.5
        }
      } else {
        suspiciousCount++;
      }
    }

    // Enhanced WebGL anomaly detection
    if (advancedSuspicious) {
      if (renderer === "unknown" || renderer === "") {
        // Check for highly suspicious combinations with stronger heuristics
        const highlyUnnatural =
          (perfectCapabilities || tooConsistent) && // Suspiciously perfect or consistent values
          (hasAllSuspicious || precisionTooUniform) && // Automation-related extensions or uniform precision
          (webglFingerprint.timing < 0.2 ||
            Math.abs(webglFingerprint.timing - 0.15) < 0.05); // Too fast or suspiciously consistent

        // Additional checks for stealth techniques
        // Enhanced detection of stealth automation patterns
        const knownBotEntropyValues = [5.129283016944964, 5.129283, 5.12928];
        const stealthIndicators = [
          // Primary indicators (higher confidence)
          knownBotEntropyValues.some(
            (value) => Math.abs(extEntropy - value) < 0.0001
          ), // Exact known bot entropy match
          Math.floor(extEntropy * 1000000) ===
            Math.floor(5.129283016944964 * 1000000), // Ultra-precise entropy match
          perfectCapabilities && tooConsistent, // Too-perfect WebGL setup
          precisionTooUniform && extensions.length >= 25, // Uniform precision with many extensions

          // Secondary indicators (suspicious patterns)
          extensionPatterns.automation.every((ext) => extensions.includes(ext)),
          extensions.length > 30,
          webglFingerprint.timing !== null &&
            Math.abs(webglFingerprint.timing - 0.15) < 0.02,

          // Hardware inconsistencies
          webglFingerprint.maxTextureSize === 16384 &&
            webglFingerprint.maxRenderbufferSize === 16384,
          webglFingerprint.vertexFloat?.precision ===
            webglFingerprint.fragmentFloat?.precision,

          // Known automation patterns
          result.components?.webGL?.value?.vendor ===
            result.components?.webGL?.value?.renderer,
          !webglFingerprint.antialias && extensions.length > 20,

          // Additional stealth indicators
          !navigator.hardwareConcurrency || navigator.hardwareConcurrency === 4,
          !navigator.deviceMemory || navigator.deviceMemory === 8,
          navigator.plugins?.length === 0 && extensions.length > 15,
          typeof navigator.languages === "object" &&
            navigator.languages.length === 1,
        ];

        // Calculate weighted stealth score
        const primaryIndicators =
          stealthIndicators.slice(0, 4).filter(Boolean).length * 2; // Primary indicators count double
        const secondaryIndicators = stealthIndicators
          .slice(4)
          .filter(Boolean).length;
        const stealthScore = primaryIndicators + secondaryIndicators;

        // More aggressive scoring for known bot patterns
        if (stealthScore >= 6) {
          suspiciousCount += 3.0; // Critical level - multiple strong indicators
          matchedTerm = "Multiple critical automation indicators detected";
        } else if (stealthScore >= 4) {
          suspiciousCount += 2.0; // High suspicion - several indicators
          matchedTerm = "Strong automation patterns detected";
        } else if (stealthScore >= 2) {
          suspiciousCount += 1.0; // Moderate suspicion
          matchedTerm = "Suspicious automation patterns detected";
        }

        

        // More nuanced entropy analysis
        if (extEntropy < 2.5 || extEntropy > 7.5) {
          suspiciousCount += 1.0; // Penalty for suspicious entropy range
          matchedTerm = "Suspicious WebGL entropy range";
        } else if (
          Math.abs(extEntropy - 5.129283016944964) < 0.0001 &&
          webGLRisk >= 2
        ) {
          suspiciousCount += 1.0; // Only penalize known value if other risks present
          matchedTerm = "Multiple suspicious patterns including entropy";
        }
      } else {
        suspiciousCount += 0.5; // Base penalty for suspicious activity
      }
    }

    // Deleted duplicate webGLRisk declaration as it's defined earlier

    // Environmental checks
    if (envSuspicious) {
      // Only count if multiple env checks fail
      if (suspiciousEnvScore >= 3) {
        suspiciousCount++;
      }
    }

    // Strong indicators of automation
    if (webdriverFlag) suspiciousCount += 2;
    if (pluginMissing && langMissing) suspiciousCount += 1.5;

    // Very high number of suspicious environment checks
    if (suspiciousEnvScore >= 5) suspiciousCount++;

    // More balanced bot detection using a scoring system
    const botConfidence = Math.min(suspiciousCount / 5, 1); // Normalize to 0-1 scale

    // Calculate risk factors separately

    const environmentRisk = [
      webdriverFlag,
      pluginMissing && langMissing,
      suspiciousEnvScore >= 4,
      envSuspicious && rendererSuspicious,
    ].filter(Boolean).length;

    const entropyRisk =
      extEntropy < 2.5 || // Too low entropy
      extEntropy > 7.5 || // Suspiciously high entropy
      (Math.abs(extEntropy - 5.129283016944964) < 0.0001 && webGLRisk >= 2) // Known bot value + other risks
        ? 1
        : 0;

    // Refined behavioral risk detection with more lenient thresholds for humans
    const behavioralRisk = [
      // Timing checks with more realistic tolerances
      Math.abs(webglFingerprint.timing - 0.15) < 0.01, // More precise timing match required
      
      // Extensions checks with realistic ranges
      extensions.length === 0 || extensions.length > 50, // Increased upper limit
      
      // Environment checks focused on automation indicators
      suspiciousEnvScore >= 4, // Increased threshold
      
      // Entropy exact match (very specific to bots)
      Math.abs(extEntropy - 5.129283016944964) < 0.0000001, // Require exact match
      
      // Hardware checks that indicate automation
      !webglFingerprint.antialias && perfectCapabilities && tooConsistent, // Require multiple indicators
      
      // Browser feature checks with tolerance for privacy settings
      !navigator.plugins?.length && !navigator.mimeTypes?.length && !hasChromeRuntime, // Must lack multiple features
      
      // Hardware concurrency check with tolerance
      typeof navigator.hardwareConcurrency === 'undefined' && typeof navigator.deviceMemory === 'undefined', // Must lack both
      
      // Language checks with context
      navigator.languages?.length === 0, // Only flag if no languages at all
      
      // WebGL capability checks with tolerance
      webglFingerprint.maxTextureSize === 16384 && perfectCapabilities && precisionTooUniform, // Must have multiple indicators
    ].filter(Boolean).length;

    // More balanced risk scoring system
    const legitFeatures = [
      extensions.length > 0 && extensions.length < 50, // Normal extension count
      navigator.languages?.length > 1, // Multiple languages
      webglFingerprint.antialias === true, // Normal antialiasing
      !perfectCapabilities || !tooConsistent, // Not suspiciously perfect
      navigator.plugins?.length > 0, // Has plugins
      extEntropy > 2.5 && extEntropy < 7.5, // Normal entropy range
      Math.abs(webglFingerprint.timing - 0.15) > 0.01, // Natural timing variation
    ].filter(Boolean).length;

    // Final decision with balanced thresholds and consideration of legitimate features
    isStealthBot = (
      // Must meet multiple strong indicators of automation
      (webGLRisk >= 3 && environmentRisk >= 2 && behavioralRisk >= 3) || // High risk across all categories
      (rendererSuspicious && suspiciousEnvScore >= 4 && behavioralRisk >= 3) || // Suspicious renderer with multiple other risks
      (perfectCapabilities && tooConsistent && precisionTooUniform && suspiciousEnvScore >= 3) || // Perfect setup with multiple risks
      
      // Strong individual indicators
      (webGLRisk >= 4 && legitFeatures <= 2) || // High WebGL risk with few legitimate features
      (behavioralRisk >= 5 && legitFeatures <= 3) || // High behavioral risk with few legitimate features
      
      // Combined risk factors with legitimate feature consideration
      (suspiciousCount >= 4.5 && legitFeatures <= 3) // High overall suspicion with few legitimate features
    ) && (
      // Additional checks to prevent false positives
      legitFeatures < 5 && // Must have few legitimate features
      (behavioralRisk + webGLRisk + environmentRisk) >= 7 // Must have high total risk
    );

    gpu_name_blacklisted = isStealthBot;

    // Add confidence level to the matchedTerm
    if (isStealthBot && matchedTerm) {
      matchedTerm = `${matchedTerm} (Confidence: ${(
        botConfidence * 100
      ).toFixed(1)}%)`;
    }

    if (isStealthBot && !matchedTerm) {
      matchedTerm = "Multiple strong suspicious signals";
    }

    // Add detailed reason about unknown renderer + WebGL state
    if (renderer === "unknown" || renderer === "") {
      const hasNormalWebGL =
        !suspiciousWebGL &&
        !suspiciousTiming &&
        !suspiciousAntialias &&
        extEntropy > 4.5;

      if (suspiciousCount >= 3.5) {
        matchedTerm = `Multiple suspicious patterns detected (score: ${suspiciousCount.toFixed(
          1
        )})`;
      } else if (hasNormalWebGL) {
        matchedTerm =
          "Privacy-focused browser (WebGL features look legitimate)";
      } else {
        matchedTerm = "Unknown renderer with some suspicious patterns";
      }
    }

    return {
      gpublacklist: {
        gpu_name: renderer,
        gpu_name_blacklisted,
        reason: gpu_name_blacklisted
          ? `🚨 Blacklisted GPU: "${matchedTerm}" in ${renderer}`
          : "✅ Looks normal",
        stealth_flags: {
          gpu_name_blacklisted,
          webdriverFlag,
          pluginMissing,
          langMissing,
          hasChromeRuntime,
          matchedTerm,
          suspiciousEnvScore,
          webglFingerprint,
          extEntropy,
          suspiciousWebGL,
          suspiciousTiming,
          suspiciousEntropy,
          suspiciousAntialias,
          suspiciousPrecision,
        },
        is_stealth_bot: isStealthBot,
      },
    };
  }

  useEffect(() => {
    const detectBotViaFingerprint = async () => {
      const fp = await FingerprintJS.load();
      const result = await fp.get();
      const visitorId = result.visitorId;
      setDeviceFingerprint(visitorId);
      // Always use the full advanced GPU detection results
      const gpuAnalysis = detectStealthBot(result);
      setgpublacklist(gpuAnalysis.gpublacklist);

      const canvasComponent = result.components?.canvas;
      if (canvasComponent && canvasComponent.value) {
        const winding = canvasComponent.value.winding;
        const geometry = canvasComponent.value.geometry || "";
        const text = canvasComponent.value.text || "";

        setCanvasMetrics({
          winding,
          geometryLength: geometry.length,
          textLength: text.length,
        });
        setMissingCanvasFingerprint(false);
      } else {
        setMissingCanvasFingerprint(true);
      }

      const audioComponent = result.components?.audio;
      // Defensive: check for both .value and .noise/.seed presence
      let entropyLow = null;
      if (
        audioComponent &&
        audioComponent.value &&
        (typeof audioComponent.value.noise === "string" ||
          typeof audioComponent.value.seed === "string")
      ) {
        const noise = audioComponent.value.noise || "";
        const seed = audioComponent.value.seed || "";

        const noiseLength = noise.length;
        const seedLength = seed.length;

        // Calculate Shannon entropy of the noise string
        function calculateEntropy(str) {
          if (!str || str.length === 0) return 0;
          const map = {};
          for (let i = 0; i < str.length; i++) {
            map[str[i]] = (map[str[i]] || 0) + 1;
          }
          let entropy = 0;
          const len = str.length;
          for (const k in map) {
            const p = map[k] / len;
            entropy -= p * Math.log2(p);
          }
          return entropy;
        }

        const noiseEntropy = calculateEntropy(noise);

        // Only flag as low entropy if noise/seed are present and entropy is low
        if (noiseLength === 0 && seedLength === 0) {
          entropyLow = null; // No audio fingerprint at all, treat as missing, not low entropy
        } else {
          entropyLow =
            noiseLength < 20 ||
            seedLength < 10 ||
            noiseEntropy < 3.5 ||
            /^([0-9])\1+$/.test(noise) || // all same digit
            /^([a-zA-Z])\1+$/.test(noise); // all same letter
        }
        setaudio_fp_entropy_low(entropyLow);
      } else {
        setaudio_fp_entropy_low(null);
      }

      // More strict bot detection checks
      const isHeadless = navigator.webdriver;
      const hasPlugins = navigator.plugins && navigator.plugins.length > 0;
      const hasLanguages =
        navigator.languages && navigator.languages.length > 0;
      const hasChrome = navigator.userAgent.includes("Chrome");
      const hasWebGL = !!document.createElement("canvas").getContext("webgl");
      const hasTouch = "ontouchstart" in window;
      const hasPermissions =
        navigator.permissions &&
        typeof navigator.permissions.query === "function";
      const hasNotifications = "Notification" in window;
      const hasStorage = "localStorage" in window && "sessionStorage" in window;
      const hasCookies = navigator.cookieEnabled;
      const hasDoNotTrack = navigator.doNotTrack !== undefined;
      const hasHardwareConcurrency = navigator.hardwareConcurrency > 0;
      const hasDeviceMemory = navigator.deviceMemory > 0;
      const hasConnection = "connection" in navigator;
      const hasBattery = "getBattery" in navigator;
      const hasVibrate = "vibrate" in navigator;
      const hasGeolocation = "geolocation" in navigator;
      const hasMediaDevices = navigator.mediaDevices !== undefined;
      const hasWebRTC = "RTCPeerConnection" in window;
      const hasWebAudio =
        "AudioContext" in window || "webkitAudioContext" in window;
      const hasWebGL2 = !!document.createElement("canvas").getContext("webgl2");
      const hasWebVR = "getVRDisplays" in navigator;
      const hasWebXR = "xr" in navigator;
      const hasGamepad = "getGamepads" in navigator;
      const hasCredentials = "credentials" in navigator;
      const hasClipboard = "clipboard" in navigator;
      const hasShare = "share" in navigator;
      const hasWakeLock = "wakeLock" in navigator;
      const hasBluetooth = "bluetooth" in navigator;
      const hasUSB = "usb" in navigator;
      const hasSerial = "serial" in navigator;
      const hasHID = "hid" in navigator;
      const hasNFC = "nfc" in navigator;
      const hasPayment = "PaymentRequest" in window;
      const hasCredentialManager = "credentials" in navigator;
      const hasPresentation = "presentation" in navigator;
      const hasRemotePlayback = "remotePlayback" in navigator;
      const hasScreenWakeLock = "wakeLock" in navigator;
      const hasScreenOrientation = "screenOrientation" in window;
      const hasScreenCapture =
        hasMediaDevices && "getDisplayMedia" in navigator.mediaDevices;
      const hasPictureInPicture = "pictureInPictureEnabled" in document;
      const hasPointerLock = "pointerLockElement" in document;
      const hasFullscreen = "fullscreenEnabled" in document;
      const hasWebShare = "share" in navigator;
      const hasWebOTP = "OTPCredential" in window;
      const hasWebAuthn = "PublicKeyCredential" in window;
      const hasWebCrypto = "crypto" in window;
      const hasWebPush = "PushManager" in window;
      const hasWebNotifications = "Notification" in window;
      const hasWebMIDI = "requestMIDIAccess" in navigator;
      const hasWebSpeech = "speechSynthesis" in window;
      const hasWebSpeechRecognition =
        "SpeechRecognition" in window || "webkitSpeechRecognition" in window;
      const hasWebGPU = "gpu" in navigator;
      const hasWebAssembly = "WebAssembly" in window;

      // Additional automation detection
      const hasAutomationFlags =
        window._phantom ||
        window.__nightmare ||
        window.callPhantom ||
        window.phantom ||
        window.selenium ||
        window.webdriver ||
        window.domAutomation ||
        window.domAutomationController ||
        window.navigator.webdriver ||
        window.navigator.userAgent.includes("Headless") ||
        window.navigator.userAgent.includes("Puppeteer") ||
        window.navigator.userAgent.includes("Selenium") ||
        window.navigator.userAgent.includes("HeadlessChrome");

      // Check for suspicious browser features
      const suspiciousFeatures = {
        noPlugins: !hasPlugins,
        noLanguages: !hasLanguages,
        noWebGL: !hasWebGL,
        noTouch: !hasTouch,
        noPermissions: !hasPermissions,
        noNotifications: !hasNotifications,
        noStorage: !hasStorage,
        noCookies: !hasCookies,
        noHardwareConcurrency: !hasHardwareConcurrency,
        noDeviceMemory: !hasDeviceMemory,
        noConnection: !hasConnection,
        noBattery: !hasBattery,
        noVibrate: !hasVibrate,
        noGeolocation: !hasGeolocation,
        noMediaDevices: !hasMediaDevices,
        noWebRTC: !hasWebRTC,
        noWebAudio: !hasWebAudio,
        noWebGL2: !hasWebGL2,
        noWebVR: !hasWebVR,
        noWebXR: !hasWebXR,
        noGamepad: !hasGamepad,
        noCredentials: !hasCredentials,
        noClipboard: !hasClipboard,
        noShare: !hasShare,
        noWakeLock: !hasWakeLock,
        noBluetooth: !hasBluetooth,
        noUSB: !hasUSB,
        noSerial: !hasSerial,
        noHID: !hasHID,
        noNFC: !hasNFC,
        noPayment: !hasPayment,
        noCredentialManager: !hasCredentialManager,
        noPresentation: !hasPresentation,
        noRemotePlayback: !hasRemotePlayback,
        noScreenWakeLock: !hasScreenWakeLock,
        noScreenOrientation: !hasScreenOrientation,
        noScreenCapture: !hasScreenCapture,
        noPictureInPicture: !hasPictureInPicture,
        noPointerLock: !hasPointerLock,
        noFullscreen: !hasFullscreen,
        noWebShare: !hasWebShare,
        noWebOTP: !hasWebOTP,
        noWebAuthn: !hasWebAuthn,
        noWebCrypto: !hasWebCrypto,
        noWebPush: !hasWebPush,
        noWebNotifications: !hasWebNotifications,
        noWebMIDI: !hasWebMIDI,
        noWebSpeech: !hasWebSpeech,
        noWebSpeechRecognition: !hasWebSpeechRecognition,
        noWebGPU: !hasWebGPU,
        noWebAssembly: !hasWebAssembly,
      };

      // Count suspicious features
      const suspiciousFeatureCount =
        Object.values(suspiciousFeatures).filter(Boolean).length;
      const suspiciousFeatureRatio =
        suspiciousFeatureCount / Object.keys(suspiciousFeatures).length;

      // Calculate base score
      let score = 0.5; // Start neutral

      // Heavy penalties for automation flags
      if (hasAutomationFlags) {
        score -= 0.4;
      }

      // Penalties for suspicious feature ratios
      if (suspiciousFeatureRatio > 0.3) {
        // More than 30% suspicious features
        score -= 0.3;
      } else if (suspiciousFeatureRatio > 0.2) {
        // More than 20% suspicious features
        score -= 0.2;
      } else if (suspiciousFeatureRatio > 0.1) {
        // More than 10% suspicious features
        score -= 0.1;
      }

      // Additional checks for common bot patterns
      if (
        !hasChrome &&
        !navigator.userAgent.includes("Firefox") &&
        !navigator.userAgent.includes("Safari")
      ) {
        score -= 0.2; // Not a common browser
      }

      if (navigator.plugins && navigator.plugins.length < 2) {
        score -= 0.1; // Too few plugins
      }

      if (navigator.languages && navigator.languages.length < 1) {
        score -= 0.1; // No languages
      }

      // Ensure score is between 0 and 1
      score = Math.max(0, Math.min(1, score));

      const totalScore = +score.toFixed(2);
      setBotFingerprintScore(totalScore);

      // Store results instead of logging
      const results = {
        botFingerprintScore: totalScore,
        automationFlagsDetected: hasAutomationFlags,
        suspiciousFeatureCount,
        suspiciousFeatureRatio: (suspiciousFeatureRatio * 100).toFixed(1) + "%",
        totalFeatures: Object.keys(suspiciousFeatures).length,
      };

      setBotDetectionResults(results);
      return totalScore;
    };

    detectBotViaFingerprint();
  }, []);

  useEffect(() => {
    setAllSpeeds(cursorSpeeds);
    console.log("All Cursor Speeds Updated:", [...cursorSpeeds]);
  }, [cursorSpeeds]);

  useEffect(() => {
    if (cursorSpeeds.length > 0) {
      console.log("Updated Cursor Speeds:", [...cursorSpeeds]); // Ensures fresh speeds are logged
    }
  }, [cursorSpeeds]);

  useEffect(() => {
    setPageLoadTime(Date.now());
  }, []);

  useEffect(() => {
    if (cursorMovements.length > 0) {
      console.log("Updated Cursor Movements:", [...cursorMovements]); // Ensures fresh movements are logged
    }
  }, [cursorMovements]);

  // console.log("Mouse moved:", event.clientX, event.clientY); // Debugging

  useEffect(() => {
    let idleTimer;

    // Complete fixed mouse handler for captcha-form.js
    const handleMouseMove = (event) => {
      detectSuspiciousPatterns(event);
      const now = Date.now();
      // Moderate throttling - not too much, not too little
      if (now - lastUpdateTime < 50) return; // Reduced from 150ms to 50ms

      const newPoint = {
        x: event.clientX,
        y: event.clientY,
        timestamp: now, // Use milliseconds instead of seconds
      };

      if (pasteDetected && now && now - now < 10000) {
        // Only count significant movements
        if (lastMouseMove) {
          const dx = event.clientX - lastMouseMove.x;
          const dy = event.clientY - lastMouseMove.y;
          const distance = Math.sqrt(dx * dx + dy * dy);

          if (distance > 10) {
            trackPostPasteAction("mouseMoves");
          }
        }
      }
      if (lastMouseMove) {
        const dx = event.clientX - lastMouseMove.x;
        const dy = event.clientY - lastMouseMove.y;
        const distance = Math.sqrt(dx ** 2 + dy ** 2);
        const timeDiff = now - lastMouseMove.timestamp;

        // Debug log for mouse movement
        console.log("Mouse Movement Debug:", {
          distance,
          timeDiff,
          dx,
          dy,
          currentSpeed: latestSpeed,
        });

        // More reasonable distance threshold
        if (distance > 0 && timeDiff > 0) {
          // Raw speed calculation
          const rawSpeed = (distance / timeDiff) * 1000;

          // Debug log for speed calculation
          console.log("Speed Calculation Debug:", {
            rawSpeed,
            filteredSpeed: latestSpeed,
            latestSpeed,
          });

          // Wider range filter to catch natural human speeds
          if (rawSpeed > 10 && rawSpeed < 1500) {
            // Add small random variation to speeds to make them more human-like
            const naturalSpeed = rawSpeed * (0.98 + Math.random() * 0.04);
            setLatestSpeed(naturalSpeed);

            setCursorSpeeds((prev) => {
              const newSpeeds = [...prev.slice(-40), naturalSpeed];
              console.log("Updated Cursor Speeds:", newSpeeds);
              return newSpeeds;
            });

            // Calculate acceleration (change in speed over time)
            setCursorAcceleration((prev) => {
              if (prev.length > 0) {
                const lastSpeed = prev[prev.length - 1];
                const accel = (naturalSpeed - lastSpeed) / timeDiff;

                // Debug log for acceleration
                console.log("Acceleration Debug:", {
                  lastSpeed,
                  currentSpeed: naturalSpeed,
                  timeDiff,
                  calculatedAccel: accel,
                });

                // More lenient filter for acceleration
                if (Math.abs(accel) < 20000) {
                  const newAccel = [...prev.slice(-40), accel];
                  console.log("Updated Cursor Acceleration:", newAccel);
                  return newAccel;
                }
              }
              // Initialize with a small value if empty
              return prev.length ? prev : [0.1];
            });
          }
        }
      }

      // Store more movement points for better analysis
      setCursorMovements((prev) => {
        // Only filter extremely close points
        const prevPoint = prev.length > 0 ? prev[prev.length - 1] : null;
        if (prevPoint) {
          const dx = newPoint.x - prevPoint.x;
          const dy = newPoint.y - prevPoint.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          // Reduced threshold to capture more natural movement
          if (dist < 5) return prev;
        }
        return [...prev.slice(-50), newPoint]; // Store more points
      });

      setLastMouseMove(newPoint);
      setLastUpdateTime(now);
    };

    const handleKeyDown = (event) => {
      setLastKeyDown((prev) => ({ ...prev, [event.key]: Date.now() }));
    };

    const handleKeyUp = (event) => {
      const now = Date.now();
      if (lastKeyDown[event.key]) {
        setKeyHoldTimes((prev) => [...prev, now - lastKeyDown[event.key]]);
      }
    };

    const handleKeyPress = (event) => {
      detectSuspiciousPatterns(event);
      const now = Date.now();

      if (pasteDetected) {
        trackPostPasteAction("keyPresses");
      }

      if (lastKeyPress) {
        setKeyPressTimes((prev) => [...prev, now - lastKeyPress]);
      }
      setLastKeyPress(now);
    };

    const handleClick = () => {
      const now = Date.now(); // Keep in milliseconds

      console.log("Click Debug:", {
        lastClickTime,
        timeSinceLastClick: lastClickTime ? now - lastClickTime : null,
        clickTimestamps: clickTimestamps,
      });

      if (pasteDetected) {
        trackPostPasteAction("clicks");
      }

      setClickTimestamps((prev) => {
        const newTimestamps = [...prev.slice(-30), now];
        console.log("Updated Click Timestamps:", newTimestamps);
        return newTimestamps;
      });

      if (lastClickTime !== null) {
        const clickSpeed = now - lastClickTime; // This will be in milliseconds
        // Only record clicks with reasonable intervals (more than 100ms)
        if (clickSpeed > 100) {
          setClickTimes((prev) => {
            const newClickTimes = [...prev.slice(-30), clickSpeed];
            console.log("Updated Click Times:", newClickTimes);
            return newClickTimes;
          });
        }
      }

      if (pasteDetected && pasteTimestamp && now - pasteTimestamp < 10000) {
        setPostPasteActivity((prev) => ({
          ...prev,
          clicks: prev.clicks + 1,
        }));
      }

      setLastClickTime(now);
    };

    // Improved scroll handler
    const handleScroll = () => {
      const now = Date.now();
      const scrollDiff = Math.abs(window.scrollY - lastScroll);
      const timeDiff = now - lastScrollTime;

      // Only record meaningful scrolls with reasonable timing
      if (scrollDiff > 5 && timeDiff > 50) {
        const scrollSpeed = (scrollDiff / timeDiff) * 1000;

        // Filter out unrealistic scroll speeds
        if (scrollSpeed > 10 && scrollSpeed < 3000) {
          setScrollSpeeds((prev) => {
            // Add some small variation to make it more natural
            const jitteredSpeed = scrollSpeed * (0.95 + Math.random() * 0.1);
            return [...prev.slice(-15), jitteredSpeed];
          });
          setScrollChanges((prev) => prev + 1);
        }
      }

      setLastScroll(window.scrollY);
      setLastScrollTime(now);
    };

    // Make sure to add this state variable at the top
    // const [lastScrollTime, setLastScrollTime] = useState(Date.now());

    const resetIdleTime = () => {
      clearTimeout(idleTimer);
      setIdleTime(0);
      idleTimer = setTimeout(() => {
        setIdleTime((prev) => prev + 1);
      }, 1000);
    };

    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("keydown", handleKeyDown);
    document.addEventListener("keyup", handleKeyUp);
    document.addEventListener("keypress", handleKeyPress);
    document.addEventListener("click", handleClick);
    window.addEventListener("scroll", handleScroll);
    document.addEventListener("paste", handlePaste);
    document.addEventListener("mousemove", resetIdleTime);
    document.addEventListener("keypress", resetIdleTime);
    document.addEventListener("scroll", handleScroll);
    document.addEventListener("keydown", handleTabKey);

    return () => {
      clearTimeout(idleTimer);
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("keydown", handleKeyDown);
      document.removeEventListener("keyup", handleKeyUp);
      document.removeEventListener("keypress", handleKeyPress);
      document.removeEventListener("click", handleClick);
      document.removeEventListener("scroll", handleScroll);
      document.removeEventListener("paste", handlePaste);
      document.removeEventListener("mousemove", resetIdleTime);
      document.removeEventListener("keypress", resetIdleTime);
      document.removeEventListener("keydown", handleTabKey);
    };
  }, [lastKeyPress, lastMouseMove, lastScroll]);

  // Modified calculateCursorCurvature function
  const calculateCursorCurvature = (movements) => {
    if (movements.length < 5) return 0; // Need at least 5 points for meaningful curvature

    const recentMovements = movements.slice(-10);

    let totalCurvature = 0;
    let validMeasurements = 0;

    // Calculate curvature across multiple point triplets
    for (let i = 2; i < recentMovements.length; i++) {
      const p1 = recentMovements[i - 2];
      const p2 = recentMovements[i - 1];
      const p3 = recentMovements[i];

      // Calculate vectors
      const v1 = { x: p2.x - p1.x, y: p2.y - p1.y };
      const v2 = { x: p3.x - p2.x, y: p3.y - p2.y };

      // Compute angle using dot product
      const v1Norm = Math.sqrt(v1.x ** 2 + v1.y ** 2);
      const v2Norm = Math.sqrt(v2.x ** 2 + v2.y ** 2);

      if (v1Norm > 5 && v2Norm > 5) {
        // Reduced threshold, was 30
        const dotProduct = v1.x * v2.x + v1.y * v2.y;
        const cosTheta = Math.max(
          -1,
          Math.min(1, dotProduct / (v1Norm * v2Norm))
        );
        const angle = Math.acos(cosTheta) * (180 / Math.PI);

        // Compute curvature but with adjusted calculation
        const curvature = angle / Math.max(20, (v1Norm + v2Norm) / 2);

        // Only count significant changes in direction
        if (angle > 3) {
          totalCurvature += curvature;
          validMeasurements++;
        }
      }
    }

    // Return average curvature or default value in expected human range
    return validMeasurements > 0 ? totalCurvature / validMeasurements : 1.0;
  };

  useEffect(() => {
    if (cursorMovements.length >= 3 && cursorMovements.length % 5 === 0) {
      const curvature = calculateCursorCurvature(cursorMovements);
      setCursorCurvature((prev) => [...prev, curvature]);
    }
  }, [cursorMovements]);

  useEffect(() => {
    if (cursorMovements.length >= 3 && cursorMovements.length % 5 === 0) {
      const entropy = calculateCursorEntropy(cursorMovements);
      setCursorEntropy(parseFloat(entropy));
    }
  }, [cursorMovements]);

  useEffect(() => {
    if (clickTimes.length > 0) {
      console.log("Click Intervals (ms):", clickTimes);
    }
  }, [clickTimes]);

  // Add new useEffect for initial bot detection
  useEffect(() => {
    const detectAutomatedBrowser = () => {
      const automated =
        navigator.webdriver ||
        window.navigator.userAgent.includes("Headless") ||
        window.navigator.userAgent.includes("Puppeteer") ||
        window.navigator.userAgent.includes("Selenium") ||
        !window.navigator.plugins.length ||
        !window.navigator.languages.length ||
        window.navigator.languages.length === 0 ||
        !window.navigator.userAgent.includes("Chrome") ||
        window.navigator.userAgent.includes("HeadlessChrome");

      setIsAutomatedBrowser(automated);

      // Collect device info
      setDeviceInfo({
        userAgent: navigator.userAgent,
        platform: navigator.platform,
        plugins: navigator.plugins.length,
        languages: navigator.languages.length,
        screenResolution: `${window.screen.width}x${window.screen.height}`,
        colorDepth: window.screen.colorDepth,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        isMobile:
          /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
            navigator.userAgent
          ),
      });
    };

    detectAutomatedBrowser();
  }, []);

  // Add new function to detect suspicious patterns
  const detectSuspiciousPatterns = (event) => {
    const now = Date.now();
    const timeSinceLastAction = now - lastActionTime;
    setLastActionTime(now);
    setActionCount((prev) => prev + 1);

    // Much more lenient timing patterns with debouncing
    if (timeSinceLastAction < 5) {
      // Reduced from 10ms to 5ms
      // Only detect rapid actions if there are multiple very quick actions in succession
      setSuspiciousPatterns((prev) => {
        const lastThreeActions = prev.slice(-3);
        const rapidActionCount = lastThreeActions.filter(
          (p) => p === "rapid_actions"
        ).length;

        // Only add rapid_actions if we've seen 3 or more rapid actions in the last 3 actions
        if (rapidActionCount >= 2) {
          return [...prev, "rapid_actions"];
        }
        return prev;
      });
    }

    // Detect suspicious mouse movements with more lenient thresholds
    if (event.type === "mousemove") {
      const { clientX, clientY } = event;
      const lastPoint = mouseTrajectory[mouseTrajectory.length - 1];

      if (lastPoint) {
        const distance = Math.sqrt(
          Math.pow(clientX - lastPoint.x, 2) +
            Math.pow(clientY - lastPoint.y, 2)
        );
        const timeDiff = now - lastPoint.timestamp;

        // More lenient linear movement detection
        if (distance > 300 && timeDiff < 30) {
          setSuspiciousPatterns((prev) => {
            if (
              prev.length === 0 ||
              prev[prev.length - 1] !== "linear_movement"
            ) {
              return [...prev, "linear_movement"];
            }
            return prev;
          });
        }
      }

      setMouseTrajectory((prev) => [
        ...prev,
        { x: clientX, y: clientY, timestamp: now },
      ]);
    }

    // More lenient keyboard pattern detection
    if (event.type === "keypress") {
      const keyPressTime = now;
      setKeyboardPatterns((prev) => [...prev, keyPressTime]);

      if (keyboardPatterns.length >= 8) {
        const intervals = keyboardPatterns
          .slice(-8)
          .map((time, i, arr) => (i > 0 ? time - arr[i - 1] : 0))
          .filter(Boolean);

        const avgInterval =
          intervals.reduce((a, b) => a + b, 0) / intervals.length;
        const stdDev = Math.sqrt(
          intervals.reduce((a, b) => a + Math.pow(b - avgInterval, 2), 0) /
            intervals.length
        );

        if (stdDev < 5) {
          setSuspiciousPatterns((prev) => {
            if (
              prev.length === 0 ||
              prev[prev.length - 1] !== "consistent_typing"
            ) {
              return [...prev, "consistent_typing"];
            }
            return prev;
          });
        }
      }
    }
  };

 

  const detectAutomationPatterns = () => {
    const patterns = [];

    // Only check for obvious automation tools
    if (window._phantom && !window.navigator.userAgent.includes("Chrome"))
      patterns.push("phantom_detected");
    if (window.__nightmare && !window.navigator.userAgent.includes("Chrome"))
      patterns.push("nightmare_detected");
    if (window.callPhantom && !window.navigator.userAgent.includes("Chrome"))
      patterns.push("phantom_api_detected");
    if (window.phantom && !window.navigator.userAgent.includes("Chrome"))
      patterns.push("phantom_object_detected");
    if (window.selenium && !window.navigator.userAgent.includes("Chrome"))
      patterns.push("selenium_detected");
    if (window.webdriver && !window.navigator.userAgent.includes("Chrome"))
      patterns.push("webdriver_detected");

    return patterns;
  };

  // Modify submitForm to include automation pattern detection
  const submitForm = async (e) => {
    e.preventDefault();

    // More strict automated browser check
    const automationPatterns = detectAutomationPatterns();
    const isAutomated =
      automationPatterns.length > 0 || botFingerprintScore > 0.7; // Lower threshold

    if (isAutomated) {
      // Log bot detection results only once here
      if (botDetectionResults) {
        console.log("=== BOT DETECTION RESULTS ===");
        console.log(
          "Bot Fingerprint Score:",
          botDetectionResults.botFingerprintScore
        );
        console.log(
          "Automation Flags Detected:",
          botDetectionResults.automationFlagsDetected
        );
        console.log(
          "Suspicious Features:",
          botDetectionResults.suspiciousFeatureCount,
          "out of",
          botDetectionResults.totalFeatures
        );
        console.log(
          "Suspicious Feature Ratio:",
          botDetectionResults.suspiciousFeatureRatio
        );
        console.log("===========================");
      }

      console.log("Automation patterns detected:", automationPatterns);
      setMessage("Automated browser detected! Access denied.");
      setIsBlocked(true);
      return;
    }

    if (!usaiId.trim()) {
      alert("Please enter the USAI ID");
      return;
    }

    if (honeypot.trim()) {
      setMessage("Suspicious activity detected!");
      setIsBlocked(true);
      return;
    }

    // Extract additional fingerprint features

    const behaviorData = {
      cursorMovements: [...cursorMovements],
      cursorSpeeds: [...cursorSpeeds],
      cursorCurvature: [...cursorCurvature],
      cursorAcceleration: [...cursorAcceleration],
      keyPressTimes: [...keyPressTimes],
      keyHoldTimes: [...keyHoldTimes],
      clickTimes: [...clickTimes],
      clickTimestamps: [...clickTimestamps],
      scrollSpeeds: [...scrollSpeeds],
      totalTimeToSubmit: Date.now() - pageLoadTime,
      scrollChanges,
      idleTime,
      pasteDetected,
      postPasteActivity,
      keyboardPatterns,
      suspiciousPatterns,
      actionCount,
      isAutomatedBrowser,
      cursorEntropy: cursorEntropy,
      botFingerprintScore,
      mouseMovementDebug: {
        distance:
          latestSpeed > 0
            ? Math.sqrt(
                Math.pow(
                  lastMouseMove?.x -
                    cursorMovements[cursorMovements.length - 2]?.x || 0,
                  2
                ) +
                  Math.pow(
                    lastMouseMove?.y -
                      cursorMovements[cursorMovements.length - 2]?.y || 0,
                    2
                  )
              )
            : 0,
        timeDiff: lastMouseMove?.timestamp || 0,
        dx:
          lastMouseMove?.x - cursorMovements[cursorMovements.length - 2]?.x ||
          0,
        dy:
          lastMouseMove?.y - cursorMovements[cursorMovements.length - 2]?.y ||
          0,
        currentSpeed: latestSpeed,
      },
      speedCalculationDebug: {
        rawSpeed: latestSpeed,
        filteredSpeed: latestSpeed,
        latestSpeed: latestSpeed,
      },
      tabkeyCount: TabKeyCount,
      cursorAngle: [...cursorAngles],
      mouseJitter: [...mouseJitter],
      microPauses: [...microPauses],
      hesitationTimes: [...hesitationTimes],
      deviceFingerprint: deviceFingerprint,
      missing_canvas_fingerprint: missingCanvasFingerprint,
      canvas_metrics: canvasMetrics,
 
      unusualScreenResolution: unusualScreenResolution,
      gpuInformation: gpuInfo,
      timingMetrics,
      evasionSignals: {
        idleResumeAngularJerk: idleResumeAngularJerk,
        thermalHoverNoise: thermalHoverNoise,
        hoverPositions: [...hoverPositions],
        deviation_angle: fittsDeviationScore,
        acceleration_variance: accelerationVariance,
        path_entropy: pathEntropy,
        cursor_micro_jitter: cursorMicroJitter,
      },
    };

    // Log the extracted fingerprint features as part of behaviorData
    console.log("Behavior Data:\n" + JSON.stringify(behaviorData, null, 2));

    const totalSubmitTime = Date.now() - pageLoadTime;
    setSubmitTime(totalSubmitTime);

    try {
      console.log("Sending request to backend...");
      const response = await fetch(
        "http://localhost:8000/captchaApp/analyze-user/",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            usai_id: usaiId.trim(),
            behavior: behaviorData,
            honeypot: honeypot,
          }),
        }
      );

      // Always show only the model prediction, never access denied
      const predictResponse = await fetch(
        "http://localhost:8000/captchaApp/predict-user-type/",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            behavior: {
              cursorMovements,
              cursorSpeeds,
              cursorCurvature,
              cursorAcceleration,
              keyPressTimes,
              keyHoldTimes,
              clickTimestamps,
              clickTimes,
              scrollSpeeds,
              totalTimeToSubmit: Date.now() - pageLoadTime,
              scrollChanges,
              idleTime,
              pasteDetected,
              postPasteActivity,
              keyboardPatterns,
              suspiciousPatterns,
              actionCount,
              isAutomatedBrowser,
              botFingerprintScore,
              mouseMovementDebug: {
                distance:
                  latestSpeed > 0
                    ? Math.sqrt(
                        Math.pow(
                          lastMouseMove?.x -
                            cursorMovements[cursorMovements.length - 2]?.x || 0,
                          2
                        ) +
                          Math.pow(
                            lastMouseMove?.y -
                              cursorMovements[cursorMovements.length - 2]?.y ||
                              0,
                            2
                          )
                      )
                    : 0,
                timeDiff: lastMouseMove?.timestamp || 0,
                dx:
                  lastMouseMove?.x -
                    cursorMovements[cursorMovements.length - 2]?.x || 0,
                dy:
                  lastMouseMove?.y -
                    cursorMovements[cursorMovements.length - 2]?.y || 0,
                currentSpeed: latestSpeed,
              },
            },
          }),
          speedCalculationDebug: {
            rawSpeed: latestSpeed,
            filteredSpeed: latestSpeed,
            latestSpeed: latestSpeed,
          },
          tabkeyCount: TabKeyCount,
          cursorAngle: [...cursorAngles],
          mouseJitter: [...mouseJitter],
          microPauses: [...microPauses],
          hesitationTimes: [...hesitationTimes],
        }
      );

      const predictResult = await predictResponse.json();
      setMessage(
        `🤖 Classification: ${predictResult.classification} (Confidence: ${predictResult.confidence}%)`
      );
      setIsBlocked(false); // Never block the UI, always show prediction
    } catch (error) {
      console.error("Error during submission:", error);
      setMessage("Error verifying user.");
    }
  };

  // Add mouse jitter, micro-pauses, and hesitation pattern feature collection to the frontend. These are tracked in state and included in the behavior data sent to the backend.
  // Mouse Jitter & Micro-pauses calculation
  useEffect(() => {
    let lastMoveTime = Date.now();
    let lastPoint = null;
    let moveDistances = [];
    let pauseDurations = [];

    const handleMouseMoveJitter = (e) => {
      const now = Date.now();
      const point = { x: e.clientX, y: e.clientY };
      if (lastPoint) {
        const dx = point.x - lastPoint.x;
        const dy = point.y - lastPoint.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        moveDistances.push(dist);
        if (moveDistances.length > 10) moveDistances.shift();
        // Jitter: stddev of last 10 distances
        if (moveDistances.length >= 5) {
          const mean =
            moveDistances.reduce((a, b) => a + b, 0) / moveDistances.length;
          const std = Math.sqrt(
            moveDistances.reduce((a, b) => a + Math.pow(b - mean, 2), 0) /
              moveDistances.length
          );
          setMouseJitter((prev) => [...prev.slice(-40), std]);
        }
        // Micro-pauses: time between moves in 50–300ms
        const pause = now - lastMoveTime;
        if (pause >= 50 && pause <= 300) {
          pauseDurations.push(pause);
          if (pauseDurations.length > 20) pauseDurations.shift();
          setMicroPauses([...pauseDurations]);
        }
      }
      lastMoveTime = now;
      lastPoint = point;
    };
    document.addEventListener("mousemove", handleMouseMoveJitter);
    return () =>
      document.removeEventListener("mousemove", handleMouseMoveJitter);
  }, []);

  // Hesitation pattern: time hovering over input/button before action
  useEffect(() => {
    const handleMouseEnter = (e) => {
      if (e.target.tagName === "INPUT" || e.target.tagName === "BUTTON") {
        setLastHoverStart(Date.now());
      }
    };

    const handleMouseLeave = (e) => {
      if (e.target.tagName === "INPUT" || e.target.tagName === "BUTTON") {
        setLastHoverStart(null);
      }
    };

    const handleAction = (e) => {
      // Only capture hesitation for input fields and buttons
      if (
        (e.type === "click" || e.type === "focus") &&
        (e.target.tagName === "INPUT" || e.target.tagName === "BUTTON") &&
        lastHoverStart
      ) {
        const hesitation = Date.now() - lastHoverStart;
        // Capture meaningful hesitation (100ms to 10 seconds)
        if (hesitation >= 100 && hesitation <= 10000) {
          setHesitationTimes((prev) => [...prev.slice(-20), hesitation]);
        }
        setLastHoverStart(null);
      }
    };

    document.addEventListener("mouseenter", handleMouseEnter, true);
    document.addEventListener("mouseleave", handleMouseLeave, true);
    document.addEventListener("click", handleAction, true);
    document.addEventListener("focus", handleAction, true);

    return () => {
      document.removeEventListener("mouseenter", handleMouseEnter, true);
      document.removeEventListener("mouseleave", handleMouseLeave, true);
      document.removeEventListener("click", handleAction, true);
      document.removeEventListener("focus", handleAction, true);
    };
  }, [lastHoverStart]);

  const inputId = useMemo(
    () => `input_${Math.random().toString(36).slice(2, 10)}`,
    []
  );
  const buttonId = useMemo(
    () => `btn_${Math.random().toString(36).slice(2, 10)}`,
    []
  );

  return (
    <div className="dashboard">
      {/* Top Navigation Bar */}
      <nav className="top-navbar">
        <div className="navbar-brand">
          <h2>Bot Detection Dashboard</h2>
        </div>
        <div className="navbar-pages">
          <button className="nav-page active">Overview</button>
          <button className="nav-page">Analytics</button>
          <button className="nav-page">Detection Log</button>
          <button className="nav-page">Configuration</button>
          <button className="nav-page">Reports</button>
        </div>
        <div className="navbar-user">
          <span>Admin User</span>
          <button className="logout-btn">Logout</button>
        </div>
      </nav>

      <div className="dashboard-body">
        {/* Left Horizontal Sidebar */}
        <aside className="left-sidebar">
          <div className="sidebar-section">
            <h3>Detection</h3>
            <ul className="sidebar-options">
              <li className="sidebar-item active">
                <i className="icon">🎯</i>
                <span>Real-time Monitor</span>
              </li>
              <li className="sidebar-item">
                <i className="icon">🤖</i>
                <span>Bot Analysis</span>
              </li>
              <li className="sidebar-item">
                <i className="icon">👤</i>
                <span>Human Behavior</span>
              </li>
              <li className="sidebar-item">
                <i className="icon">🔍</i>
                <span>Pattern Detection</span>
              </li>
            </ul>
          </div>

          <div className="sidebar-section">
            <h3>Management</h3>
            <ul className="sidebar-options">
              <li className="sidebar-item">
                <i className="icon">⚙️</i>
                <span>Settings</span>
              </li>
              <li className="sidebar-item">
                <i className="icon">🛡️</i>
                <span>Security Rules</span>
              </li>
              <li className="sidebar-item">
                <i className="icon">📊</i>
                <span>Thresholds</span>
              </li>
              <li className="sidebar-item">
                <i className="icon">🔔</i>
                <span>Alerts</span>
              </li>
            </ul>
          </div>

          <div className="sidebar-section">
            <h3>Reports</h3>
            <ul className="sidebar-options">
              <li className="sidebar-item">
                <i className="icon">📈</i>
                <span>Statistics</span>
              </li>
              <li className="sidebar-item">
                <i className="icon">📋</i>
                <span>Logs</span>
              </li>
              <li className="sidebar-item">
                <i className="icon">💾</i>
                <span>Export Data</span>
              </li>
              <li className="sidebar-item">
                <i className="icon">🕒</i>
                <span>History</span>
              </li>
            </ul>
          </div>

          <div className="sidebar-section">
            <h3>System</h3>
            <ul className="sidebar-options">
              <li className="sidebar-item">
                <i className="icon">💻</i>
                <span>System Health</span>
              </li>
              <li className="sidebar-item">
                <i className="icon">🔧</i>
                <span>Maintenance</span>
              </li>
              <li className="sidebar-item">
                <i className="icon">❓</i>
                <span>Help & Support</span>
              </li>
            </ul>
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="main-content">
          <div className="content-header">
            <h1>Real-time Bot Detection Monitor</h1>
            <div className="content-actions">
              <button className="action-btn primary">Start Monitoring</button>
              <button className="action-btn secondary">Refresh</button>
            </div>
          </div>

          <div className="dashboard-grid">
            {/* Quick Stats Cards */}
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-icon">🤖</div>
                <div className="stat-info">
                  <h3>Bot Detections</h3>
                  <p className="stat-number">1,247</p>
                  <span className="stat-change increase">+12% today</span>
                </div>
              </div>
              
              <div className="stat-card">
                <div className="stat-icon">👥</div>
                <div className="stat-info">
                  <h3>Human Users</h3>
                  <p className="stat-number">8,932</p>
                  <span className="stat-change decrease">-3% today</span>
                </div>
              </div>
              
              <div className="stat-card">
                <div className="stat-icon">🛡️</div>
                <div className="stat-info">
                  <h3>Blocked Threats</h3>
                  <p className="stat-number">456</p>
                  <span className="stat-change increase">+8% today</span>
                </div>
              </div>
              
              <div className="stat-card">
                <div className="stat-icon">⚡</div>
                <div className="stat-info">
                  <h3>Detection Rate</h3>
                  <p className="stat-number">97.8%</p>
                  <span className="stat-change stable">No change</span>
                </div>
              </div>
            </div>

            {/* Activity Feed */}
            <div className="activity-section">
              <h2>Recent Activity</h2>
              <div className="activity-feed">
                <div className="activity-item bot">
                  <div className="activity-icon">🤖</div>
                  <div className="activity-details">
                    <p><strong>Bot Detected</strong> - Automated script from IP 192.168.1.100</p>
                    <span className="activity-time">2 minutes ago</span>
                  </div>
                </div>
                
                <div className="activity-item human">
                  <div className="activity-icon">👤</div>
                  <div className="activity-details">
                    <p><strong>Human Verified</strong> - Legitimate user behavior pattern</p>
                    <span className="activity-time">5 minutes ago</span>
                  </div>
                </div>
                
                <div className="activity-item warning">
                  <div className="activity-icon">⚠️</div>
                  <div className="activity-details">
                    <p><strong>Suspicious Activity</strong> - Multiple rapid requests detected</p>
                    <span className="activity-time">8 minutes ago</span>
                  </div>
                </div>
                
                <div className="activity-item blocked">
                  <div className="activity-icon">🚫</div>
                  <div className="activity-details">
                    <p><strong>Threat Blocked</strong> - Malicious bot attempt prevented</p>
                    <span className="activity-time">12 minutes ago</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Detection Chart Placeholder */}
            <div className="chart-section">
              <h2>Detection Trends</h2>
              <div className="chart-placeholder">
                <p>📊 Chart visualization would go here</p>
                <p>Bot vs Human traffic over time</p>
              </div>
            </div>
          </div>
        </main>
      </div>

      {/* Dashboard Styles */}
      <style jsx>{`
        .dashboard {
          min-height: 100vh;
          height: 100vh;
          width: 100vw;
          background-color: #f5f7fa;
          font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
          overflow: hidden;
          position: fixed;
          top: 0;
          left: 0;
          margin: 0;
          padding: 0;
        }

        .top-navbar {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          padding: 1rem 2rem;
          display: flex;
          justify-content: space-between;
          align-items: center;
          box-shadow: 0 2px 10px rgba(0,0,0,0.1);
          width: 100%;
          height: 80px;
          position: relative;
          z-index: 10;
        }

        .navbar-brand h2 {
          margin: 0;
          font-weight: 600;
        }

        .navbar-pages {
          display: flex;
          gap: 1rem;
        }

        .nav-page {
          background: rgba(255,255,255,0.1);
          border: none;
          color: white;
          padding: 0.5rem 1rem;
          border-radius: 6px;
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .nav-page:hover, .nav-page.active {
          background: rgba(255,255,255,0.2);
          transform: translateY(-1px);
        }

        .navbar-user {
          display: flex;
          align-items: center;
          gap: 1rem;
        }

        .logout-btn {
          background: rgba(255,255,255,0.1);
          border: 1px solid rgba(255,255,255,0.3);
          color: white;
          padding: 0.5rem 1rem;
          border-radius: 6px;
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .logout-btn:hover {
          background: rgba(255,255,255,0.2);
        }

        .dashboard-body {
          display: flex;
          height: calc(100vh - 80px);
          width: 100%;
          overflow: hidden;
        }

        .left-sidebar {
          width: 280px;
          min-width: 280px;
          background: white;
          border-right: 1px solid #e1e8ed;
          padding: 2rem 0;
          overflow-y: auto;
          box-shadow: 2px 0 10px rgba(0,0,0,0.05);
          height: 100%;
        }

        .sidebar-section {
          margin-bottom: 2rem;
          padding: 0 1.5rem;
        }

        .sidebar-section h3 {
          color: #64748b;
          font-size: 0.875rem;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          margin-bottom: 1rem;
          padding-left: 0.5rem;
        }

        .sidebar-options {
          list-style: none;
          margin: 0;
          padding: 0;
        }

        .sidebar-item {
          display: flex;
          align-items: center;
          padding: 0.75rem 1rem;
          margin-bottom: 0.25rem;
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.2s ease;
          color: #475569;
        }

        .sidebar-item:hover {
          background-color: #f1f5f9;
          color: #334155;
          transform: translateX(4px);
        }

        .sidebar-item.active {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
        }

        .sidebar-item .icon {
          margin-right: 0.75rem;
          font-size: 1.1rem;
        }

        .main-content {
          flex: 1;
          padding: 2rem;
          overflow-y: auto;
          height: 100%;
          background-color: #f5f7fa;
        }

        .content-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 2rem;
        }

        .content-header h1 {
          color: #1e293b;
          margin: 0;
          font-size: 2rem;
          font-weight: 600;
        }

        .content-actions {
          display: flex;
          gap: 1rem;
        }

        .action-btn {
          padding: 0.75rem 1.5rem;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          font-weight: 500;
          transition: all 0.3s ease;
        }

        .action-btn.primary {
          background: linear-gradient(135deg, #10b981 0%, #059669 100%);
          color: white;
        }

        .action-btn.secondary {
          background: white;
          color: #64748b;
          border: 1px solid #e2e8f0;
        }

        .action-btn:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }

        .dashboard-grid {
          display: grid;
          gap: 2rem;
          grid-template-columns: 1fr;
        }

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 1.5rem;
          margin-bottom: 2rem;
        }

        .stat-card {
          background: white;
          padding: 1.5rem;
          border-radius: 12px;
          box-shadow: 0 1px 3px rgba(0,0,0,0.1);
          display: flex;
          align-items: center;
          transition: all 0.3s ease;
        }

        .stat-card:hover {
          transform: translateY(-4px);
          box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }

        .stat-icon {
          font-size: 2.5rem;
          margin-right: 1rem;
        }

        .stat-info h3 {
          margin: 0 0 0.5rem 0;
          color: #64748b;
          font-size: 0.875rem;
          font-weight: 500;
        }

        .stat-number {
          margin: 0 0 0.25rem 0;
          font-size: 2rem;
          font-weight: 700;
          color: #1e293b;
        }

        .stat-change {
          font-size: 0.875rem;
          font-weight: 500;
        }

        .stat-change.increase { color: #10b981; }
        .stat-change.decrease { color: #ef4444; }
        .stat-change.stable { color: #64748b; }

        .activity-section, .chart-section {
          background: white;
          padding: 1.5rem;
          border-radius: 12px;
          box-shadow: 0 1px 3px rgba(0,0,0,0.1);
          margin-bottom: 2rem;
        }

        .activity-section h2, .chart-section h2 {
          margin: 0 0 1.5rem 0;
          color: #1e293b;
          font-size: 1.25rem;
          font-weight: 600;
        }

        .activity-feed {
          space-y: 1rem;
        }

        .activity-item {
          display: flex;
          align-items: center;
          padding: 1rem;
          margin-bottom: 1rem;
          border-radius: 8px;
          border-left: 4px solid #e2e8f0;
        }

        .activity-item.bot { border-left-color: #ef4444; background: #fef2f2; }
        .activity-item.human { border-left-color: #10b981; background: #f0fdf4; }
        .activity-item.warning { border-left-color: #f59e0b; background: #fffbeb; }
        .activity-item.blocked { border-left-color: #8b5cf6; background: #faf5ff; }

        .activity-icon {
          margin-right: 1rem;
          font-size: 1.5rem;
        }

        .activity-details p {
          margin: 0 0 0.25rem 0;
          color: #374151;
        }

        .activity-time {
          color: #6b7280;
          font-size: 0.875rem;
        }

        .chart-placeholder {
          background: #f8fafc;
          border: 2px dashed #cbd5e1;
          border-radius: 8px;
          padding: 3rem;
          text-align: center;
          color: #64748b;
        }

        .chart-placeholder p {
          margin: 0.5rem 0;
          font-size: 1.1rem;
        }

        @media (max-width: 768px) {
          .dashboard {
            position: relative;
            height: auto;
            min-height: 100vh;
          }
          
          .dashboard-body {
            flex-direction: column;
            height: auto;
            min-height: calc(100vh - 80px);
          }
          
          .left-sidebar {
            width: 100%;
            min-width: 100%;
            order: 2;
            height: auto;
          }
          
          .main-content {
            order: 1;
            height: auto;
          }
          
          .navbar-pages {
            display: none;
          }
          
          .stats-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
};

export default Authenticate_user;

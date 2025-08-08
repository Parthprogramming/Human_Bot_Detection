const { chromium } = require('playwright');

(async () => {
  let browser;
  try {
    // Launch browser with stealth settings
    browser = await chromium.launch({
      headless: false,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-blink-features=AutomationControlled',
        '--disable-infobars',
        '--disable-dev-shm-usage',
        '--disable-web-security',
        '--disable-features=VizDisplayCompositor'
      ]
    });

    const context = await browser.newContext({
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      viewport: { width: 1920, height: 1080 },
      locale: 'en-US',
      timezoneId: 'America/New_York',
      permissions: ['geolocation'],
      geolocation: { latitude: 40.7128, longitude: -74.0060 },
      colorScheme: 'light'
    });

    const page = await context.newPage();

    // Add stealth scripts
    await page.addInitScript(() => {
      // Override webdriver property
      Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined,
      });
      
      // Override plugins
      Object.defineProperty(navigator, 'plugins', {
        get: () => [1, 2, 3, 4, 5],
      });
      
      // Override languages
      Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en'],
      });
    });

    // Navigate to the page
    await page.goto('http://localhost:3000/', { 
      waitUntil: 'networkidle',
      timeout: 30000 
    });

    // Wait for input field
    await page.waitForSelector('input[placeholder="Enter USAI ID"]');
    await page.type('input[placeholder="Enter USAI ID"]', 'kalwa741', { delay: 50 + Math.random() * 100 });

    // Add some mouse movement before clicking
    const button = await page.getByRole('button', { name: /verify/i })
   
    await button.hover();
    
    // Wait a bit before clicking
    await page.waitForTimeout(500 + Math.random() * 1000);
    
    // Click with human-like behavior
    await button.click({ delay: 100 });

    // Wait for response
    await page.waitForTimeout(5000);

    console.log('Playwright test completed successfully!');

  } catch (error) {
    console.error('Playwright test failed:', error.message);
  } finally {
    if (browser) {
      await browser.close();
    }
  }
})();
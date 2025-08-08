const puppeteer = require('puppeteer');
const { createCursor } = require('ghost-cursor');

// Utility function for delays
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

// Utility function to type with natural delays
const typeWithNaturalDelays = async (page, text) => {
  for (let char of text) {
    await page.keyboard.type(char, { delay: 100 + Math.random() * 100 });
    await delay(50 + Math.random() * 100);
  }
};

// Error handling wrapper
const safeExecute = async (fn, errorMsg) => {
  try {
    return await fn();
  } catch (error) {
    console.error(`${errorMsg}: ${error.message}`);
    throw error;
  }
};

(async () => {
  let browser;
  try {
    // Launch browser with specific settings
    browser = await safeExecute(
      () => puppeteer.launch({
        headless: false,
        defaultViewport: null,
        args: [
          '--start-maximized',
          '--no-sandbox',
          '--disable-setuid-sandbox',
          '--disable-dev-shm-usage',
          '--disable-accelerated-2d-canvas',
          '--disable-gpu'
        ],
        ignoreHTTPSErrors: true
      }),
      'Failed to launch browser'
    );

    const [page] = await browser.pages();
    
    // Set up page settings
    await safeExecute(
      async () => {
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
        await page.setViewport({ width: 1920, height: 1080 });
        await page.setDefaultNavigationTimeout(30000);
      },
      'Failed to configure page settings'
    );

    // Navigate to the page
    await safeExecute(
      () => page.goto('http://localhost:3000/', { 
        waitUntil: 'networkidle2',
        timeout: 30000 
      }),
      'Failed to navigate to page'
    );

    // Create cursor with natural movement
    const cursor = createCursor(page, {
      // Add some randomness to cursor movement
      movementCurve: (t) => t * (1 + Math.random() * 0.1),
      // Add slight acceleration/deceleration
      movementSpeed: () => 0.5 + Math.random() * 0.3
    });

    // Wait for and interact with input field
    await safeExecute(
      async () => {
        // Wait for input using placeholder selector
        await page.waitForSelector('input[placeholder="Enter USAI ID"]', { visible: true, timeout: 5000 });
        
        // Find the input element
        const inputElement = await page.$('input[placeholder="Enter USAI ID"]');
        
        if (!inputElement) {
          throw new Error('Input field not found');
        }

        // Move cursor naturally to input field
        await cursor.move(inputElement, { duration: 1000 + Math.random() * 500 });
        await cursor.click();

        // Add natural pause after clicking
        await delay(300 + Math.random() * 200);

        // Type with natural delays using our custom function
        await typeWithNaturalDelays(page, "mumbra0987");
      },
      'Failed to interact with input field'
    );

    await delay(1000 + Math.random() * 500);

    // Wait for and click verify button
    await safeExecute(
      async () => {
        // Find all buttons and select the one with text 'Verify'
        const buttons = await page.$$('button');
        let verifyButton = null;
        for (const btn of buttons) {
          const text = await page.evaluate(el => el.textContent, btn);
          if (text && text.trim().includes('Verify')) {
            verifyButton = btn;
            break;
          }
        }
        if (!verifyButton) {
          throw new Error('Verify button not found');
        }
        // Move cursor naturally to button
        await cursor.move(verifyButton, { duration: 800 + Math.random() * 400 });
        await cursor.click();
      },
      'Failed to interact with verify button'
    );

    // Wait for response
    await delay(5000);

  } catch (error) {
    console.error('Test failed:', error);
    process.exit(1);
  } finally {
    if (browser) {
      await browser.close();
    }
  }
})();




// const puppeteer = require('puppeteer');
// const { createCursor } = require('ghost-cursor');

// // Utility function for delays
// const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

// // Utility function to type with natural delays
// const typeWithNaturalDelays = async (page, text) => {
//   for (let char of text) {
//     await page.keyboard.type(char, { delay: 100 + Math.random() * 100 });
//     await delay(50 + Math.random() * 100);
//   }
// };

// // Error handling wrapper
// const safeExecute = async (fn, errorMsg) => {
//   try {
//     return await fn();
//   } catch (error) {
//     console.error(`${errorMsg}: ${error.message}`);
//     throw error;
//   }
// };

// (async () => {
//   let browser;
//   try {
//     // Launch browser with specific settings
//     browser = await safeExecute(
//       () => puppeteer.launch({
//         headless: false,
//         defaultViewport: null,
//         args: [
//           '--start-maximized',
//           '--no-sandbox',
//           '--disable-setuid-sandbox',
//           '--disable-dev-shm-usage',
//           '--disable-accelerated-2d-canvas',
//           '--disable-gpu'
//         ],
//         ignoreHTTPSErrors: true
//       }),
//       'Failed to launch browser'
//     );

//     const [page] = await browser.pages();
    
//     // Set up page settings
//     await safeExecute(
//       async () => {
//         await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
//         await page.setViewport({ width: 1920, height: 1080 });
//         await page.setDefaultNavigationTimeout(30000);
//       },
//       'Failed to configure page settings'
//     );

//     // Navigate to the page
//     await safeExecute(
//       () => page.goto('http://localhost:3000/', { 
//         waitUntil: 'networkidle2',
//         timeout: 30000 
//       }),
//       'Failed to navigate to page'
//     );

//     // Create cursor with natural movement
//     const cursor = createCursor(page, {
//       // Add some randomness to cursor movement
//       movementCurve: (t) => t * (1 + Math.random() * 0.1),
//       // Add slight acceleration/deceleration
//       movementSpeed: () => 0.5 + Math.random() * 0.3
//     });

//     // Wait for and interact with input field
//     await safeExecute(
//       async () => {
//         await page.waitForSelector('#inputfield', { visible: true, timeout: 5000 });
//         const inputElement = await page.type('input[placeholder="Enter USAI ID"]', 'testuser');

        
//         if (!inputElement) {
//           throw new Error('Input field not found');
//         }

//         // Move cursor naturally to input field
//         await cursor.move(inputElement, { duration: 1000 + Math.random() * 500 });
//         await cursor.click();
//         await inputElement.focus();
//         await delay(500 + Math.random() * 300);

//         // Type with natural delays using Puppeteer's keyboard API
//         await typeWithNaturalDelays(page, "mumbra0987");
//       },
//       'Failed to interact with input field'
//     );

//     await delay(1000 + Math.random() * 500);

//     // Wait for and click verify button
//     await safeExecute(
//       async () => {
//         await page.waitForSelector('#tosubmitform', { visible: true, timeout: 5000 });
//         const verifyButton = await page.$('#tosubmitform');
        
//         if (!verifyButton) {
//           throw new Error('Verify button not found');
//         }

//         // Move cursor naturally to button
//         await cursor.move(verifyButton, { duration: 800 + Math.random() * 400 });
//         await cursor.click();
        
//       },
//       'Failed to interact with verify button'
//     );

//     // Wait for response
//     await delay(5000);

//   } catch (error) {
//     console.error('Test failed:', error);
//     process.exit(1);
//   } finally {
//     if (browser) {
//       await browser.close();
//     }
//   }
// })();
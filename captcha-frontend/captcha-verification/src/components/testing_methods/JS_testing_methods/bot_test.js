const puppeteer = require('puppeteer');
const http = require('http');

// Utility function to wait for server
const waitForServer = async (url, maxRetries = 5, retryDelay = 2000) => {
  const { hostname, port, pathname } = new URL(url);
  for (let i = 0; i < maxRetries; i++) {
    try {
      await new Promise((resolve, reject) => {
        const req = http.request({
          hostname,
          port,
          path: pathname,
          method: 'GET',
          timeout: 1500
        }, res => {
          if (res.statusCode >= 200 && res.statusCode < 400) resolve();
          else reject(new Error('Bad status: ' + res.statusCode));
        });
        req.on('error', reject);
        req.on('timeout', () => req.destroy());
        req.end();
      });
      return true;
    } catch (error) {
      console.log(`Attempt ${i + 1}/${maxRetries}: Server not ready, retrying in ${retryDelay/1000} seconds...`);
      await new Promise(resolve => setTimeout(resolve, retryDelay));
    }
  }
  throw new Error(`Server not available at ${url} after ${maxRetries} attempts`);
};

(async () => {
  let browser;
  try {
    // Wait for server to be ready
    console.log('Waiting for React server to start...');
    // Try both localhost and 127.0.0.1 for maximum compatibility
    try {
      await waitForServer('http://localhost:3000');
    } catch (e) {
      console.log('localhost failed, trying 127.0.0.1...');
      await waitForServer('http://127.0.0.1:3000');
    }
    console.log('Server is ready!');

    // Launch browser
    console.log('Launching browser...');
    browser = await puppeteer.launch({
      headless: false,
      defaultViewport: null,
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();
    
    // Set a reasonable timeout
    page.setDefaultNavigationTimeout(30000);
    page.setDefaultTimeout(30000);

    // Navigate to the page
    console.log('Navigating to the page...');
    await page.goto('http://192.168.1.7:3000', { 
      waitUntil: 'networkidle2',
      timeout: 30000 
    });

    // Wait for the input field using placeholder
    console.log('Waiting for input field...');
    await page.waitForSelector('input[placeholder="Enter USAI ID"]', { visible: true, timeout: 5000 });

    // Add some random mouse movement before typing
    const inputField = await page.$('input[placeholder="Enter USAI ID"]');
    const inputBox = await inputField.boundingBox();
    await page.mouse.move(
      inputBox.x + inputBox.width / 2 + (Math.random() * 20 - 10),
      inputBox.y + inputBox.height / 2 + (Math.random() * 20 - 10),
      { steps: 10 }
    );

    // Click the input with a small random offset
    await page.mouse.click(
      inputBox.x + inputBox.width / 2 + (Math.random() * 6 - 3),
      inputBox.y + inputBox.height / 2 + (Math.random() * 6 - 3)
    );

    // Type with variable delays
    console.log('Typing USAI ID...');
    for (const char of 'kanjurmarg852456') {
      await page.keyboard.type(char, { delay: 100 + Math.random() * 200 });
      await new Promise(r => setTimeout(r, 50 + Math.random() * 150));
    }

    // Add natural pause before clicking submit
    await new Promise(r => setTimeout(r, 800 + Math.random() * 1200));

    // Wait for and click the submit button
    console.log('Clicking submit button...');
    
    // Wait for any button containing "Verify" text
    const submitButton = await page.waitForSelector('button', {
      visible: true,
      timeout: 5000
    });

    // Verify we found the right button
    const buttonText = await page.evaluate(button => button.textContent, submitButton);
    if (!buttonText.includes('Verify')) {
      throw new Error('Could not find Verify button');
    }

    const buttonBox = await submitButton.boundingBox();
    
    // Move mouse in a slightly curved path
    await page.mouse.move(
      buttonBox.x + buttonBox.width / 2 + (Math.random() * 30 - 15),
      buttonBox.y + buttonBox.height / 2 + (Math.random() * 30 - 15),
      { steps: 15 }
    );

    // Hover briefly before clicking
    await new Promise(r => setTimeout(r, 200 + Math.random() * 300));

    // Click with a small random offset
    await page.mouse.click(
      buttonBox.x + buttonBox.width / 2 + (Math.random() * 4 - 2),
      buttonBox.y + buttonBox.height / 2 + (Math.random() * 4 - 2)
    );
    
    // Wait for backend processing with variable delay
    await new Promise(resolve => setTimeout(resolve, 8000 + Math.random() * 2000));

    // Wait for response
    console.log('Waiting for response...');

    console.log('Test completed successfully!');

  } catch (error) {
    console.error('Test failed:', error.message);
    if (error.message.includes('ERR_CONNECTION_REFUSED')) {
      console.error('\nMake sure your React application is running!');
      console.error('Run this in a separate terminal:');
      console.error('cd "D:\\Parth folder\\authnpayy\\Captcha\\captcha-frontend\\captcha-verification"');
      console.error('npm start');
    }
    process.exit(1);
  } finally {
    if (browser) {
      await browser.close();
    }
  }
})();




// const puppeteer = require('puppeteer');

// // Utility function to wait for server
// const waitForServer = async (url, maxRetries = 5, retryDelay = 2000) => {
//   for (let i = 0; i < maxRetries; i++) {
//     try {
//       const response = await fetch(url);
//       if (response.ok) return true;
//     } catch (error) {
//       console.log(`Attempt ${i + 1}/${maxRetries}: Server not ready, retrying in ${retryDelay/1000} seconds...`);
//       await new Promise(resolve => setTimeout(resolve, retryDelay));
//     }
//   }
//   throw new Error(`Server not available at ${url} after ${maxRetries} attempts`);
// };

// (async () => {
//   let browser;
//   try {
//     // Wait for server to be ready
//     console.log('Waiting for React server to start...');
//     await waitForServer('http://192.168.1.7:3000');
//     console.log('Server is ready!');

//     // Launch browser
//     console.log('Launching browser...');
//     browser = await puppeteer.launch({
//       headless: false,
//       defaultViewport: null,
//       args: ['--no-sandbox', '--disable-setuid-sandbox']
//     });

//     const page = await browser.newPage();
    
//     // Set a reasonable timeout
//     page.setDefaultNavigationTimeout(30000);
//     page.setDefaultTimeout(30000);

//     // Navigate to the page
//     console.log('Navigating to the page...');
//     await page.goto('http://192.168.1.7:3000', { 
//       waitUntil: 'networkidle2',
//       timeout: 30000 
//     });

//     // Wait for the input field
//     console.log('Waiting for input field...');
//     await page.waitForSelector('#inputfield', { visible: true, timeout: 5000 });

//     // Type in a form slowly
//     console.log('Typing USAI ID...');
//     await page.type('#inputfield', 'kanjurmarg852456', { delay: 150 });

//     // Wait for and click the submit button
//     console.log('Clicking submit button...');
//     await page.waitForSelector('#tosubmitform', { visible: true, timeout: 5000 });
//     await page.click('#tosubmitform');
    
//     await new Promise(resolve => setTimeout(resolve, 9000));

//     // Wait for response
//     console.log('Waiting for response...');

//     console.log('Test completed successfully!');

//   } catch (error) {
//     console.error('Test failed:', error.message);
//     if (error.message.includes('ERR_CONNECTION_REFUSED')) {
//       console.error('\nMake sure your React application is running!');
//       console.error('Run this in a separate terminal:');
//       console.error('cd "D:\\Parth folder\\authnpayy\\Captcha\\captcha-frontend\\captcha-verification"');
//       console.error('npm start');
//     }
//     process.exit(1);
//   } finally {
//     if (browser) {
//       await browser.close();
//     }
//   }
// })();


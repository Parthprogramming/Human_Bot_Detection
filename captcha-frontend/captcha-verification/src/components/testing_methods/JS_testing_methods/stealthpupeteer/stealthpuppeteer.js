// bot_puppeteer.js
const puppeteer = require('puppeteer-extra');
const {executablePath} = require('puppeteer');
const StealthPlugin   = require('puppeteer-extra-plugin-stealth');

puppeteer.use(StealthPlugin());

(async () => {
  const browser = await puppeteer.launch({
    headless: false,
    executablePath: executablePath(),         // use local Chrome
    defaultViewport: {width: 1280, height: 900}
  });
  const [page] = await browser.pages();
  await page.goto('http://localhost:3000/', {waitUntil: 'domcontentloaded'});

  // Human-style scroll
  for (let y = 0; y <= 600; y += 60) {
    await page.evaluate(scrollY => window.scrollTo(0, scrollY), y);
    await new Promise(resolve => setTimeout(resolve, 200));
  }

  // Type ID with delays
  const input = await page.waitForSelector('input[placeholder="Enter USAI ID"]', { visible: true, timeout: 5000 });

  await input.click({delay: 80});
  for (const ch of 'jupiter5002') {
    await page.keyboard.type(ch, {delay: Math.random() * 120 + 80});
  }

  // Find and click the 'Verify' button by text
  const buttons = await page.$$('button');
  let verifyButton = null;
  for (const btn of buttons) {
    const text = await page.evaluate(el => el.textContent, btn);
    if (text && text.trim().toLowerCase().includes('verify')) {
      verifyButton = btn;
      break;
    }
  }
  if (!verifyButton) {
    throw new Error('Verify button not found');
  }
  await verifyButton.click({delay: 120});

  await new Promise(resolve => setTimeout(resolve, 20000)); // ✅ Works everywhere

  await browser.close();
})();

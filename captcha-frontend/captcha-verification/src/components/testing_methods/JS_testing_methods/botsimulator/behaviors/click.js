const { randomInt, sleep } = require('../utils/random');

async function click(page) {
  const keywords = ['verify', 'submit', 'check', 'next', 'continue', 'go', 'proceed'];
  let verifyButtons = [];
  let attempts = 0;
  const maxAttempts = 5;
  while (verifyButtons.length === 0 && attempts < maxAttempts) {
    const buttons = await page.$$('button');
    verifyButtons = [];
    for (const btn of buttons) {
      const text = await page.evaluate(el => el.textContent, btn);
      if (text && keywords.some(k => text.trim().toLowerCase().includes(k))) {
        verifyButtons.push(btn);
      }
    }
    // Also check for <input type="submit"> elements
    const inputs = await page.$$('input[type="submit"]');
    for (const inp of inputs) {
      const value = await page.evaluate(el => el.value, inp);
      if (value && keywords.some(k => value.trim().toLowerCase().includes(k))) {
        verifyButtons.push(inp);
      }
    }
    // Optionally check for [role=button] elements
    const roleButtons = await page.$$('[role="button"]');
    for (const btn of roleButtons) {
      const text = await page.evaluate(el => el.textContent, btn);
      if (text && keywords.some(k => text.trim().toLowerCase().includes(k))) {
        verifyButtons.push(btn);
      }
    }
    if (verifyButtons.length === 0) {
      await sleep(400); // Wait a bit and retry
      attempts++;
    }
  }
  if (verifyButtons.length > 0) {
    const btn = verifyButtons[randomInt(0, verifyButtons.length - 1)];
    await btn.click();
    await sleep(randomInt(100, 1000));
  } else {
    console.warn('⚠️ Verify/Submit button not found after retries.');
  }
}
module.exports = click;

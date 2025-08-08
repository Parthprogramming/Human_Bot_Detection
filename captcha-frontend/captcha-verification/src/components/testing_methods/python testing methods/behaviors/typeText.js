const { sleep } = require('../../utils/random');
const { typingText } = require('../../config');

async function typeText(page) {
  try {
    // Wait for any of the input selectors to be available
    await page.waitForSelector('input, textarea, [contenteditable="true"]', { timeout: 5000 });

    // Query all possible targets
    const inputHandle = await page.$('input[type="text"]') ||
                        await page.$('textarea') ||
                        await page.$('[contenteditable="true"]') ||
                        await page.$('input');

    if (inputHandle) {
      await inputHandle.focus();

      console.log('✅ Typing into element:', await page.evaluate(el => el.tagName, inputHandle));

      // Type text realistically
      for (const char of typingText) {
        await page.keyboard.type(char, { delay: Math.random() * 200 });
        await sleep(50);
      }
    } else {
      console.warn('⚠️ No input element found to type into.');
    }
  } catch (err) {
    console.error('❌ Error in typeText:', err.message);
  }
}

module.exports = typeText;

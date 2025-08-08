// behaviors/enterUsaiId.js

const { sleep } = require('../../utils/random');
const { usaiId } = require('../../config');

async function enterUsaiId(page) {
  try {
    // ✅ Wait for input field with ID "inputfield"
    await page.waitForSelector('#inputfield', { timeout: 5000 });

    const inputHandle = await page.$('#inputfield');

    if (inputHandle) {
      await inputHandle.click({ clickCount: 3 }); // clear previous text if any
      await inputHandle.focus();
      await page.keyboard.type(usaiId, { delay: Math.random() * 150 });
      console.log(`✅ USAI ID entered: ${usaiId}`);
      await sleep(300);
    } else {
      console.warn('⚠️ Could not find USAI ID input field.');
    }

    // ✅ Click the button with ID "tosubmitform"
    const verifyBtn = await page.$('#tosubmitform');
    if (verifyBtn) {
      await verifyBtn.click();
      console.log('✅ Verify button clicked.');
      await sleep(500);
    } else {
      console.warn('⚠️ Verify button not found.');
    }
  } catch (err) {
    console.error('❌ Error in enterUsaiId:', err.message);
  }
}

module.exports = enterUsaiId;

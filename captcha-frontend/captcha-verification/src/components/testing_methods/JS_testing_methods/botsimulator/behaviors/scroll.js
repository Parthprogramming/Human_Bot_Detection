const { randomInt, sleep } = require('../utils/random');

async function scroll(page) {
  try {
    const isScrollable = await page.evaluate(() => {
      return document.body.scrollHeight > window.innerHeight;
    });

    if (!isScrollable) {
      console.warn('⚠️ Page is not scrollable. Skipping scroll behavior.');
      return;
    }

    console.log('🌀 Scrolling the page...');
    for (let i = 0; i < randomInt(5, 15); i++) {
      const step = randomInt(100, 500);
      await page.evaluate((step) => {
        window.scrollBy({ top: step, behavior: 'smooth' });
      }, step);
      await sleep(randomInt(400, 800));
    }

    console.log('✅ Done scrolling.');
  } catch (err) {
    console.error('❌ Scroll behavior failed:', err.message);
  }
}

module.exports = scroll;

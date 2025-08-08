const puppeteer = require('puppeteer');
const { url } = require('./config');
const { randomChoice } = require('./utils/random');

const enterUsaiId = require('./behaviors/enterUsaiId');

const behaviors = {
  mouse: require('./behaviors/mouseMove'),
  scroll: require('./behaviors/scroll'),
  type: require('./behaviors/typeText'),
  paste: require('./behaviors/pasteAction'),
  idle: require('./behaviors/idle'),
  click: require('./behaviors/click')
};

(async () => {
  const browser = await puppeteer.launch({ headless: false });
  const page = await browser.newPage();
  await page.goto(url, { waitUntil: 'networkidle2' });

  // ✅ Mandatory: Enter USAI ID + click verify
  await enterUsaiId(page);

  // 🎲 Randomize post-verification behaviors
  const behaviorCombos = [
    ['scroll','click'],
    [ 'scroll','mouse'],
    ['scroll', 'type' ],
    ['paste', 'scroll'],
    ['click', 'scroll'],
    ['idle', 'scroll'],
    ['mouse', 'scroll'],
    ['scroll', 'type'],
    ['click', 'idle'],
    ['mouse', 'paste']
  ];

  const selectedBehaviors = randomChoice(behaviorCombos);

  for (const behavior of selectedBehaviors) {
    console.log(`Executing: ${behavior}`);
    await behaviors[behavior](page);
  }

  await browser.close();
})();

const { randomInt, sleep } = require('../utils/random');

async function mouseMove(page) {
  const box = await page.viewport();
  const movements = randomInt(10, 50);
  for (let i = 0; i < movements; i++) {
    const x = randomInt(0, box.width);
    const y = randomInt(0, box.height);
    await page.mouse.move(x, y, { steps: randomInt(5, 25) });
    await sleep(randomInt(50, 200));
  }
}
module.exports = mouseMove;

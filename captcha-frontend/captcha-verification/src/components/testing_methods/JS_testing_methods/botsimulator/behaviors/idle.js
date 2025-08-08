const { sleep, randomInt } = require('../utils/random');

async function idle(page) {
  await sleep(randomInt(3000, 10000));
}
module.exports = idle;

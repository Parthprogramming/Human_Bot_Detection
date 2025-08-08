module.exports = {
  randomInt: (min, max) => Math.floor(Math.random() * (max - min + 1)) + min,
  randomChoice: (arr) => arr[Math.floor(Math.random() * arr.length)],
  sleep: (ms) => new Promise(resolve => setTimeout(resolve, ms))
};

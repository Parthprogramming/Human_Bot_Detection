async function pasteAction(page) {
  await page.focus('input[type="text"], textarea');
  await page.evaluate(() => {
    const clipboardData = new DataTransfer();
    clipboardData.setData('text/plain', "Pasted bot data");
    const pasteEvent = new ClipboardEvent('paste', {
      clipboardData,
      bubbles: true
    });
    document.activeElement.dispatchEvent(pasteEvent);
  });
}
module.exports = pasteAction;

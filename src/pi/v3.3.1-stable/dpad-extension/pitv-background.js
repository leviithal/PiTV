// PiTV V3.1: Browser-history Back; never synthesizes Left in Netflix.
chrome.commands.onCommand.addListener((command) => {
  if (command !== 'pitv-browser-back') return;
  chrome.tabs.query({active: true, currentWindow: true})
    .then((tabs) => {
      const tab = tabs[0];
      if (!tab || typeof tab.id !== 'number') return;
      return chrome.tabs.goBack(tab.id);
    })
    .catch((error) => console.warn('PiTV Back:', error.message));
});

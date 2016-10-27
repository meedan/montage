/**
 *
 * @fileoverview Background script for Browser Action button settings
 *
 */


/**
 * Sets icon and local storage based on what current setting is
 */
var updateIcon = function() {
  if (localStorage['enabled'] == 'true') {
    localStorage['enabled'] = 'false';
    chrome.browserAction.setIcon({path: 'images/19grey.png'});
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
      chrome.tabs.sendMessage(tabs[0].id, {'method': 'disableExtension'},
          function(response) {
          });
    });
  } else {
    chrome.browserAction.setIcon({path: 'images/19.png'});
    localStorage['enabled'] = 'true';
    chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
      chrome.tabs.sendMessage(tabs[0].id, {'method': 'enableExtension'},
          function(response) {
          });
    });
  }
};


/**
 * Add Event listener to hear calls from the main app as to whether the
 * extension is enabled or not
 */
chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
  if (request.method == 'getEnabled') {
    if (localStorage['enabled'] == 'false') {
      sendResponse({'enabled': 'false'});
    } else {
      sendResponse({'enabled': 'true'});
    }
  } else {
    sendResponse({}); // Not valid request so reply with empty object
  }
});

//Initialises event listener on the browser action
chrome.browserAction.onClicked.addListener(updateIcon);
updateIcon();

// Copyright 2015 Google Inc. All Rights Reserved.

/**
 * @fileoverview Stubs for the Chrome Extension API. Used only by tests.
 * @author cosborn@google.com (Charles Douglas-Osborn)
 */

var chrome;
chrome.runtime;


/**
 * Returns mainfest version
 * @return {object}
 **/
chrome.runtime.getManifest = function() {
  var manifest = {};
  manifest.version = 1;
  return manifest;
};
chrome.runtime.onMessage;


/** Blank function **/
chrome.runtime.onMessage.addListener = function() {};
chrome.runtime.sendMessage;

chrome.tabs;


/** Blank function **/
chrome.tabs.query = function() {};


/** Blank function **/
chrome.tabs.sendMessage = function() {};

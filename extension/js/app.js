/**
 * @fileoverview Main App file for Greenday Content Script.
 */
goog.provide('greenday.extension.App');


goog.require('goog.Uri');
goog.require('goog.array');
goog.require('goog.dom');
goog.require('goog.events');
goog.require('goog.events.EventHandler');
goog.require('goog.events.EventType');
goog.require('goog.string');
goog.require('greenday.extension.ButtonBuilders');



/**
 * @constructor
 */
greenday.extension.App = function() {
  /** @type {!Array.<!Object>} Array of all projects user currently has */
  this.greendayProjects = [];

  /** @type {string} Current Video user is interacting with */
  this.currentVideo = '';

  /** @type {boolean} Whether the user is authorised on the app */
  this.unauthorised = false;

  /** @type {string} String with last checked URL */
  this.currentURL = document.URL;

  /** @type {number} Interval for checking AJax calls. */
  this.checkInterval = 0;

  /** @private {goog.events.EventHandler} */
  this.eventHandler_ = new goog.events.EventHandler(this);

  /** @type {boolean} Whether YouTubeGapi is loaded. */
  this.youtubeLoaded = false;

  // Initialise extension
  this.init();
};


/** @private @enum {string} */
greenday.extension.App.ApiConstants_ = {
  GREENDAY_API_ENDPOINT: 'https://greenday-project.appspot.com/_ah/api',
  GAPI: 'https://apis.google.com/js/client.js',
  VERSION: 'v1',
  API_NAME: 'greenday',
  API_KEY: 'AIzaSyASFlPz3OiJvgzeUCZoA9JLtUJYN89s8y0 ',
  CLIENT_ID: '583467124136-skj4h4i335dv20n8cjlp0kd2158q0ac3.apps.googleuserco' +
      'ntent.com',
  YOUTUBE_API_NAME: 'youtube',
  YOUTUBE_VERSION: 'v3'
};


/** @enum {string} @private */
greenday.extension.App.Paths_ = {
  WATCH: '/watch',
  HOME: '/',
  PLAYLISTS: '/playlists',
  CHANNEL: '/channel',
  USER: '/user',
  SEARCH: '/results',
  SUBSCRIPTIONS: '/feed/subscriptions',
  DART_IFRAME: '/doubleclick/DARTIframe.html',
  HISTORY: '/feed/history'
};


/** @const {number} */
greenday.extension.App.INTERVAL = 500;


/** @const {!Array.<string>} */
greenday.extension.App.SCOPES = [
  'https://www.googleapis.com/auth/userinfo.email',
  'https://www.googleapis.com/auth/youtube'
];


/** @type {string} */
greenday.extension.App.GREENDAY_BUTTON_CLASS = 'greenday-button';


/** @type {string} */
greenday.extension.App.GREENDAY_VIDEO_BUTTON_CLASS = 'greenday-video-button';


/**
 * Initialises the extension.
 */
greenday.extension.App.prototype.init = function() {
  if (document.readyState == 'complete') {
    this.loadUpCheck();
  } else {
    this.eventHandler_.listenOnce(goog.dom.getWindow(document),
        goog.events.EventType.LOAD, this.loadUpCheck);
  }
};


/**
 * Checks whether extension should load or not.
 */
greenday.extension.App.prototype.loadUpCheck = function() {
  chrome.runtime.sendMessage(
      {'method': 'getEnabled'}, goog.bind(this.readBackgroundResponse, this));
};


/**
 * Checks if the hash has changed (when YouTube runs Ajax).
 */
greenday.extension.App.prototype.hashHandler = function() {
  if (this.currentURL != window.location.href) {
    window.setTimeout(
        goog.bind(this.checkURLs, this), greenday.extension.App.INTERVAL);
    this.currentURL = window.location.href;
  }
};


/**
 * Removes all greenday buttons from the stage.
 * @param {Object} response
 */
greenday.extension.App.prototype.readBackgroundResponse = function(response) {
  if (response.enabled == 'true') {
    this.loadUpGapi();
    this.handleClientLoad();
    this.currentURL = window.location.href;
    this.checkInterval = setInterval(
        goog.bind(this.hashHandler, this), greenday.extension.App.INTERVAL);
    goog.events.listen(goog.dom.getDocument().body,
        goog.events.EventType.DOMNODEINSERTED,
        goog.bind(this.newNodeInserted, this));
  }
  this.addBrowserActionListener();
};


/**
 * Removes all greenday buttons from the stage.
 * @param {Event} event The event to be handled.
 */
greenday.extension.App.prototype.newNodeInserted = function(event) {
  if (!goog.dom.isElement(event.target)) {
    return;
  }
  var target = /** @type {Element} */ (event.target);
  if (target.className ==
      greenday.extension.ButtonBuilders.ClassName.THUMBNAIL ||
      goog.dom.getElementByClass(
      greenday.extension.ButtonBuilders.ClassName.THUMBNAIL,
      target) != null) {
    this.checkURLs();
  }
  event.stopPropagation();
};


/**
 * Removes all greenday buttons from the stage.
 */
greenday.extension.App.prototype.removeGreenday = function() {
  var buttons = goog.dom.getElementsByClass(
      greenday.extension.App.GREENDAY_BUTTON_CLASS);
  goog.array.forEach(buttons, function(button) {
    button.remove();
  });
  var videoButtons = goog.dom.getElementsByClass(
      greenday.extension.App.GREENDAY_VIDEO_BUTTON_CLASS);
  goog.array.forEach(videoButtons, function(button) {
    button.remove();
  });
};


/**
 * Adds event listener for Browser action to disable and enable extension.
 */
greenday.extension.App.prototype.addBrowserActionListener = function() {
  chrome.runtime.onMessage.addListener(goog.bind(function(request, sender,
      sendResponse) {
        if (request.method == 'disableExtension') {
          this.removeGreenday();
        } else if (request.method == 'enableExtension') {
          this.init();
        } else {
          sendResponse({}); // snub them.
        }
      }, this));
};


/**
 * Checks the current URL and adds button in correct locations.
 */
greenday.extension.App.prototype.checkURLs = function() {
  var url = document.URL;
  var builder = new greenday.extension.ButtonBuilders(this);
  var uri = goog.Uri.parse(url);
  var path = uri.getPath();
  // Enum alias for readability.
  var Paths_ = greenday.extension.App.Paths_;
  if (goog.string.startsWith(path, Paths_.SUBSCRIPTIONS) ||
      goog.string.startsWith(path, Paths_.PLAYLISTS) ||
      goog.string.startsWith(path, Paths_.CHANNEL) ||
      goog.string.startsWith(path, Paths_.HISTORY) ||
      goog.string.startsWith(path, Paths_.SEARCH) ||
      path == Paths_.HOME ||
      goog.string.startsWith(path, Paths_.USER)) {
    builder.addNormalPreview();
  } else if (goog.string.startsWith(path, Paths_.WATCH)) {
    builder.addVideoPageButton();
  }
};


/**
 * Get lists of current projects for the user.
 */
greenday.extension.App.prototype.getUsersProjects = function() {
  if (typeof gapi.client.greenday != 'undefined') {
    gapi.client.greenday.project.myprojects().execute(goog.bind(function(resp) {
      if (typeof resp.items !== 'undefined') {
        this.greendayProjects =  /** @type {!Array.<!Object>} */ (resp.items);
      } else if (resp.code == 401) {
        this.unauthorised = true;
      }
    }, this));
  } else {
    console.log('Problem loading Greenday');
  }
};


/**
 * Adds Gapi onto the stage.
 */
greenday.extension.App.prototype.loadUpGapi = function() {
  var head = document.getElementsByTagName('head')[0];
  var gapiScript = document.createElement('script');
  gapiScript.src = greenday.extension.App.ApiConstants_.GAPI;
  head.appendChild(gapiScript);
};


/**
 * Sets API Key and starts Auth.
 */
greenday.extension.App.prototype.handleClientLoad = function() {
  if (typeof gapi != 'undefined' && typeof gapi.client != 'undefined') {
    gapi.client.setApiKey(greenday.extension.App.ApiConstants_.API_KEY);
    window.setTimeout(goog.bind(this.checkAuth, this), 1);
  } else {
    window.setTimeout(goog.bind(this.handleClientLoad, this),
        greenday.extension.App.INTERVAL);
  }
};


/**
 * Checks to see whether user is logged in or not.
 */
greenday.extension.App.prototype.checkAuth = function() {
  var url = document.URL;
  var uri = goog.Uri.parse(url);
  var path = uri.getPath();
  if (!goog.string.startsWith(
      path, greenday.extension.App.Paths_.DART_IFRAME)) {
    this.unauthorised = true;
    gapi.auth.authorize({
      client_id: greenday.extension.App.ApiConstants_.CLIENT_ID,
      scope: greenday.extension.App.SCOPES,
      immediate: true
    }, goog.bind(this.handleAuthResult, this));
  }
};


/**
 * Handles result of OAuth check.
 * @param {Object} authResult
 */
greenday.extension.App.prototype.handleAuthResult = function(authResult) {
  if (authResult && !authResult.error) {
    this.loadGreendayAPI();
    this.unauthorised = false;
  } else if (authResult && authResult.error == 'immediate_failed') {
    gapi.auth.authorize({
      client_id: greenday.extension.App.ApiConstants_.CLIENT_ID,
      scope: greenday.extension.App.SCOPES,
      immediate: false
    }, goog.bind(this.handleAuthResult, this));
  } else {
    this.unauthorised = true;
  }
};


/**
 * Button to force a window open for user to login fully.
 * @param {!goog.events.Event} event Event caused by click.
 */
greenday.extension.App.prototype.handleAuthClick = function(event) {
  gapi.auth.authorize({
    client_id: greenday.extension.App.ApiConstants_.CLIENT_ID,
    scope: greenday.extension.App.SCOPES, immediate: false},
      goog.bind(this.handleAuthResult, this));
};


/**
 * Loads the Greenday API up.
 */
greenday.extension.App.prototype.loadGreendayAPI = function() {
  gapi.client.load(greenday.extension.App.ApiConstants_.API_NAME,
      greenday.extension.App.ApiConstants_.VERSION,
      goog.bind(function() {
        this.getUsersProjects();
        this.checkURLs();
      }, this), greenday.extension.App.ApiConstants_.GREENDAY_API_ENDPOINT);

  // Load up YouTube API as well as well.
  gapi.client.load(
      greenday.extension.App.ApiConstants_.YOUTUBE_API_NAME,
      greenday.extension.App.ApiConstants_.YOUTUBE_VERSION,
      goog.bind(function() {
        this.youtubeLoaded = true;
      }, this));
};

var GreendayExtension = new greenday.extension.App();

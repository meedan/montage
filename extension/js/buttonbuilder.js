/**
 * @fileoverview Button creation utilities
 */
goog.provide('greenday.extension.ButtonBuilders');

goog.require('goog.Uri');
goog.require('goog.array');
goog.require('goog.dom');
goog.require('goog.dom.TagName');
goog.require('goog.dom.classes');
goog.require('goog.events.EventHandler');
goog.require('goog.events.EventType');
goog.require('goog.style');



/**
 * Service for building greenday buttons on the current page.
 * @param {!greenday.extension.App} app Instance of App.
 * @constructor
 */
greenday.extension.ButtonBuilders = function(app) {

  /** @private {!greenday.extension.App} */
  this.app_ = app;

  /** @private {string} */
  this.currentVideo_ = '';

  /** @private {!goog.events.EventHandler} */
  this.eventHandler_ = new goog.events.EventHandler(this);

};


/** @const {string} */
greenday.extension.ButtonBuilders.GREENDAY_ICON =
    chrome.extension.getURL('images/miniIcon.png');


/** @const {string} */
greenday.extension.ButtonBuilders.GREENDAY_BASE =
    'https://montage.withgoogle.com';


/** @const {string} */
greenday.extension.ButtonBuilders.PROJECT_BASE =
    greenday.extension.ButtonBuilders.GREENDAY_BASE + '/projects/';


/** @const {string} */
greenday.extension.ButtonBuilders.NO_PROJECTS =
    '<br><br><p style="text-align:center">' +
    'No projects yet, please create one below</p>';


/** @enum {string} */
greenday.extension.ButtonBuilders.PopupSize = {
  WIDTH: '200px',
  HEIGHT: '200px'
};


/** @enum {string} */
greenday.extension.ButtonBuilders.DomId = {
  PRE_CHECKBOX: 'checkbox-project-',
  VIDEO_PAGE_INSERT_DIV: 'watch8-secondary-actions',
  GREENDAY_POPUP: 'greenday-popup',
  VIDEO_ACTION: 'yt-uix-videoactionmenu-menu',
  POPUP_INNER: 'greenday-popup-inner',
  GREENDAY_MENU: 'greenday-menu'
};


/** @enum {string} */
greenday.extension.ButtonBuilders.Copy = {
  ADD_TO: 'Add To Montage',
  ADD_TO_HEADER: 'Add To',
  LOGIN_TEXT: 'You are not authorised. Login here',
  LOGIN_BUTTON_TEXT: 'Login',
  CREATE_PROJECT: 'Create new project',
  CHECKBOX_ADD: 'Click to add video to this project'
};
// TODO(cosborn): Localise


/** @enum {string} */
greenday.extension.ButtonBuilders.ClassName = {
  BUTTON: 'yt-uix-button yt-uix-button-size-small ' +
      'yt-uix-button-default yt-uix-button-empty yt-uix-button-has-icon ' +
      'greenday-button addto-queue-button video-actions spf-nolink ' +
      'hide-until-delayloaded addto-greenday-button yt-uix-tooltip',
  LOGIN_BUTTON: 'yt-uix-button  yt-uix-sessionlink ' +
      'yt-uix-button-default yt-uix-button-size-default',
  POPUP: 'yt-ui-menu-content yt-uix-menu-content ' +
      'yt-uix-menu-content-external yt-uix-kbd-nav',
  ADD_BUTTON: 'greenday-video-button',
  NOT_AUTHORISED: 'greenday-not-authorised',
  POPUP_INNER: 'greenday-popup-inner add-to-widget',
  LOADING: 'greenday-loading',
  MENU_ITEM: 'addto-playlist-item yt-uix-button-menu-item',
  MENU_ITEM_CHECKBOX: 'playlist-status',
  MENU_ITEM_PROJECT: 'playlist-name',
  GREENDAY_MENU: 'playlists yt-uix-scroller',
  CREATE_PROJECT: 'create-playlist-item yt-uix-button-menu-item ' +
      'menu-panel active-panel greenday-new-project',
  CHECKBOX_SELECTED: 'contains-all-selected-videos',
  THUMBNAIL: 'yt-lockup-thumbnail',
  CHECKBOX_LOADING: 'greenday-checkbox-loading'
};


/** @enum {string} */
greenday.extension.ButtonBuilders.Attribute = {
  GREENDAY_ID: 'greenday-video-id'
};


/**
 * Adds greenday button to Video viewing page.
 */
greenday.extension.ButtonBuilders.prototype.addVideoPageButton = function() {
  if (goog.dom.getElement(
      greenday.extension.ButtonBuilders.DomId.VIDEO_PAGE_INSERT_DIV) == null) {
    window.setTimeout(function() {
      this.addVideoPageButton();
    }.bind(this), 500);
    return;
  }

  var url = document.URL;
  var uri = goog.Uri.parse(url);
  this.currentVideo_ = uri.getParameterValue('v') || '';

  var checkerButton = goog.dom.getElementByClass(
      greenday.extension.ButtonBuilders.ClassName.ADD_BUTTON,
      goog.dom.getElement(
          greenday.extension.ButtonBuilders.DomId.VIDEO_PAGE_INSERT_DIV));
  if (checkerButton != null) {
    return;
  }
  var button = goog.dom.createDom(goog.dom.TagName.BUTTON,
      greenday.extension.ButtonBuilders.ClassName.BUTTON + ' ' +
      greenday.extension.ButtonBuilders.ClassName.ADD_BUTTON);
  button.setAttribute('data-tooltip-text',
      greenday.extension.ButtonBuilders.Copy.ADD_TO);
  var icon = goog.dom.createDom(goog.dom.TagName.IMG, {
    src: greenday.extension.ButtonBuilders.GREENDAY_ICON
  });
  goog.dom.appendChild(button, icon);
  button.onclick = function() { return false; };
  this.eventHandler_.listen(button, goog.events.EventType.CLICK,
      function(buttonEvent) {
        this.showGreendayMenu(buttonEvent, button, this.currentVideo_);
      });

  goog.dom.appendChild(
      goog.dom.getElement(
          greenday.extension.ButtonBuilders.DomId.VIDEO_PAGE_INSERT_DIV),
      button);
};


/**
 * Shows the Popup Menu of Projects to add to.
 * @param {!goog.events.Event} buttonEvent Event caused by click.
 * @param {!Element} addButton Button which has the event.
 * @param {string} videoId What the YouTube Video ID is.
 */
greenday.extension.ButtonBuilders.prototype.showGreendayMenu =
    function(buttonEvent, addButton, videoId) {
  this.closeExtension();
  buttonEvent.stopPropagation();
  this.currentVideo_ = videoId;
  var top = goog.style.getPageOffsetTop(addButton) +
      goog.style.getSize(addButton).height;
  var left = goog.style.getPageOffsetLeft(addButton);
  var menuDiv = goog.dom.createDom(goog.dom.TagName.DIV,
      greenday.extension.ButtonBuilders.ClassName.POPUP);
  menuDiv.setAttribute('id',
      greenday.extension.ButtonBuilders.DomId.GREENDAY_POPUP);
  menuDiv.style.top = top + 'px';
  menuDiv.style.left = left + 'px';
  menuDiv.style.width = greenday.extension.ButtonBuilders.PopupSize.WIDTH;
  menuDiv.style.height = greenday.extension.ButtonBuilders.PopupSize.HEIGHT;
  goog.dom.appendChild(document.body, menuDiv);
  if (this.app_.unauthorised) {
    var noAuthDiv = goog.dom.createDom(goog.dom.TagName.DIV,
        greenday.extension.ButtonBuilders.ClassName.NOT_AUTHORISED);
    goog.dom.setTextContent(noAuthDiv,
        greenday.extension.ButtonBuilders.Copy.LOGIN_TEXT);
    goog.dom.appendChild(menuDiv, noAuthDiv);

    var loginButton = goog.dom.createDom(goog.dom.TagName.DIV,
        greenday.extension.ButtonBuilders.ClassName.LOGIN_BUTTON);
    loginButton.innerHTML =
        greenday.extension.ButtonBuilders.Copy.LOGIN_BUTTON_TEXT;
    goog.dom.appendChild(menuDiv, loginButton);
    this.eventHandler_.listen(loginButton, goog.events.EventType.CLICK,
        goog.bind(this.app_.handleAuthClick, this.app_));
  } else {
    var videoAction = goog.dom.createElement(goog.dom.TagName.DIV);
    videoAction.setAttribute('id',
        greenday.extension.ButtonBuilders.DomId.VIDEO_ACTION);
    goog.dom.appendChild(menuDiv, videoAction);

    var addToHeader = goog.dom.createElement(goog.dom.TagName.H3);
    goog.dom.setTextContent(addToHeader,
        greenday.extension.ButtonBuilders.Copy.ADD_TO_HEADER);
    goog.dom.appendChild(videoAction, addToHeader);

    var popupInner = goog.dom.createDom(goog.dom.TagName.DIV,
        greenday.extension.ButtonBuilders.ClassName.POPUP_INNER);
    popupInner.setAttribute('id',
        greenday.extension.ButtonBuilders.DomId.POPUP_INNER);
    goog.dom.appendChild(videoAction, popupInner);

    var loader = goog.dom.createDom(goog.dom.TagName.DIV,
        greenday.extension.ButtonBuilders.ClassName.LOADING);
    goog.dom.appendChild(popupInner, loader);

    this.setupProjects('');
  }

  this.eventHandler_.listen(document, goog.events.EventType.CLICK,
      this.closeListener_);
};


/**
 * Add Projects to Menu
 * @param {!Array.<!Object>} greendayProjects
 * @param {!Element} menu
 * @param {!Array.<!Object>} items
 */
greenday.extension.ButtonBuilders.prototype.addProjects =
    function(greendayProjects, menu, items) {
  goog.array.forEach(greendayProjects, goog.bind(function(project, id) {
    var li = goog.dom.createDom('li',
        greenday.extension.ButtonBuilders.ClassName.MENU_ITEM);
    var button = goog.dom.createDom(goog.dom.TagName.BUTTON,
        greenday.extension.ButtonBuilders.ClassName.MENU_ITEM_CHECKBOX);
    button.title = greenday.extension.ButtonBuilders.Copy.CHECKBOX_ADD;
    button.setAttribute('aria-checked', 'unchecked');
    button.setAttribute('role', 'menuitemcheckbox');
    button.setAttribute('id',
        greenday.extension.ButtonBuilders.DomId.PRE_CHECKBOX + project.id);
    goog.dom.appendChild(li, button);

    var projectLink = goog.dom.createDom('a',
        greenday.extension.ButtonBuilders.ClassName.MENU_ITEM_PROJECT);
    projectLink.setAttribute('href',
        greenday.extension.ButtonBuilders.PROJECT_BASE + project.id);
    projectLink.innerHTML = project.name;
    goog.dom.appendChild(li, projectLink);
    goog.dom.appendChild(menu, li);

    this.checkProjectStatus(project.id, items);
  }, this));
};


/**
 * Setups projects for popup.
 * @param {string} searchTerm
 */
greenday.extension.ButtonBuilders.prototype.setupProjects =
    function(searchTerm) {
  var greendayProjects = this.app_.greendayProjects;
  var menuDiv = goog.dom.createDom(goog.dom.TagName.DIV,
      greenday.extension.ButtonBuilders.ClassName.GREENDAY_MENU);
  menuDiv.setAttribute('id',
      greenday.extension.ButtonBuilders.DomId.GREENDAY_MENU);
  menuDiv.setAttribute('width',
      greenday.extension.ButtonBuilders.PopupSize.WIDTH);

  goog.dom.appendChild(
      goog.dom.getElement(greenday.extension.ButtonBuilders.DomId.POPUP_INNER),
      menuDiv);

  var menu = goog.dom.createElement('ul');
  menu.setAttribute('role', 'menu');
  goog.dom.appendChild(menuDiv, menu);

  // Check which projects already have the video in
  var query = {youtube_id: this.currentVideo_};
  gapi.client.greenday.onesearch.advanced_videos(query).execute(
      goog.bind(function(resp) {
        this.addProjects(greendayProjects, menu, resp.items);
      }, this));

  var createProjectButton = goog.dom.createDom(goog.dom.TagName.BUTTON,
      greenday.extension.ButtonBuilders.ClassName.CREATE_PROJECT);
  goog.dom.setTextContent(createProjectButton,
      greenday.extension.ButtonBuilders.Copy.CREATE_PROJECT);

  this.eventHandler_.listen(createProjectButton, goog.events.EventType.CLICK,
      function(e) {
        window.open(greenday.extension.ButtonBuilders.GREENDAY_BASE, '_blank');
      });
  goog.dom.appendChild(menuDiv, createProjectButton);

  if (greendayProjects.length == 0) {

    var innerPopup = goog.dom.getElement(
        greenday.extension.ButtonBuilders.DomId.POPUP_INNER);
    innerPopup.innerHTML = greenday.extension.ButtonBuilders.NO_PROJECTS;

    var loginButton = goog.dom.createDom(goog.dom.TagName.DIV,
        greenday.extension.ButtonBuilders.ClassName.LOGIN_BUTTON);
    loginButton.innerHTML =
        greenday.extension.ButtonBuilders.Copy.LOGIN_BUTTON_TEXT;
    goog.dom.appendChild(innerPopup, loginButton);
    this.eventHandler_.listen(loginButton, goog.events.EventType.CLICK,
        goog.bind(this.gotoGreenday, this));
  }
};


/**
 * Opens up the greenday homepage.
 */
greenday.extension.ButtonBuilders.prototype.gotoGreenday = function() {
  window.open(greenday.extension.ButtonBuilders.GREENDAY_BASE);
};


/**
 * Listener for when a user clicks outside of the box.
 * @param {!goog.events.Event} e
 * @private
 */
greenday.extension.ButtonBuilders.prototype.closeListener_ = function(e) {
  var shouldCloseExtension = true;
  var theElem = e.target;
  while (theElem != null) {
    if (theElem == goog.dom.getElement(
        greenday.extension.ButtonBuilders.DomId.GREENDAY_POPUP)) {
      shouldCloseExtension = false;
    }
    theElem = theElem.parentNode;
  }
  if (shouldCloseExtension) {
    this.closeExtension();
    this.eventHandler_.unlisten(document, goog.events.EventType.CLICK,
        this.closeListener_);
  }
};


/**
 * Adds current video to the requested project.
 * @param {string} youtubeTime
 * @return {number} time in seconds.
 */
greenday.extension.ButtonBuilders.prototype.getSecondsFromYouTubeTime =
    function(youtubeTime) {
  var total = 0;
  var hours = youtubeTime.match(/(\d+)H/);
  var minutes = youtubeTime.match(/(\d+)M/);
  var seconds = youtubeTime.match(/(\d+)S/);
  if (hours) total += parseInt(hours[1], 10) * 3600;
  if (minutes) total += parseInt(minutes[1], 10) * 60;
  if (seconds) total += parseInt(seconds[1], 10);
  return total;
};


/**
 * Adds current video to the requested project.
 * @param {number} projectId
 */
greenday.extension.ButtonBuilders.prototype.addToProject = function(projectId) {

  var checkboxElement = goog.dom.getElement(
      greenday.extension.ButtonBuilders.DomId.PRE_CHECKBOX + projectId);
  this.loadingCheckbox(checkboxElement);

  var insertionCorpus = {
    youtube_ids: [this.currentVideo_],
    project_id: projectId
  };
  gapi.client.greenday.video.video_batch_create(insertionCorpus).execute(
      goog.bind(function(insertResponse) {
        var videoId = insertResponse.videos[0].id;
        this.enableCheckbox(checkboxElement);
        checkboxElement.setAttribute(
            greenday.extension.ButtonBuilders.Attribute.GREENDAY_ID,
            videoId
        );
      }, this));
};


/**
 * Removes current video from the requested project.
 * @param {number} projectId
 */
greenday.extension.ButtonBuilders.prototype.removeFromProject =
    function(projectId) {
  var checkboxElement = goog.dom.getElement(
      greenday.extension.ButtonBuilders.DomId.PRE_CHECKBOX + projectId);
  this.loadingCheckbox(checkboxElement);
  var id = checkboxElement.getAttribute(
      greenday.extension.ButtonBuilders.Attribute.GREENDAY_ID);
  var removeEntry = {
    project_id: projectId,
    youtube_id: this.currentVideo_
  };
  gapi.client.greenday.video.delete(removeEntry).execute(
      goog.bind(function(resp) {
        this.disableCheckbox(checkboxElement);
      }, this));
};


/**
 * Checks if project has already been added.
 * @param {number} projectId
 * @param {!Array.<!Object>} items Projects which have the current YT video in.
 */
greenday.extension.ButtonBuilders.prototype.checkProjectStatus =
    function(projectId, items) {
  var checkboxElement = goog.dom.getElement(
      greenday.extension.ButtonBuilders.DomId.PRE_CHECKBOX + projectId);
  var found = false;
  var greendayId = 0;
  if (goog.isDefAndNotNull(items)) {
    var element = goog.array.find(items, function(item, index) {
      return item.project_id == projectId;
    });
    if (goog.isDefAndNotNull(element)) {
      greendayId = element.project_id;
    }
  }
  if (greendayId != 0) {
    this.enableCheckbox(checkboxElement);
    checkboxElement.setAttribute(
        greenday.extension.ButtonBuilders.Attribute.GREENDAY_ID, greendayId);
  } else {
    this.disableCheckbox(checkboxElement);
  }
};


/**
 * Enables Checkbox for a project in popup window.
 * @param {Element} elem
 */
greenday.extension.ButtonBuilders.prototype.enableCheckbox = function(elem) {
  elem.setAttribute('aria-checked', 'checked');
  goog.dom.classes.set(elem,
      greenday.extension.ButtonBuilders.ClassName.MENU_ITEM_CHECKBOX);
  goog.dom.classes.add(goog.dom.getParentElement(elem),
      greenday.extension.ButtonBuilders.ClassName.CHECKBOX_SELECTED);
  var projectId = this.getProjectFromElem(elem);
  this.eventHandler_.listenOnce(elem, goog.events.EventType.CLICK,
      function(e) { this.removeFromProject(projectId); });
};


/**
 * Sets Checkbox to loading animation for a project in popup window.
 * @param {Element} elem
 */
greenday.extension.ButtonBuilders.prototype.loadingCheckbox = function(elem) {
  goog.dom.classes.set(elem,
      greenday.extension.ButtonBuilders.ClassName.MENU_ITEM_CHECKBOX + ' ' +
      greenday.extension.ButtonBuilders.ClassName.CHECKBOX_LOADING);
  this.eventHandler_.unlisten(elem, goog.events.EventType.CLICK);
};


/**
 * Disables Checkbox for a project in popup window.
 * @param {Element} elem
 */
greenday.extension.ButtonBuilders.prototype.disableCheckbox = function(elem) {
  elem.setAttribute('aria-checked', '');
  goog.dom.classes.set(elem,
      greenday.extension.ButtonBuilders.ClassName.MENU_ITEM_CHECKBOX);
  goog.dom.classes.remove(goog.dom.getParentElement(elem),
      greenday.extension.ButtonBuilders.ClassName.CHECKBOX_SELECTED);
  var projectId = this.getProjectFromElem(elem);
  this.eventHandler_.listenOnce(elem, goog.events.EventType.CLICK,
      function(e) { this.addToProject(projectId); });
};


/**
 * Returns the ID of the project from a checkbox.
 * @param {Element} elem
 * @return {string}
 */
greenday.extension.ButtonBuilders.prototype.getProjectFromElem =
    function(elem) {
  var projectId = elem.id.substring(
      greenday.extension.ButtonBuilders.DomId.PRE_CHECKBOX.length);
  return projectId;
};


/**
 * Closes Extension.
 */
greenday.extension.ButtonBuilders.prototype.closeExtension = function() {
  goog.dom.removeNode(goog.dom.getElement(
      greenday.extension.ButtonBuilders.DomId.GREENDAY_POPUP));
};


/**
 * Generates buttons over normal thumbails.
 */
greenday.extension.ButtonBuilders.prototype.addNormalPreview = function() {
  var thumbnails = goog.dom.getElementsByClass(
      greenday.extension.ButtonBuilders.ClassName.THUMBNAIL);
  goog.array.forEach(thumbnails, goog.bind(function(thumbnail) {
    var anchor = thumbnail.getElementsByTagName('a')[0];
    if (goog.isDefAndNotNull(anchor)) {
      var checkerButton = goog.dom.getElementByClass(
          greenday.extension.ButtonBuilders.ClassName.BUTTON, thumbnail);
      if (checkerButton != null) {
        return;
      }
      var anchorHref = anchor.href;
      var videoId = anchorHref.substring(anchorHref.indexOf('v=') + 2);
      var button = goog.dom.createDom(goog.dom.TagName.BUTTON,
          greenday.extension.ButtonBuilders.ClassName.BUTTON);
      button.setAttribute('data-tooltip-text',
          greenday.extension.ButtonBuilders.Copy.ADD_TO);
      var icon = goog.dom.createDom(goog.dom.TagName.IMG, {
        src: greenday.extension.ButtonBuilders.GREENDAY_ICON
      });
      goog.dom.appendChild(button, icon);
      goog.dom.appendChild(anchor, button);
      button.onclick = function() { return false; };
      this.eventHandler_.listen(button, goog.events.EventType.CLICK,
          function(buttonEvent) {
            this.showGreendayMenu(
                buttonEvent, thumbnail, videoId);
          });
    } else {
      // TODO(cosborn): Check why.
    }
  }, this));
};

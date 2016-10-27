(function() {
	angular.module('components.popup')
		.factory('popupManager', popupManager);

	/** @ngInject */
	function popupManager(backdropService, popupFactory, POPUP_DEFAULTS) {
		var popups = {};

		var service = {
			show: show,
			hide: hide
		};

		return service;

		/////////////////////
		function create(element, options) {
			var instance = popupFactory.getInstance(element, options);
			popups[instance.id] = instance;

			return instance;
		}

		function show(element, options) {

		}

		function hide() {

		}
	}
}());

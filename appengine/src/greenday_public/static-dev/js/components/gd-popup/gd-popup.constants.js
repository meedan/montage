(function () {
	var POPUP_DEFAULTS = {
		alignEdge: 'top left',
		alignTo: 'bottom left',
		attachTo: $('body'),
		backdrop: 'true',
		gapX: '0',
		gapY: '0',
		position: 'outside',
		zIndex: 2000
	};

	angular.module('components.popup')
		.constant('POPUP_DEFAULTS', POPUP_DEFAULTS);
}());

(function () {
	angular.module('components.popup')
		.directive('gdPopupContent', popupContent);

	/** @ngInject */
	function popupContent($log, $compile, popupFactory, POPUP_DEFAULTS) {
		var directive = {
			restrict: 'E',
			compile: compile,
			require: ['^gdPopup'],
			priority: 10000,
			// templateUrl: 'components/gd-popup/gd-popup-content.template.html',
			terminal: true
		};

		/** @ngInject */
		function controller($scope, $element, $attrs) {
			// Note: It's important that we don't put/alter any properties on
			// the scope this component has access to as this is an inherited
			// scope not private to the popup instance. This is how content
			// within popups is able to access parent scope properties.
			// Assigning scope properties from within this directive means the
			// data assigned will be visible to things other than the popup,
			// and the data will remain on the inherited scope even after the
			// popup is closed.
			$log.debug('<gd-popup-content>:controller');
		}

		function compile(tElement, tAttrs) {
			return link;
		}

		function link(scope, element, attrs, controller, transclude) {
			$log.debug('<gd-popup-content>:postLink');
		}

		return directive;
	}
}());

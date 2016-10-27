(function () {
	angular.module('components.popup')
		.directive('gdPopupElement', popupElement);

	/** @ngInject */
	function popupElement($log) {
		var directive = {
			restrict: 'E',
			// bindToController: true,
			controller: controller,
			controllerAs: 'popupElementCtrl',
			templateUrl: 'components/gd-popup/gd-popup-element.template.html',
			transclude: true,
			link: link,
			scope: false
		};

		/** @ngInject */
		function controller($scope, $element, $attrs) {
			$log.debug('<gd-popup-element>:controller');
			this.name = '<gd-popup-element>';

			this.close = function () {
				$scope._popupInstance.close();
			};

			this.reposition = function () {
				$scope._popupInstance.position();
			};
		}

		function link(scope, element, attrs, ctrl, transclude) {
			$log.debug('<gd-popup-element>:link');
		}

		return directive;
	}
}());

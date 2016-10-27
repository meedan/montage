(function () {
	angular.module('components.popup')
		.directive('gdPopupButton', popupButton);

	/** @ngInject */
	function popupButton($log) {
		var directive = {
			restrict: 'E',
			bindToController: true,
			controller: controller,
			controllerAs: 'popupButtonCtrl',
			link: link,
			require: ['^gdPopup'],
			templateUrl: 'components/gd-popup/gd-popup-button.template.html',
			transclude: true,
			scope: {}
		};

		/** @ngInject */
		function controller($scope, $element, $attrs) {
			$log.debug('<gd-popup-button>:controller');
			this.name = '<gd-popup>';
		}

		function link(scope, element, attrs, ctrl, transclude) {
			var gdPopupCtrl = ctrl[0];

			$log.debug('<gd-popup-button>:link');

			scope.open = function (argument) {
				$log.debug('<gd-popup-button>:scope.open()');
				gdPopupCtrl.open(element);
			};
		}

		return directive;
	}
}());

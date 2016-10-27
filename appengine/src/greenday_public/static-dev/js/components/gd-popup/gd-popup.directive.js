(function () {
	angular.module('components.popup')
		.directive('gdPopup', popup);

	/** @ngInject */
	function popup($log, $compile, popupFactory, POPUP_DEFAULTS) {
		var directive = {
			restrict: 'E',
			bindToController: true,
			controller: controller,
			controllerAs: 'popupCtrl',
			link: link,
			scope: {}
		};

		/** @ngInject */
		function controller($scope, $element, $attrs, POPUP_DEFAULTS) {
			$log.debug('<gd-popup>:controller');

			var ctrl = this;
			var popup;

			ctrl.name = '<gd-popup>';
			ctrl.instance = null;

			ctrl.open = function ($triggerElement) {
				ctrl.$triggerElement = $triggerElement;
				$scope.isOpen = true;
			};
		}

		function link(scope, element, attrs, ctrl, transclude) {
			$log.debug('<gd-popup>:link');

			var $contents = element.find('gd-popup-content').eq(0);
			var linker;
			var options = {};
			var popupInstance;
			var popupScope;
			var promise;
			var template;

			scope.isOpen = false;

			// Proxy options from attributes
			angular.forEach(POPUP_DEFAULTS, function (defValue, option) {
				if (angular.isDefined(attrs[option])) {
					options[option] = attrs[option];
				}
			});

			template = '<gd-popup-element>' + $contents.html() +
				'</gd-popup-element>';

			// Remove the contents of the popup.
			$contents.remove();

			scope.$watch('isOpen', function (isOpen, wasOpen) {
				if (isOpen === true && isOpen !== wasOpen) {
					// Create a new child scope that prototypically inherits
					// from scope.$parent. This is effectively our manual
					// transclusion scope. We create a new scope here instead of
					// just passing scope.$parent because we want to attach
					// some popup specific data which should not be published
					// on scope.$parent.
					popupScope = scope.$parent.$new(false, scope.$parent);

					// Compile the popup template.
					linker = $compile(template);

					// Create a popup instance
					popupInstance = new popupFactory.getInstance(options);

					// Patch the popup instance onto the scope we are going to
					// use to link the <gd-popup-element>.
					popupScope._popupInstance = popupInstance;

					// Now link the popup to the popup scope and set the new
					// element as the element of the popup instance.
					popupInstance.setElement(linker(popupScope));

					// Keep a reference to the instance on our controller.
					ctrl.instance = popupInstance;

					// Open the popup. Ensure that we bind to the resolve/reject
					// of the open promise so that we can clear up necessary
					// stuff once the popup is closed.
					promise = popupInstance.open(ctrl.$triggerElement);
					promise.finally(function () {
						$log.warn('<gd-popup>:promise resolve');
						scope.isOpen = false;

						// Destroy the popup scope.
						popupScope.$destroy();
						ctrl.instance = null;
					});

					popupScope.$on('$destroy', function () {
						$log.warn('$destroy');
					});
				}
			});
		}

		return directive;
	}
}());

(function () {
	angular.module('components.buttons', ['app.services'])
		.directive('gdButton', plainIconButton);

	/** @ngInject */
	function plainIconButton($timeout) {
		var directive = {
			templateUrl: 'components/buttons/gd-button/gd-button.html',
			restrict: 'E',
			scope: {
				async: '&?',
				name: '@?',
				title: '@?',
				type: '@?'
			},
			controller: controller,
			controllerAs: 'ctrl',
			link: link,
			transclude: true
		};

		/** @ngInject **/
		function controller($scope, $element, $attrs) {
			var ctrl = this;
			ctrl.isBusy = false;
			ctrl.isAsync = angular.isDefined($attrs.async);
		}

		function link(scope, element, attrs, ctrl) {
			var $buttonElement = element.find('button').eq(0),
				inProgressClass = 'is-in-progress';

			if (angular.isDefined(scope.name)) {
				$buttonElement.attr('name', scope.name);
			}

			if (angular.isDefined(scope.title)) {
				$buttonElement.attr('title', scope.title);
			}

			if (angular.isDefined(scope.type)) {
				$buttonElement.attr('type', scope.type);
			}

			if (ctrl.isAsync === true) {
				var $wrapperEl = element.find('.gd-button').eq(0);

				$wrapperEl.addClass('gd-button--async');

				ctrl.click = function ($event) {
					// Prevent the callback if an async operation is
					// already in progress.
					if (!ctrl.isBusy) {
						ctrl.isBusy = true;
						$buttonElement.addClass(inProgressClass);

						// FIXME: Support passing $event as
						// per ng-click.
						// See https://github.com/angular/angular.js/blob/e057a9aa398ead209bd6bbf76e22d2d5562904fb/src/ng/directive/ngEventDirs.js#L64
						scope.async().finally(function () {
							ctrl.isBusy = false;
							$buttonElement.removeClass(inProgressClass);
						});
					}
				};
			}
		}

		return directive;
	}
}());

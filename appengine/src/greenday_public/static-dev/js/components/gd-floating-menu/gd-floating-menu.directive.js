(function () {
	angular.module('components')
		.directive('gdFloatingMenu', floatingMenu);

	/** @ngInject */
	function floatingMenu($rootScope, $compile, $timeout, $window, gdFloatingMenuManager) {
		var directive = {
			templateUrl: 'components/gd-floating-menu/gd-floating-menu.html',
			restrict: 'E',
			transclude: true,
			controller: controller,
			controllerAs: 'ctrl',
			link: link,
			scope: {
				'menuId': '@',
				'menuData': '=',
				'menuWidth': '@'
			}
		};

		return directive;

		/** @ngInject */
		function controller($scope, $element, $attrs, $transclude) {
			var ctrl = this;

			$scope.isOpen = false;

			ctrl.hide = function () {
				gdFloatingMenuManager.close($scope.menuId);
			};

			ctrl.getMenuTemplate = function() {
				return $attrs.menuTemplateUrl;
			};
		}

		/** @ngInject */
		function link($scope, $element, $attrs) {
			var	self = this,
				$body = $('body'),
				$button = $('.gd-floating-menu__button'),
				$content = $element.find('.gd-floating-menu__content'),
				$windowEl = angular.element($window);

			$element.addClass('gd-floating-menu md-whiteframe-z1');
			$element.attr('layout', 'horizontal');

			positionMenu($element);

			$windowEl.on('resize.gdFloatingMenu', onWindowResize);
			$scope.$on('$destroy', function() {
				$windowEl.off('resize.gdFloatingMenu', onWindowResize);
			});

			function positionMenu() {
				var menu = gdFloatingMenuManager.lookup($scope.menuId),
					menuPosition = {},
					horizontalOffset,
					triggerElementPosition,
					verticalOffset,
					$offsetParent,
					$parent = menu.config.attachTo,
					$triggerElement = menu.config.triggerElement;

				// If the floating menu is not being positioned at the window
				// level, then we have to change our positioning logic.
				if (angular.isElement(menu.config.attachTo)) {

					// Check if the `attachTo` element is the offset parent.
					$offsetParent = $element.offsetParent();

					// Get the trigger elements position relative to
					// the offsetParent.
					triggerElementPosition = $triggerElement.position();

					if ($offsetParent.get(0) !== $parent.get(0)) {
						// The attach to div is not the offset parent, so
						// we will need to take into account the position of
						// both element and menu.config.attachTo with respect
						// to the offsetParent. For now we just warn because I'm
						// not sure how we'd handle this properly. It's easier
						// if we just make sure the attachTo element
						// is positioned in CSS.
						console.warn(
							'<gd-floating-menu> The element that the ' +
							'floating menu is attached to is not positioned. ' +
							'Calculations may be off.');
					}

					// The attach to div is the offset parent, so all
					// positioning calculations will be relative to the
					// attachTo element.

					if (menu.config.alignTo === 'right') {
						menuPosition.right =
							$offsetParent.outerWidth() -
							triggerElementPosition.left -
							$triggerElement.outerWidth();

						menuPosition.top = triggerElementPosition.top;
					} else {
						menuPosition = triggerElementPosition;
					}

				} else {
					// Set the dropdowns position according to the trigger
					// element's position. In this case we are relative to the
					// window, so offset is used.
					triggerElementPosition = menu.config.triggerElement.offset();

					// If the align-to option is specified, we align the menu
					// as required.
					if (menu.config.alignTo === 'right') {
						menuPosition.right =
							$windowEl.width() -
							triggerElementPosition.left -
							menu.config.triggerElement.width();

						menuPosition.top = triggerElementPosition.top;
					} else {
						menuPosition = triggerElementPosition;
					}
				}

				$element.css(menuPosition);
			}

			function onWindowResize(evnt) {
				positionMenu();
			}
		}
	}
}());

(function () {
	angular.module('components')
		.directive('gdFloatingMenuGroup', floatingMenuGroup);

	/** @ngInject */
	function floatingMenuGroup() {
		var directive = {
			templateUrl: 'components/gd-floating-menu/gd-floating-menu-group.html',
			restrict: 'E',
			compile: compile,
			require: '^gdFloatingMenu',
			transclude: true,
			scope: {
				icon: '@?',
				title: '@',
				menuData: '='
			}
		};

		var positionGroupPopup = function($groupParent, $groupContent) {
			var $window = $(window),
				availableWidth,
				groupContentOffset,
				groupContentWidth,
				groupParentOffset,
				groupParentWidth,
				padding = 50;

			// Ensure the group div has layout and dimensions but
			// remains hidden;
			$groupContent.css({
				'visibility': 'hidden',
				'display': 'block'
			});

			groupContentWidth = $groupContent.width();
			groupParentWidth = $groupParent.width();

			groupContentOffset = $groupContent.offset();
			groupParentOffset = $groupParent.offset();

			availableWidth = $window.width() -
							(groupParentOffset.left + groupParentWidth);

			if (availableWidth > groupContentWidth + padding) {
				$groupContent.removeClass('gd-floating-menu-group__content--left');
				$groupContent.addClass('gd-floating-menu-group__content--right');
			} else {
				$groupContent.removeClass('gd-floating-menu-group__content--right');
				$groupContent.addClass('gd-floating-menu-group__content--left');
			}

			$groupContent.css({
				'visibility': '',
				'display': ''
			});
		};

		/** @ngInject **/
		function compile(tElement, tAttrs) {
			// Dynamically inject menuData from gd-floating-menu element to
			// child scope.
			tElement.attr('menu-data', 'menuData');
			return link;
		}

		/** @ngInject **/
		function link(scope, element, attrs, gdFloatingMenuController) {
			var $groupContent;

			element.addClass('gd-floating-menu-group');

			// Calculate which side to show the group on based on available
			// viewport size.
			$groupContent = element.find('.gd-floating-menu-group__content');

			element.on('mouseenter', onMouseEnter);
			element.on('mouseleave', onMouseLeave);

			function onMouseEnter() {
				positionGroupPopup(element, $groupContent);
				$groupContent.show();
			}

			function onMouseLeave() {
				$groupContent.hide();
			}
		}

		return directive;
	}
}());

(function () {
	angular.module('components')
		.directive('gdFloatingMenuItem', floatingMenuItem);

	/** @ngInject */
	function floatingMenuItem() {
		var directive = {
			templateUrl: 'components/gd-floating-menu/gd-floating-menu-item.html',
			restrict: 'E',
			link: link,
			require: '^gdFloatingMenu',
			transclude: true,
			scope: {
				icon: '@?',
				menuData: '=',
				hideOnClick: '@?'
			}
		};

		/** @ngInject **/
		function link(scope, element, attrs, gdFloatingMenuController) {
			element.addClass('gd-floating-menu-item');

			function onItemClicked() {
				gdFloatingMenuController.hide();
			}

			if (!attrs.hideOnClick || attrs.hideOnClick !== 'false') {
				element.on('click', onItemClicked);
			}

			scope.$on('$destroy', function () {
				element.off('click', onItemClicked);
			});
		}

		return directive;
	}
}());

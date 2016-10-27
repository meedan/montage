(function () {
	angular.module('components')
		.directive('gdFloatingMenuButton', floatingMenuButton);

	/** @ngInject */
	function floatingMenuButton(gdFloatingMenuService) {
		var directive = {
			templateUrl: 'components/gd-floating-menu/gd-floating-menu-button.html',
			restrict: 'E',
			transclude: true,
			link: link,
			require: '?^gdBackdropRoot',
			scope: {
				alignTo: '@?',
				attachTo: '=?',
				menuTemplateUrl: '@',
				menuData: '=',
				menuWidth: '@?',
				menuZIndex: '@?'
			}
		};

		return directive;

		/** @ngInject */
		function link(scope, element, attrs, backdropRootCtrl) {
			var ctrl = this,
				backdropRoot,
				defaults,
				options;

			defaults = {
				alignTo: 'left',
				attachTo: 'body'
			};

			if (backdropRootCtrl) {
				defaults.backdropRoot = backdropRootCtrl.element;
			}

			element.addClass('gd-floating-menu-button');
			element.attr('layout', 'horizontal');
			element.attr('layout-align', 'center');

			options = angular.extend({}, defaults, {
				alignTo: scope.alignTo,
				attachTo: scope.attachTo,
				button: element,
				scope: scope,
				menuTemplateUrl: scope.menuTemplateUrl,
				menuWidth: scope.menuWidth || '3x',
				menuZIndex: parseInt(scope.menuZIndex, 10) || 1500,
				triggerElement: element
			});

			scope.show = function() {
				gdFloatingMenuService.open(options);
			};
		}
	}
}());

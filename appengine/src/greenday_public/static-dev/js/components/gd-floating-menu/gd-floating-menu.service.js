(function() {
	angular.module('components')
		.factory('gdFloatingMenuService', menuProvider);

	/** @ngInject */
	function menuProvider($document, $rootScope, $q, $http, $templateCache, gdFloatingMenuManager) {
		var menu = {};

		function getTemplatePromise(options) {
			return options.menuTemplate ? $q.when(options.menuTemplate) :
				$http.get(angular.isFunction(options.menuTemplateUrl) ? (options.menuTemplateUrl)() : options.menuTemplateUrl, {
					cache: $templateCache
				}).then(function(result) {
					return result.data;
				});
		}

		menu.open = function(menuOptions) {
			var body = $document.find('body').eq(0),
				menuInstance,
				templatePromise;

			if (!menuOptions.menuTemplate && !menuOptions.menuTemplateUrl) {
				throw new Error('One of template or templateUrl options is required.');
			}

			// FIXME: Do we need this?
			menuInstance = {
				close: function(result) {}
			};

			templatePromise = getTemplatePromise(menuOptions).then(function (contentTemplate) {
				var scopeToUse = menuOptions.scope || $rootScope,
					menuScope = scopeToUse.$new();

				menuScope.$close = menuInstance.close;

				gdFloatingMenuManager.open(menuInstance, {
					content: contentTemplate,
					scope: menuScope,
					alignTo: menuOptions.alignTo,
					attachTo: menuOptions.attachTo,
					backdropRoot: menuOptions.backdropRoot,
					button: menuOptions.button,
					menuTemplateUrl: menuOptions.menuTemplateUrl,
					menuWidth: menuOptions.menuWidth,
					menuZIndex: menuOptions.menuZIndex,
					triggerElement: menuOptions.triggerElement
				});
			});

			return menuInstance;
		};

		return menu;
	}
}());

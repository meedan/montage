(function() {
	angular.module('components')
		.factory('gdFloatingMenuManager', menuManagerProvider);

	/** @ngInject */
	function menuManagerProvider(_, $compile, $document, $rootScope, backdropService) {
		var menuManager = {};
		var backdrop = null;
		var currentMenuId = null;
		var registry = {};

		menuManager.register = function(id, node, backdrop, menuInstance, config) {
			registry[id] = {
				element: node,
				backdrop: backdrop,
				config: config,
				menuInstance: menuInstance
			};
		};

		menuManager.unregister = function(id) {
			delete registry[id];
		};

		menuManager.lookup = function (menuId) {
			return registry[menuId];
		};

		menuManager.open = function(menuInstance, menuOptions) {
			var backdrop,
				menuId = _.uniqueId('menu-'),
				$compiledMenu,
				$menuDomEl;

			// Create the backdrop
			backdrop = backdropService.add({
				attachTo: menuOptions.backdropRoot,
				zIndex: menuOptions.menuZIndex - 1
			});

			// Close this menu when the backdrop promise is resolve (i.e. it is
			// clicked).
			backdrop.promise.then(function () {
				menuManager.close();
			});

			// Compile the floating menu template.
			$menuDomEl = angular.element([
				'<gd-floating-menu ',
					'menu-template-url="' + menuOptions.menuTemplateUrl + '" ',
					'menu-id="' + menuId + '"',
					'menu-data="menuData" ',
					'menu-width="' + menuOptions.menuWidth + '"',
				'></gd-floating-menu>'
				].join(''));

			// Link the template with the provided scope.
			$compiledMenu = $compile($menuDomEl)(menuOptions.scope);

			// Set the z-index
			$compiledMenu.css('z-index', menuOptions.menuZIndex);

			// Add the new floating menu to our register of menus.
			menuManager.register(menuId, $compiledMenu, backdrop, menuInstance, menuOptions);

			// Attach the floating menu to the correct part of the DOM.
			if (angular.isElement(menuOptions.attachTo)) {
				menuOptions.attachTo.append($compiledMenu);
			} else {
				$document.find('body').eq(0).append($compiledMenu);
			}

			// Store a reference to the current menu id so we can close it.
			currentMenuId = menuId;
		};

		menuManager.close = function() {
			var menu;

			if (currentMenuId) {
				// Obtain the active menu's configuration data from the
				// menu manager service so we can remove it's element.
				menu = menuManager.lookup(currentMenuId);

				// Menus will always have their own scope, so destroy it.
				menu.config.scope.$destroy();

				// Remove the menu element from the DOM.
				menu.element.remove();

				// Remove the backdrop.
				backdropService.remove(menu.backdrop.id);

				// Forget all about this menu element.
				menuManager.unregister(currentMenuId);
			} else {
				throw 'Cannot close menu. No menu is open';
			}
		};

		return menuManager;
	}
}());

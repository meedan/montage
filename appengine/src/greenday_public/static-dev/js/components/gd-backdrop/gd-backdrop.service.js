(function() {
	angular.module('components.backdrop')
		.factory('backdropService', backdropService);

	/** @ngInject */
	function backdropService(_, $document, $compile, $rootScope, $q, BACKDROP_DEFAULTS) {
		var backdropStack = {};

		var service = {
			add: add,
			getById: getById,
			remove: remove
		};

		return service;

		//////////////////

		function add(options) {
			var attachTarget,
				backdrop;

			options = angular.extend({}, BACKDROP_DEFAULTS, options);

			// Create the backdrop and register it in the stack.
			backdrop = new Backdrop(options);
			backdropStack[backdrop.id] = backdrop;

			if (options.attachTo) {
				attachTarget = options.attachTo;
			} else {
				attachTarget = $document.find('body');
			}

			// Append the backdrop to the page.
			attachTarget.append(backdrop.element);

			return backdrop;
		}

		/**
		 * Removes the backdrop from the DOM, and optionally resolves the
		 * Backdrops promise if the `resolve` parameter is true.
		 *
		 * @param  {String} id
		 *         The id of the backdrop to remove.
		 *
		 * @param  {Boolean} resolve
		 *         If true, the backdrops promise will be resolved. Otherwise
		 *         it will be rejected.
		 *
		 * @return {Undefined}
		 */
		function remove(id, resolve) {
			var backdrop = backdropStack[id];

			if (!angular.isDefined(resolve)) {
				resolve = false;
			}

			if (!angular.isDefined(id)) {
				throw new TypeError('No id passed to Backdrop.close()');
			}

			// If there is no backdrop with the provided ID, it's either already
			// been closed or it never existed, so we don't need to do anything.
			if (!angular.isDefined(backdrop)) {
				return;
			}

			// Remove the backdrop from the DOM and destroy the manually
			// created backdrop scope.
			backdrop.scope.$destroy();
			backdrop.element.remove();

			if (resolve) {
				backdrop._dfd.resolve();
			} else {
				backdrop._dfd.reject();
			}

			delete backdropStack[backdrop.id];
		}

		function getById(id) {
			return backdropStack[id];
		}

		function onBackdropClick(id) {
			// Call remove with resolve set to true. The backdrops promise will
			// be resolved and any .then() handlers attached by other
			// components to the backdrop will be run. This gives them a chance
			// to perform actions when the backdrop is closed, like cleaning up
			// their own component (as per floating menus).
			remove(id, true);
		}

		function Backdrop(options) {
			var id = _.uniqueId('backdrop-'),
				html = '<gd-backdrop callback="close(\'' + id + '\')"></gd-backdrop>',
				el = angular.element(html);

			this.id = id;
			this.options = options;
			this.scope = $rootScope.$new(true);

			// We manually pass through the close method to the backdrop scope
			// so that the gd-backdrop directive can call it when it's clicked.
			this.scope.close = onBackdropClick;

			// Keep a reference to the backdrops element so we can remove
			// it later.
			this.element = $compile(el)(this.scope);

			this._dfd = $q.defer();
			this.promise = this._dfd.promise;

			// Setup backdrop zIndex
			if (angular.isDefined(options.zIndex)) {
				this.element.css('zIndex', options.zIndex);
			}
		}
	}
}());

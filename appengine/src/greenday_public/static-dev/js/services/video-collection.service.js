/**
 * Video Collection service
 *
 */
(function () {
	angular
		.module('app.services')
		.factory('VideoCollection', VideoCollection);

	/** @ngInject */
	function VideoCollection($q, $timeout, VideoModel, FilterUtils) {
		var collections = {},
			service = {
				get: get
			};

		function get(filters) {
			var cacheKey = FilterUtils.generateCacheKeyFromFilters(filters);

			if (!collections[cacheKey]) {
				collections[cacheKey] = new Collection(cacheKey, filters);
			}
			return collections[cacheKey];
		}

		var Collection = function (cacheKey, filters) {
			this.cacheKey = cacheKey;
			this.filters = filters;
			this.items = [];
			this.isBusy = false;
			this.pristine = true;

			return this;
		};

		Collection.prototype.findAll = function(options) {
			var self = this,
				opts = angular.extend({bypassCache: true}, options || {}),
				fetchPromise = VideoModel.findAll(self.filters, opts),
				dfd = $q.defer();

			self.isBusy = true;

			fetchPromise
				.then(function (videos) {
					self.setItems(videos);
					dfd.resolve(self.items);
				}, function (response) {
					dfd.reject(response);
				})
				.finally(function () {
					self.isBusy = false;
					self.pristine = false;
				});

			return dfd.promise;
		};

		Collection.prototype.setItems = function (items) {
			var self = this;

			while (self.items.length) {
				self.items.pop();
			}

			angular.forEach(items, function (item) {
				self.items.push(item);
			});
		};

		return service;
	}
}());

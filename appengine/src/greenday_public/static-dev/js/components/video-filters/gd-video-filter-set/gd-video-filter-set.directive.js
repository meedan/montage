(function () {
	angular.module('components')
		.directive('gdVideoFilterSet', videoFilterSet);

	/** @ngInject */
	function videoFilterSet($rootScope, $location, $timeout, VideoModel, VideoCollection, PageService, FilterUtils) {
		var directive = {
				templateUrl: 'components/video-filters/gd-video-filter-set/gd-video-filter-set.html',
				restrict: 'E',
				scope: {
					ngModel: '=',
					onUpdate: '&',
					autoFetch: '=',
					project: '=?',
					collection: '=?',
					config: '=?'
				},
				link: link,
				controller: controller,
				controllerAs: 'ctrl',
				require: ['^gdVideoFilterSet']
			},
			defaultMeta = {
				isOpen: false
			},
			filtersMeta = {
				q: angular.copy(defaultMeta),
				tag_ids: angular.copy(defaultMeta),
				date: angular.copy(defaultMeta),
				location: angular.copy(defaultMeta),
				channel_ids: angular.copy(defaultMeta)
			},
			defaultDisplayConfig = {
				keyword: true,
				tag: true,
				date: true,
				location: true,
				channel: true
			};

		return directive;

		function link(scope, element, attrs, controllers) {
			var ctrl = controllers[0];
			scope.$watchCollection('ngModel.filters', ctrl.update);
			scope.displayConfig = angular.copy(defaultDisplayConfig);
			if (angular.isDefined(scope.config)) {
				angular.extend(scope.displayConfig, scope.config);
			}
		}

		function controller($scope) {
			var ctrl = this,
				pageData = PageService.getPageData();

			ctrl.projectId = $scope.project ? $scope.project.id : null;
			ctrl.collectionId = $scope.collection ? $scope.collection.id : null;
			ctrl.debounce = 500;

			var buildUrl = function () {
				var params = [],
					qs = $location.search();

				angular.forEach(qs, function (value, key) {
					params.push(key + '=' + value);
				});

				if (ctrl.collectionId) {
					params.push('collectionId=' + ctrl.collectionId);
				}

				if (params.length) {
					return '?' + params.join('&');
				}

				return '';
			};

			$scope.$on('$routeUpdate', function () {
				ctrl.updateTheaterUrls();
			});

			ctrl.updateTheaterUrls = function () {
				var qs = buildUrl(),
					collection = ctrl.getCollection();

				if (collection) {
					angular.forEach(collection.items, function (video) {
						video.theatre_url = video.c_theatre_url + qs;
					});
				}
			};

			ctrl.getCollection = function () {
				var cleanedFilters = FilterUtils.cleanFilters($scope.ngModel.filters),
					filtersToApply = {
						project_id: ctrl.projectId,
						archived_at: null
					},
					filterObj = angular.extend({}, cleanedFilters),
					collection;

				if (ctrl.collectionId) {
					filtersToApply.collection_id = ctrl.collectionId;
				}

				if ($scope.ngModel.archived === true) {
					filtersToApply.archived = true;
					filtersToApply.archived_at = '!null';
				}

				angular.extend(filterObj, filtersToApply);

				collection = VideoCollection.get(filterObj);

				PageService.updatePageData({
					videos: collection
				}, true);

				return collection;
			};

			ctrl.fetchVideos = function () {
				var collection = ctrl.getCollection();

				$scope.ngModel.videos = collection.items;

				if (collection.pristine === true) {
					// Fethching for the very first time for this collection
					$rootScope.$broadcast('filterSet::fetch::start');
				} else {
					$rootScope.$broadcast('filterSet::background-fetch::start');
				}

				$timeout(function () {
					collection
						.findAll()
						.then(function () {
							ctrl.updateTheaterUrls();
						})
						.finally(function () {
							$rootScope.$broadcast('filterSet::fetch::end');
							$rootScope.$broadcast('filterSet::background-fetch::end');
						});
				});
			};

			ctrl.fetchTags = function () {
				$rootScope.$broadcast('filterSet::fetch::start');

				var cleanedFilters = FilterUtils.cleanFilters($scope.ngModel.filters),
					filterObj = {
						archived: $scope.ngModel.archived,
						project_id: ctrl.projectId
					};

				angular.extend(filterObj, cleanedFilters);

				if (ctrl.collectionId) {
					filterObj.collection_id = ctrl.collectionId;
				}

				VideoModel
					.fetchTagList({params: filterObj})
					.then(function (data) {
						$scope.ngModel.tags = data.data.items;
					})
					.finally(function () {
						$rootScope.$broadcast('filterSet::fetch::end');
					});
			};

			ctrl.update = function (filters, oldFilters) {
				if (!angular.equals(filters, oldFilters)) {
					$scope.onUpdate();
				}
			};

			ctrl.forceUpdate = function () {
				$scope.onUpdate();
			};

			ctrl.fetch = function() {
				ctrl.fetchVideos();
				ctrl.fetchTags();
			};

			ctrl.setFilters = function(filters, archived) {
				$scope.ngModel.archived = archived;
				angular.forEach(filters, function (filterValue, filterKey) {
					$scope.ngModel.filters[filterKey] = filterValue;
				});

				if ($scope.autoFetch !== false) {
					ctrl.fetch();
				}
			};

			$scope.ngModel.forceUpdate = ctrl.forceUpdate;
			$scope.ngModel.update = ctrl.update;
			$scope.ngModel.setFilters = ctrl.setFilters;
			$scope.ngModel.fetch = ctrl.fetch;
			$scope.ngModel.fetchTags = ctrl.fetchTags;
			$scope.ngModel.fetchVideos = ctrl.fetchVideos;
			$scope.filtersMeta = filtersMeta;
		}

	}
}());

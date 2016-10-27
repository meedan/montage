(function () {
	angular.module('components')
		.directive('oneSearch', oneSearch);

	/** @ngInject */
	function oneSearch($timeout, $q, $location, $log, $window, OneSearchService, ToastService, _, FilterUtils, OneSearchVideoModel) {
		var directive = {
			templateUrl: 'components/one-search/one-search.html',
			restrict: 'E',
			scope: {
				ngModel: '=',
				searching: '=',
				selectedProject: '=?',
				selectedCollection: '=?'
			},
			link: link,
			require: ['^oneSearch'],
			controller: controller,
			controllerAs: 'ctrl'
		};

		return directive;

		function link(scope, element, attrs, controllers) {
			var oneSearchCtrl = controllers[0],
				$searchBox = element.find('.one-search__input').get(0);

			oneSearchCtrl.$listContainer = element.find('.video-list').eq(0);

			scope.$watch('searching', function (isSearching, wasSearching) {
				if (isSearching === true) {
					// Grab the initial query string so we can put it back when we are done.
					oneSearchCtrl.initialQs = angular.copy($location.search());
					$timeout(function () {
						$searchBox.focus();
					});
				}
			});

			$timeout(function () {
				$searchBox.focus();
			});

			scope.$watch('ctrl.filterSet.filters.q', function(q, oldQ) {
				if (q !== oldQ) {
					oneSearchCtrl.onFilterSetUpdate(oneSearchCtrl.filterSet);
				}
			});

			scope.$watch('selectedProject', function () {
				oneSearchCtrl.selectedProject = scope.selectedProject;
			});

			scope.$watch('selectedCollection', function () {
				oneSearchCtrl.selectedCollection = scope.selectedCollection;
			});

			scope.$on('$routeChangeSuccess', function () {
				if (scope.searching === true) {
					scope.searching = false;
				}
			});

			scope.$on('project:videosUpdated', function (event, projectId, videos) {
				if (scope.searching === true && scope.selectedProject.id === projectId) {
					OneSearchVideoModel.inject(videos);
				}
			});

			scope.$on('collection:videosUpdated', function (event, projectId, collectionId, videos) {
				if (scope.searching === true && scope.selectedProject.id === projectId && scope.selectedCollection.id === collectionId) {
					OneSearchVideoModel.inject(videos);
				}
			});

			scope.$on('$routeUpdate', oneSearchCtrl.onRouteUpdate);
		}

		/** @ngInject */
		function controller($scope) {
			var ctrl = this;

			ctrl.initialQs = null;

			ctrl.filterSet = {
				filters: {},
				videos: []
			};
			ctrl.filterConfig = {
				tag: false,
				keyword: false,
				channel: false
			};

			ctrl.currentFilter = null;

			ctrl.videoListOptions = {
				trackBy: 'youtube_id',
				showStats: false,
				bottomSheetActions: {
					addTo: true,
					batchTag: false,
					markAsDuplicate: false,
					archive: false
				}
			};

			ctrl.closeSearch = function () {
				if (ctrl.initialQs) {
					delete ctrl.initialQs.searchVisible;
					$location.search(ctrl.initialQs);
				}
				$scope.searching = false;
			};

			ctrl.onFilterSetUpdate = function (filterSet) {
				$log.debug('onesearch.controller:onFilterSetUpdate');
				var filters = FilterUtils.getB64FilterUrl(ctrl.filterSet.filters),
					qs = $location.search();

				if (!_.isEmpty(ctrl.filterSet.filters)) {
					qs.search = filters;
					ctrl.isFiltering = true;
				} else {
					ctrl.isFiltering = false;
					delete qs.search;
				}

				$location.search(qs);
			};

			ctrl.reset = function () {
				ctrl.searchResults = [];
				ctrl.loading = false;
				ctrl.filterSet.filters = {};
				ctrl.isFiltering = false;
				if (ctrl.initialQs) {
					delete ctrl.initialQs.search;
				}
			};

			ctrl.searchError = function (response) {
				ctrl.searchResults = [];
				ctrl.loading = false;
				ToastService.showError('Error: ' + response.data.error.message, 0);
			};

			ctrl.onRouteUpdate = function () {
				$log.debug('onesearch.controller:onRouteUpdate');
				var qs = $location.search(),
					filter = FilterUtils.urlToObj(qs.search),
					filters = FilterUtils.cleanFilters(filter);

				if (qs.search !== ctrl.currentFilter) {
					ctrl.currentFilter = qs.search;
					ctrl.filterSet.setFilters(filter);
					ctrl.loading = true;
					if (_.values(filters).length) {
						OneSearchService
							.doSearch(filters)
							.then(function (results) {
								ctrl.searchResults = results;
								ctrl.$listContainer.scrollTop(0);
								ctrl.loading = false;
								ctrl.hasMoreResults = !!OneSearchService.ytNextPageToken;
							}, ctrl.searchError);
					} else {
						ctrl.reset();
					}
				}
			};

			ctrl.loadMore = function () {
				var qs = $location.search(),
					filter = FilterUtils.urlToObj(qs.search),
					filters = FilterUtils.cleanFilters(filter);

				ctrl.loading = true;

				OneSearchService
					.doSearch(filters, true)
					.then(function (results) {
						ctrl.searchResults = results;
						ctrl.loading = false;
						ctrl.hasMoreResults = !!OneSearchService.ytNextPageToken;
					}, ctrl.searchError);
			};

			$timeout(ctrl.onRouteUpdate);
		}
	}
}());

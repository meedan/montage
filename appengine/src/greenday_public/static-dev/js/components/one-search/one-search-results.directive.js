(function () {
	angular.module('components')
		.directive('oneSearchResults', oneSearchResults);

	/** @ngInject */
	function oneSearchResults($rootScope, $filter, _, PageService, ProjectModel, CollectionModel, ToastService) {
		var directive = {
			templateUrl: 'components/one-search/one-search-results.html',
			restrict: 'E',
			scope: {
				options: '=',
				videos: '=',
				viewMode: '=',
				filtering: '=',
				selectedProject: '=?',
				selectedCollection: '=?',
				hasMoreResults: '=',
				onLoadMoreClick: '&'
			},
			link: link,
			controller: controller,
			controllerAs: 'ctrl',
			require: ['^oneSearchResults']
		};

		return directive;

		function link(scope, element, attrs, controllers) {
			var oneSearchResultsCtrl = controllers[0];

			scope.$watch('selectedProject', function () {
				oneSearchResultsCtrl.selectedProject = scope.selectedProject;
			});

			scope.$watch('selectedCollection', function () {
				oneSearchResultsCtrl.selectedCollection = scope.selectedCollection;
			});
		}

		function controller($scope, $element, $attrs) {
			var ctrl = this;

			ctrl.selectedVideos = [];
			ctrl.allSelected = false;
			ctrl.orderBy = $filter('orderBy');

			ctrl.ordering = {
				defaultKey: 'order',
				defaultReverse: false,
				currentKey: 'order',
				reverse: false
			};

			$scope.$watchCollection('videos', function (newVideos, oldVideos) {
				updateSelectedVideos();
			});

			$scope.$on('video:selectedChange', updateSelectedVideos);

			ctrl.onloadMoreClick = function () {
				$scope.onLoadMoreClick();
			};

			ctrl.selectAllVideos = function (selected) {
				angular.forEach($scope.videos, function (video) {
					video.selected = selected;
				});

				ctrl.allSelected = selected;
				updateSelectedVideos();
			};

			ctrl.addAll = function () {
				var projectId = $scope.selectedProject.id,
					project = ProjectModel.get(projectId),
					collectionId = $scope.selectedCollection ? $scope.selectedCollection.id : null,
					collection = collectionId ? CollectionModel.get(collectionId) : null;

				var ytVideoIds = _.pluck(ctrl.selectedVideos, 'youtube_id');

				ToastService.show("Adding videos", true);
				PageService.startLoading();
				project
					.addVideos(ytVideoIds)
					.then(function (projectResult) {
						if (collection) {
							ytVideoIds = _.pluck(projectResult.videos, 'youtube_id');

							collection
								.addVideos(ytVideoIds)
								.then(function (collectionResult) {
									var videos = collectionResult.videos;
									$rootScope.$broadcast('collection:videosUpdated', projectId, collectionId, videos);
									ToastService.show("Videos added", true);
								}, function (response) {
									ToastService.showError('Error: ' + response.data.error.message, 0);
								})
								.finally(function () {
									PageService.stopLoading();
								});
						}
						else {
							$rootScope.$broadcast('project:videosUpdated', projectId, projectResult.videos);
							ToastService.show("Videos added", true);
							PageService.stopLoading();
						}
					}, function(response) {
						ToastService.showError("Error adding videos: " + response.data.error.message, 0);
						PageService.stopLoading();
					});
			};

			ctrl.sort = function (predicate) {
				if (ctrl.ordering.currentKey === predicate) {
					if (ctrl.ordering.reverse !== ctrl.ordering.defaultReverse) {
						ctrl.ordering.currentKey = ctrl.ordering.defaultKey;
						ctrl.ordering.reverse = ctrl.ordering.defaultReverse;
					} else {
						ctrl.ordering.reverse = !ctrl.ordering.reverse;
					}
				} else {
					ctrl.ordering.currentKey = predicate;
					ctrl.ordering.reverse = ctrl.ordering.defaultReverse;
				}
			};

			function updateSelectedVideos() {
				ctrl.selectedVideos = _.filter($scope.videos, {selected: true});
			}
		}
	}
}());

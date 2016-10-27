(function () {
	angular.module('components')
		.directive('gdVideoAdder', gdVideoAdder);

	/** @ngInject */
	function gdVideoAdder($rootScope, ProjectModel, CollectionModel, ToastService, _) {
		var directive = {
			restrict: 'E',
			templateUrl: 'components/gd-video-adder/gd-video-adder.html',
			link: link,
			controller: controller,
			controllerAs: 'ctrl',
			require: ['^gdVideoAdder'],
			scope: {
				ngModel: '=',
				isVisible: '=',
				videos: '=',
				resetWhen: '=',
				project: '=?selectedProject',
				collection: '=?selectedCollection'
			}
		};

		return directive;

		function link(scope, element, attrs, controllers) {
			var ctrl = controllers[0];

			scope.$watch('project', function (project) {
				if (project && project !== ctrl.selectedProject) {
					ctrl.selectedProject = project;
					if (!ctrl.selectedCollection) {
						ctrl.selectedCollection = 'library';
					}
				}
			});

			scope.$watch('collection', function (collection) {
				if (collection) {
					ctrl.selectedCollection = collection;
				}
			});

			scope.$watch('resetWhen', function (isReset) {
				if (isReset === true) {
					ctrl.reset();
					ctrl.results = [];
				}
			});
		}

		function controller($scope) {
			var ctrl = this;

			ctrl.addVideos = addVideos;
			ctrl.reset = reset;

			function addVideos(videos) {
				var projectId = ctrl.selectedProject.id,
					project = ProjectModel.get(projectId),
					collectionId = ctrl.selectedCollection.id || null,
					collection = collectionId ? CollectionModel.get(collectionId) : null;

				ctrl.addingVideos = true;

				var ytVideoIds = _.pluck(videos, 'youtube_id');

				project
					.addVideos(ytVideoIds)
					.then(function (projectResult) {

						if (ctrl.selectedCollection === 'library') {
							$rootScope.$broadcast('project:videosUpdated', projectId, projectResult.videos);

							showResults(projectResult);
							ctrl.addingVideos = false;
						} else {
							ytVideoIds = _.pluck(projectResult.videos, 'youtube_id');

							collection
								.addVideos(ytVideoIds)
								.then(function (collectionResult) {
									var videos = collectionResult.videos;
									$rootScope.$broadcast('collection:videosUpdated', projectId, collectionId, videos);

									showResults(collectionResult);
								}, function (response) {
									ToastService.showError('Error: ' + response.data.error.message, 0);
								})
								.finally(function () {
									ctrl.addingVideos = false;
								});
						}
					}, function (response) {
						ToastService.showError('Error: ' + response.data.error.message, 0);
						ctrl.addingVideos = false;
					});
			}

			function showResults(result) {
				var results = [];

				angular.forEach(result.videos, function (video, index) {
					var item = result.items[index];
					item.video = video;
					results.push(item);
				});
				ctrl.results = results;
				ctrl.reset();
			}

			function reset() {
				if (ctrl.selectedCollection) {
					ctrl.selectedCollection = null;
				}
			}
		}
	}
}());

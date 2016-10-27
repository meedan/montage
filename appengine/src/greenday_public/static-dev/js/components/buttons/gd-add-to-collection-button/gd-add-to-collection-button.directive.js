(function () {
	angular.module('components.buttons')
		.directive('gdAddToCollectionButton', addToCollectionButton);

	/** @ngInject */
	function addToCollectionButton($q, $rootScope, ToastService, _) {
		var directive = {
			templateUrl: 'components/buttons/gd-add-to-collection-button/gd-add-to-collection-button.html',
			restrict: 'E',
			scope: {
				video: '=',
				project: '=',
				collection: '=?'
			},
			controller: controller,
			controllerAs: 'ctrl'
		};

		return directive;

		/** @ngInject **/
		function controller($scope) {
			var ctrl = this;

			ctrl.addToCollection = function addToCollection() {
				var addToDeferred = $q.defer(),
					projectPromise,
					collectionPromise,
					toastMsg;

				ctrl.isBusy = true;

				projectPromise = $scope.project.addVideos($scope.video.youtube_id);

				projectPromise
					.then(function (projectResult) {
						if (!$scope.collection) {
							$rootScope.$broadcast('project:videosUpdated', $scope.project.id, projectResult.videos);
							ctrl.isBusy = false;
							addToDeferred.resolve(projectResult.videos);
							ToastService.show('Video added to ' + $scope.project.name);
						} else {
							var youtubeIds = _.pluck(projectResult.videos, 'youtube_id');

							$scope.collection
								.addVideos(youtubeIds)
								.then(function (collectionResult) {
									var videos = collectionResult.videos;
									$rootScope.$broadcast('collection:videosUpdated', $scope.project.id, $scope.collection.id, videos);
									addToDeferred.resolve(collectionResult.videos);
									ToastService.show('Video added to ' + $scope.collection.name);
								}, function (response) {
									ToastService.showError(response, 0);
								})
								.finally(function () {
									ctrl.isBusy = false;
								});
						}
				});

				return addToDeferred.promise;
			};
		}
	}
}());

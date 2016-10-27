/**
 * The video theater module.
 */
(function () {
	angular
		.module('pages.video')
		.controller('RemoveVideoDialogCtrl', dialogCtrl);

	/** @ngInject */
	function dialogCtrl($scope, video, $location, $mdDialog, $routeParams, PageService, VideoModel, ProjectModel) {
		var ctrl = this;
		ctrl.video = video;
		ctrl.collectionId = $routeParams.collectionId ? $routeParams.collectionId : null;

		/////////////////
		// Scope API
		/////////////////
		$scope.remove = remove;
		$scope.cancel = cancel;
		$scope.collectionId = ctrl.collectionId;

		/////////////////
		// Controller API
		/////////////////

		function cancel() {
			$mdDialog.hide();
		}

		function remove() {
			if(ctrl.collectionId) {
				var collection = PageService.getPageData().videos;
				collection
					.deleteVideos([ctrl.video.youtube_id], ctrl.collectionId)
					.then(function() {
						$mdDialog.hide();
						$location.url('/project/' + ctrl.video.project_id + '/collection/' + ctrl.collectionId);
				});
			} else {
				VideoModel
					.destroy(ctrl.video.c_id)
					.then(function() {
						$mdDialog.hide();
						// Update the project meta so we can get the correct video_count
						ProjectModel.refresh(ctrl.video.project_id);
						$location.url('/project/' + ctrl.video.project_id);
				});
			}
		}
	}
}());

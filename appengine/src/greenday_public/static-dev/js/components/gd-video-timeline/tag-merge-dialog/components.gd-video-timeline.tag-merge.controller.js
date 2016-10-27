/**
 * The video theater module.
 */
(function () {
	angular
		.module('components.videoTimeline')
		.controller('TagMergeDialogCtrl', TagMergeDialogCtrl);

	/** @ngInject */
	function TagMergeDialogCtrl(_, $q, $scope, $mdDialog, ToastService,
		ProjectTagModel, VideoTagModel, projectId, video, mergingFromTag, mergingToTagId) {

		var ctrl = this;

		/////////////////
		// Scope API
		/////////////////
		$scope.saving = false;

		/////////////////
		// Controller API
		/////////////////
		ctrl.mergeTags = mergeTags;
		ctrl.cancel = cancel;

		/////////////////
		// Scope Events
		/////////////////
		$scope.$on('pagedata:changed', function () {
			cancel();
		});

		/////////////////
		// Scope/Controller function implementations
		/////////////////

		/**
		 * Callback for the Cancel button of the dialog. Simply closes
		 * the dialog.
		 */
		function cancel() {
			$mdDialog.cancel();
		}

		function mergeTags() {
			var merge;

			$scope.saving = true;

			merge = ProjectTagModel.merge({
				data: {
					'merging_from_tag_id': mergingFromTag.project_tag.global_tag_id,
					'merging_into_tag_id': mergingToTagId
				}
			});

			merge.then(function (response) {
				var mergingToTag = VideoTagModel.filter({ project_tag_id: mergingToTagId})[0];
				$mdDialog.hide();
				ProjectTagModel.eject(mergingFromTag.project_tag_id);
				VideoTagModel.eject(mergingFromTag.id);
				VideoTagModel.find(mergingToTag.id, {bypassCache: true});
			}, function (response) {
				ToastService.showError('Error: ' + response.data.error.message, 0);
			});

			merge.finally(function () {
				$scope.saving = false;
			});
		}
	}
}());

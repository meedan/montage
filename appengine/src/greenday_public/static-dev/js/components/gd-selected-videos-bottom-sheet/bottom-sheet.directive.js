(function () {
	angular.module('components')
		.directive('gdSelectedVideosBottomSheet', gdSelectedVideosBottomSheet);

	/** @ngInject */
	function gdSelectedVideosBottomSheet(PageService, ToastService, VideoModel, ProjectModel, _, moment) {
		var directive = {
			restrict: 'E',
			templateUrl: 'components/gd-selected-videos-bottom-sheet/bottom-sheet.html',
			link: link,
			controller: controller,
			controllerAs: 'ctrl',
			bindToController: true,
			scope: {
				videos: '=',
				actions: '=',
				selectedProject: '=?',
				selectedCollection: '=?',
				selectedTab: '=?'
			}
		};

		return directive;

		function link (scope, element) {

		}

		function controller($scope) {
			var ctrl = this;

			ctrl.archiveVideos = function (videos) {
				var pageData = PageService.getPageData(),
					ytVideoIds = _.pluck(videos, 'youtube_id'),
					projectId = pageData.projectId;

				VideoModel.batchArchive({
					params: { project_id: projectId },
					data: { youtube_ids: ytVideoIds }
				}).then(function () {
					var collection = pageData.videos;
					angular.forEach(videos, function (video) {
						video.archived_at = moment.utc().format();
						_.remove(collection.items, { id: video.id });
					});
					ctrl.selectedTab = null;
					$scope.$emit('videos:archived', videos);
					ToastService.show(videos.length + ' videos archived');

					// Update project meta
					ProjectModel.refresh(pageData.projectId);
				});
			};

			ctrl.removeFromCollection = function (videos) {
				var ytVideoIds = _.pluck(videos, 'youtube_id'),
					collection = PageService.getPageData().collection;

				collection
					.removeVideos(ytVideoIds)
					.then(function () {
						ctrl.selectedTab = null;
						$scope.$emit('collection:videosDeleted', videos);
						ToastService.show(videos.length + ' videos removed from collection');
					});
			};

			ctrl.markVideosAsDuplicate = function (videos) {
				var ytVideoIds = _.pluck(videos, 'youtube_id'),
					projectId = PageService.getPageData().projectId;

				VideoModel.batchMarkAsDuplicate({
					params: {
						project_id: projectId
					},
					data: {
						youtube_ids: ytVideoIds
					}
				}).then(function (response) {
					ctrl.selectedTab = null;
					angular.forEach(videos, function (video) {
						var instance = VideoModel.createInstance(video),
							v = VideoModel.get(instance.c_id);

						v.duplicate_count += 1;
						VideoModel.inject(v);
					});
					ToastService.show(videos.length + ' videos marked as duplicate');
				});
			};
		}
	}
}());

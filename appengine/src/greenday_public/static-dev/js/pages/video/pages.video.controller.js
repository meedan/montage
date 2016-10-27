/**
 * The video theater module.
 */
(function () {
	angular
		.module('pages.video')
		.controller('VideoPageCtrl', VideoPageCtrl);

	/** @ngInject */
	function VideoPageCtrl($scope, $timeout, $location, $filter, FilterUtils, PageService, VideoCollection, EventService, project, video, _, hotkeys) {
		var ctrl = this,
			hotkeyConfig = [{
				combo: ['shift+p'],
				description: 'Previous video',
				callback: previousVideo
			}, {
				combo: ['shift+n'],
				description: 'Next video',
				callback: nextVideo
			}],
			filtersToApply;

		/////////////////
		// Controller API
		/////////////////
		ctrl.player = null;
		ctrl.project = project;
		ctrl.gdVideoData = video.gd;
		ctrl.ytVideoData = video.yt.items[0];
		ctrl.videoStartTime = parseFloat($location.search().t || 0);
		ctrl.collectionId = $location.search().collectionId;
		ctrl.filters = FilterUtils.urlToObj($location.search().filters);
		ctrl.nextUrl = null;
		ctrl.prevUrl = null;
		ctrl.videoCollection = PageService.getPageData().videos;

		function previousVideo() {
			if (ctrl.prevUrl) {
				$location.url(ctrl.prevUrl);
			}
		}

		function nextVideo() {
			if (ctrl.nextUrl) {
				$location.url(ctrl.nextUrl);
			}
		}

		// Hotkeys
		angular.forEach(hotkeyConfig, function (config) {
			hotkeys.add(config);
		});

		if (!ctrl.videoCollection) {
			filtersToApply = {
				project_id: ctrl.project.id,
				archived_at: null
			};

			if (ctrl.collectionId) {
				filtersToApply.collection_id = ctrl.collectionId;
			}

			// If the video is archived, it means we are coming from the archived list
			if (ctrl.gdVideoData.archived_at !== null) {
				filtersToApply.archived = true;
				filtersToApply.archived_at = '!null';
			}

			ctrl.videoCollection = VideoCollection.get(filtersToApply);
		}

		PageService.updatePageData({
			title: ctrl.gdVideoData.name,
			headerTitle: ctrl.gdVideoData.name,
			loading: false,
			projectId: ctrl.project.id,
			project: ctrl.project,
			videoId: ctrl.gdVideoData.id,
			videos: ctrl.videoCollection
		});

		if (!ctrl.gdVideoData.watched) {
			$timeout(function () {
				ctrl.gdVideoData.setWatched(true);
			}, 2000);
		}

		ctrl.videoCollection
			.findAll({bypassCache: false})
			.then(function (videos) {
				var orderBy = $filter('orderBy'),
					orderKey = $location.search().orderBy,
					sortedVideos = orderBy(videos, orderKey),
					videoIndex = _.findIndex(sortedVideos, {id: ctrl.gdVideoData.id}),
					prevIndex = videoIndex - 1,
					nextIndex = videoIndex + 1,
					prevVideo = prevIndex >= 0 ? sortedVideos[prevIndex] : null,
					nextVideo = nextIndex < sortedVideos.length ? sortedVideos[nextIndex] : null,
					qs = $.param($location.search());

				if (qs) {
					qs = '?' + qs;
				}

				PageService.updatePageData({
					titleInfo: (videoIndex + 1) + ' of ' + sortedVideos.length
				}, true);

				if (prevVideo) {
					ctrl.prevVideo = prevVideo;
					ctrl.prevUrl = prevVideo.c_theatre_url + qs;
				}

				if (nextVideo) {
					ctrl.nextVideo = nextVideo;
					ctrl.nextUrl = nextVideo.c_theatre_url + qs;
				}
			});

		EventService.setVideo(ctrl.gdVideoData.id, ctrl.project.id);

		$scope.$on('$destroy', function () {
			EventService.setVideo();
			angular.forEach(hotkeyConfig, function (config) {
				hotkeys.del(config.combo);
			});
		});
	}
}());

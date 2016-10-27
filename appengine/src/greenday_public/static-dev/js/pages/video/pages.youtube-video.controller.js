/**
 * The video theater module.
 */
(function () {
	angular
		.module('pages.video')
		.controller('YoutubeVideoPageCtrl', YTVideoPageCtrl);

	/** @ngInject */
	function YTVideoPageCtrl($scope, $location, PageService, video, OneSearchService, FilterUtils, EventService, _) {
		var ctrl = this,
			snippet,
			recordingDetails,
			location;

		/////////////////
		// Controller API
		/////////////////
		ctrl.player = null;
		ctrl.videoStartTime = 0;
		ctrl.ytVideoData = video.items[0];

		EventService.setVideo(null, null);

		snippet = ctrl.ytVideoData.snippet;
		recordingDetails = ctrl.ytVideoData.recordingDetails;
		location = recordingDetails ? ctrl.ytVideoData.recordingDetails.location : null;

		ctrl.gdVideoData = {
			id: ctrl.ytVideoData.id,
			youtube_id: ctrl.ytVideoData.id,
			channel_name: snippet.channelTitle,
			publish_date: snippet.publishedAt,
			recorded_date: recordingDetails ? recordingDetails.recordingDate : null,
			latitude: location ? location.latitude : null,
			longitude: location ? location.longitude : null
		};

		PageService.updatePageData({
			title: ctrl.ytVideoData.snippet.title,
			headerTitle: ctrl.ytVideoData.snippet.title,
			loading: false,
			projectId: null,
			videoId: ctrl.ytVideoData.id
		});

		ctrl.videos = OneSearchService.currentResults || [];

		if (ctrl.videos.length === 0) {
			var qs = $location.search(),
				filter = FilterUtils.urlToObj(qs.search),
				filters = FilterUtils.cleanFilters(filter);


			if (_.values(filters).length) {
				OneSearchService
					.doSearch(filters)
					.then(function () {
						ctrl.videos = OneSearchService.currentResults;
					});
			}
		}


		$scope.$watch('ctrl.videos', function (videos) {
			if (videos && videos.length) {
				var videoIndex = _.findIndex(ctrl.videos, {youtube_id: ctrl.gdVideoData.id}),
					prevIndex = videoIndex - 1,
					nextIndex = videoIndex + 1,
					prevVideo = prevIndex >= 0 ? ctrl.videos[prevIndex] : null,
					nextVideo = nextIndex < ctrl.videos.length ? ctrl.videos[nextIndex] : null,
					qs = $.param($location.search());

				if (qs) {
					qs = '?' + qs;
				}

				if (prevVideo) {
					ctrl.prevVideo = prevVideo;
					ctrl.prevUrl = '/video/' + prevVideo.youtube_id + qs;
				}

				if (nextVideo) {
					ctrl.nextVideo = nextVideo;
					ctrl.nextUrl = '/video/' + nextVideo.youtube_id + qs;
				}
			}
		});

	}
}());

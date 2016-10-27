/**
 * video page routes
 */
(function () {
	angular
		.module('pages.video')
		.config(config);

	/** @ngInject */
	function config($routeProvider) {
		$routeProvider
			.when('/project/:projectId/video/:videoId', {
				templateUrl: 'pages/video/pages.video.html',
				controller: 'VideoPageCtrl',
				controllerAs: 'ctrl',
				reloadOnSearch: false,
				resolve: {
					/** @ngInject */
					project: function ($route, UserService, ProjectModel) {
						var $routeParams = $route.current.params;
						return UserService.getUser().then(function () {
							return ProjectModel.find($routeParams.projectId, { bypassCache: true });
						});
					},
					/** @ngInject */
					video: function ($route, $q, ToastService, UserService, VideoModel, YouTubeDataService) {
						var $routeParams = $route.current.params;

						return UserService.getUser().then(function () {
							var dfd = $q.defer(),
								promises = [],
								gdVideoPromise,
								ytVideoPromise,
								// We might need to change the parts used
								parts = ['recordingDetails', 'snippet', 'statistics'],
								cVideoId = $routeParams.projectId + ':' + $routeParams.videoId;


							gdVideoPromise = VideoModel.find(cVideoId, {
								params: {
									project_id: $routeParams.projectId
								}
							});

							gdVideoPromise
								.then(angular.noop, function (response) {
									ToastService.showError('There was a problem fetching video data.', 0);
									dfd.reject(response);
								});

							ytVideoPromise = YouTubeDataService.request('videos', 'list', {
								part: parts.join(','),
								id: $routeParams.videoId
							});

							ytVideoPromise
								.then(angular.noop, function (response) {
									ToastService.showError('There was a problem fetching data from YouTube.', 0);
									dfd.reject(response);
								});

							promises.push(gdVideoPromise, ytVideoPromise);

							$q.all(promises)
								.then(function (responses) {
									dfd.resolve({
										gd: responses[0],
										yt: responses[1]
									});
								});

							return dfd.promise;
						});
					}
				}
			})
			.when('/video/:videoId', {
				templateUrl: 'pages/video/pages.youtube-video.html',
				controller: 'YoutubeVideoPageCtrl',
				controllerAs: 'ctrl',
				reloadOnSearch: false,
				resolve: {
					video: function ($route, UserService, YouTubeDataService, ToastService) {
						var $routeParams = $route.current.params;

						return UserService.getUser().then(function () {
							var parts = ['recordingDetails', 'snippet', 'statistics'],
								ytVideoPromise = YouTubeDataService.request('videos', 'list', {
									part: parts.join(','),
									id: $routeParams.videoId
								});

							ytVideoPromise
								.then(angular.noop, function (response) {
									ToastService.showError('There was a problem fetching data from YouTube.', 0);
								});

							return ytVideoPromise;
						});
					}
				}
			});
	}
}());

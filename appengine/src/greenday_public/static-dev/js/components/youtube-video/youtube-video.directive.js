(function () {
	angular.module('components')
		.directive('youtubeVideo', youtubeVideo);

	/** @ngInject */
	function youtubeVideo($interval, $q, DEBUG, YouTubePlayerService) {
		var directive = {
			templateUrl: 'components/youtube-video/youtube-video.html',
			restrict: 'E',
			scope: {
				videoId: '=',
				autoPlay: '=?',
				player: '=',
				startTime: '=?'
			},
			controller: controller,
			controllerAs: 'ctrl',
			link: link,
			transclude: true
		};

		return directive;

		/** @ngInject */
		function controller($scope, $element, $attrs) {
			var ctrl = this;
			var tickTimer = null;

			var playerLoaded = false;
			var playerLoading = false;
			var playerApiDeferred = $q.defer();

			var playerOptions = {};
			var startTime = Math.round($scope.startTime);

			ctrl.iframe = $element.find('.youtube-video__iframe').get(0);

			$scope.player = ctrl.player = {
				$ytPlayerApi: null,
				loadVideo: loadVideo,
				api: {},
				info: {
					availablePlaybackRates: null,
					duration: null,
				},
				state: {
					currentTime: 0,
					frozenTime: null,
					isPlaying: false,
					playbackRate: 1
				}
			};

			$scope.$on('$destroy', function () {
				if (ctrl.player.$ytPlayerApi) {
					$interval.cancel(tickTimer);
					ctrl.player.$ytPlayerApi.destroy();
				}
			});

			// Load the API immediately for now.
			if ($scope.startTime > 0) {
				playerOptions.autoplay = $scope.autoPlay;
				playerOptions.start = startTime;
				$scope.player.state.currentTime = startTime;
			}

			loadVideo(playerOptions);

			/////////////////
			// Function definitions
			/////////////////
			function loadVideo(options) {
				if (!playerLoaded && !playerLoading) {
					playerLoading = true;

					YouTubePlayerService
						.createVideo(ctrl.iframe, $scope.videoId, options)
						.then(function (player) {
							ctrl.player.$ytPlayerApi = player;
							ctrl.player.$ytPlayerApi.addEventListener('onStateChange', onPlayerStateChange);

							if ($scope.autoPlay === true) {
								ctrl.player.$ytPlayerApi.playVideo();
							}

							// FOR DEBUGGING!
							if (DEBUG) {
								ctrl.player.$ytPlayerApi.mute();
							}

							playerLoading = false;
							playerLoaded = true;

							playerApiDeferred.resolve(player);
						});
				}

				return playerApiDeferred.promise;
			}

			function onPlayerStateChange(newState) {
				$scope.$apply(function () {

					// Playing
					if (newState.data === 1) {
						// Start time counter.
						tickTimer = $interval(onPlayTick, 500);
						ctrl.player.state.isPlaying = true;
					} else {
						// Stop the timer.
						$interval.cancel(tickTimer);
						ctrl.player.state.isPlaying = false;
					}

				});
			}

			function onPlayTick() {
				if (ctrl.player.state.frozenTime === null) {
					ctrl.player.state.currentTime = ctrl.player.$ytPlayerApi
						.getCurrentTime();
				}
			}

			/**
			 * Player API method wrappers.
			 * We need these so that we can update our state variable so that we
			 * don't need to wait for the player to start playing to update the
			 * state.
			 */
			ctrl.player.api.seekTo = function(seconds, allowSeekAhead) {
				var dfd = $q.defer();

				loadVideo().then(function () {
					var duration = ctrl.player.$ytPlayerApi.getDuration();

					ctrl.player.$ytPlayerApi.seekTo(seconds, allowSeekAhead);

					// Mimic YouTube API behaviour and cap the seekTo value to the
					// duration of the video
					if (seconds < 0) {
						seconds = 0;
					} else if (seconds > duration) {
						seconds = duration;
					}

					if (ctrl.player.state.frozenTime === null) {
						ctrl.player.state.currentTime = seconds;
					}

					dfd.resolve();
				});

				return dfd.promise;
			};

			ctrl.player.api.freeze = function() {
				// If the player is already frozen, do nothing.
				if (ctrl.player.state.frozenTime !== null) {
					return;
				}

				// Freeze the player
				ctrl.player.state.frozenTime = ctrl.player.state.currentTime;
			};

			ctrl.player.api.unfreeze = function() {
				ctrl.player.$ytPlayerApi.seekTo(ctrl.player.state.currentTime, true);
				ctrl.player.state.frozenTime = null;

				// Erm. Why does the YT API start playing when you call seekTo?
				ctrl.player.$ytPlayerApi.pauseVideo();
			};
		}

		/** @ngInject */
		function link(scope, element, attrs) {
			element.addClass('youtube-video');
		}
	}
}());

/**
 * Youtube service
 *
 */
(function () {
	angular
		.module('app.services')
		.factory('YouTubePlayerService', YouTubePlayerService);

	/** @ngInject */
	function YouTubePlayerService($q, $window, GapiLoader, oAuthParams) {
		var service = {
				createVideo: createVideo,
				getRelativeFrameTime: getRelativeFrameTime,
				skipTime: skipTime,
				skipFrames: skipFrames,
				togglePlay: togglePlay,
				toggleFullScreen: toggleFullScreen,
				increaseVolume: increaseVolume,
				decreaseVolume: decreaseVolume,
				toggleMute: toggleMute,
				seekToTime: seekToTime,
				seekToPercentage: seekToPercentage,
				slowDown: slowDown,
				speedUp: speedUp,
				setPlaybackRate: setPlaybackRate
			},
			defaultPlayerVars = {
				autoplay: 0,
				controls: 1,
				iv_load_policy: 3,
				loop: 1,
				modestbranding: 1,
				nologo: 1,
				ps: 'play',
				rel: 0,
				showinfo: '0',
				vq: 'hd720'
			},
			apiLoadDeferred = $q.defer(),
			baseUrl = '//www.googleapis.com/youtube/v3/videos?' + oAuthParams.api_key,
			gapi,
			onYouTubePlayerReady = function () {
				apiLoadDeferred.resolve(window.YT);
				return window.YT;
			};

		/* jshint ignore:start */
		$window['onYouTubeIframeAPIReady'] = onYouTubePlayerReady;
		/* jshint ignore:end */

		return service;

		function loadAPI() {
			var tag = document.createElement('script'),
				firstScriptTag = document.getElementsByTagName('script')[0];

			tag.src = 'https://www.youtube.com/player_api';
			firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
			return apiLoadDeferred.promise;
		}

		function createVideo(container, videoId, playerVars) {
			var ytDeferred = $q.defer();

			if (!playerVars) {
				playerVars = {
					rel: 0
				};
			}

			playerVars = angular.extend({}, defaultPlayerVars, playerVars);

			loadAPI().then(function (YT) {
				var ytplayer = new YT.Player(container, {
					height: '720',
					width: '1280',
					videoId: videoId,
					html5: true,
					playerVars: playerVars,
					events: {
						onReady: function () {
							ytDeferred.resolve(ytplayer);
						}
					}
				});
			});

			return ytDeferred.promise;
		}

		/**
		 * Skips the YT video by `time` seconds
		 * @param  {Number} time
		 *         Number of seconds to skip by. Supports negative numbers to
		 *         skip backwards.
		 *
		 * @return {Undefined}
		 */
		function skipTime(player, time) {
			if (player.$ytPlayerApi) {
				var currentTime = player.$ytPlayerApi.getCurrentTime();
				var newTime = currentTime + time;
				player.api.seekTo(newTime, true);
			}
		}

		/**
		 * Skips the YT video by `numFrames` frames.
		 * @param  {Number} frames
		 *         Number of frames to skip by. Supports negative numbers to
		 *         skip backwards.
		 *
		 * @return {Undefined}
		 */
		function skipFrames(player, frames) {
			var playerApi,
				currentTime,
				newTime;

			if (player.$ytPlayerApi) {
				playerApi = player.$ytPlayerApi;

				playerApi.pauseVideo();
				currentTime = playerApi.getCurrentTime();
				newTime = getRelativeFrameTime(player, currentTime, frames);

				playerApi.seekTo(newTime, true);

				// Manually update the scope so the ui doesn't have to wait
				// until the next tick to update
				player.state.currentTime = playerApi.getCurrentTime();
			}
		}

		/**
		 * Gets the relative frame's time
		 * @param {YT.Player} player The Youtube player
		 * @param {Number} baseTime Base time
		 * @param {Number} numFrames The number of frames
		 * @return {Number} The new time based on baseTime
		 */
		function getRelativeFrameTime(player, baseTime, numFrames) {
			var fps = 25,
				playerApi,
				timeToAdvance,
				newTime;

			if (player.$ytPlayerApi) {
				playerApi = player.$ytPlayerApi;

				timeToAdvance = (1/fps) * numFrames;
				newTime = baseTime + timeToAdvance;
			}

			return newTime;
		}

		/**
		 * Toggles play/pause
		 * @param {YT.player} player The Youtube player
		 */
		function togglePlay(player) {
			player.loadVideo().then(function () {
				var playerApi = player.$ytPlayerApi;
				var playState = playerApi.getPlayerState();

				if (playState === 1) {
					playerApi.pauseVideo();
				} else {
					playerApi.playVideo();
				}
			});
		}

		/**
		 * Toggles fullscreen of the video
		 * @param {YT.player} player The Youtube player
		 */
		function toggleFullScreen(player) {
			player.loadVideo().then(function () {
				var playerApi = player.$ytPlayerApi,
					playerElement = playerApi.getIframe(),
					isFullScreen = document.isFullScreen || document.webkitIsFullScreen,
					requestFullScreen = playerElement.requestFullScreen || playerElement.webkitRequestFullScreen,
					exitFullScreen = document.exitFullscreen || document.webkitExitFullscreen;

				if (isFullScreen === false) {
					if (requestFullScreen) {
						requestFullScreen.bind(playerElement)();
					}
				} else {
					if (exitFullScreen) {
						exitFullScreen.bind(document)();
					}
				}
			});
		}

		/**
		 * Increases the volume by `amount`
		 * @param {YT.Player} player The Youtube player
		 * @param {Number} amount The amount of the volume
		 */
		function increaseVolume(player, amount) {
			if (angular.isUndefined(amount)) {
				amount = 1;
			}
			player.loadVideo().then(function () {
				var playerApi = player.$ytPlayerApi,
					currentVolume = playerApi.getVolume(),
					isMuted = playerApi.isMuted();

				// If it's muted, unmoute it
				if (isMuted) {
					playerApi.unMute();
				}

				playerApi.setVolume(currentVolume + 1);
			});
		}

		/**
		 * Decreases the volume by `amount`
		 * @param {YT.Player} player The Youtube player
		 * @param {Number} amount The amount of the volume
		 */
		function decreaseVolume(player, amount) {
			if (angular.isUndefined(amount)) {
				amount = 1;
			}
			player.loadVideo().then(function () {
				var playerApi = player.$ytPlayerApi,
					currentVolume = playerApi.getVolume();

				playerApi.setVolume(currentVolume - 1);
			});
		}

		/**
		 * Toggles the mute state
		 * @param {YT.player} player The Youtube player
		 */
		function toggleMute(player) {
			player.loadVideo().then(function () {
				var playerApi = player.$ytPlayerApi,
					isMuted = playerApi.isMuted();

				if (isMuted) {
					playerApi.unMute();
				} else {
					playerApi.mute();
				}
			});
		}

		/**
		 * Seeks to a specific time of the video
		 * @param {YT.Player} player The Youtube video
		 * @param {Number} time The seconds to seek to
		 */
		function seekToTime(player, time) {
			player.loadVideo().then(function () {
				var playerApi = player.$ytPlayerApi,
					totalTime = playerApi.getDuration();

				time = Math.max(time, 0);
				time = Math.min(time, totalTime);

				playerApi.seekTo(time);
			});
		}

		/**
		 * Seeks to a specific percent of the video
		 * @param {YT.Player} player The Youtube video
		 * @param {Number} percentage The percentage to seek to
		 */
		function seekToPercentage(player, percentage) {
			player.loadVideo().then(function () {
				var playerApi = player.$ytPlayerApi,
					totalTime = playerApi.getDuration(),
					time = Math.ceil(totalTime * percentage / 100);

				playerApi.seekTo(time);
			});
		}

		/**
		 * Sets the playback rate to a given rate
		 * @param {YT.Player} player The Youtube player
		 * @param {Number} newRate The new rate to set the playback rate to
		 */
		function setPlaybackRate(player, newRate) {
			player.loadVideo().then(function () {
				var playerApi = player.$ytPlayerApi,
					availableRates = playerApi.getAvailablePlaybackRates(),
					isRateAvailable = availableRates.indexOf(newRate) !== 1;

				if (isRateAvailable) {
					playerApi.setPlaybackRate(newRate);
				}
			});
		}

		/**
		 * Gets the next available playback rate with the given step
		 * @param {YT.Player} player The Youtube player
		 * @param {Number} step The step for the next playback rate
		 * @return {Number} The next available playback rate
		 */
		function getNextPlaybackRate(player, step) {
			var playerApi = player.$ytPlayerApi,
				availableRates = playerApi.getAvailablePlaybackRates(),
				currentRate = playerApi.getPlaybackRate(),
				currentRateIndex = availableRates.indexOf(currentRate),
				newRateIndex = currentRateIndex + step,
				newRate = availableRates[newRateIndex];

			return newRate;
		}

		/**
		 * Slows down the playback
		 * @param {YT.Player} player The Youtube player
		 */
		function slowDown(player) {
			player.loadVideo().then(function () {
				var newRate = getNextPlaybackRate(player, -1);
				setPlaybackRate(player, newRate);
			});
		}

		/**
		 * Speeds up the playback
		 * @param {YT.Player} player The Youtube player
		 */
		function speedUp(player) {
			player.loadVideo().then(function () {
				var newRate = getNextPlaybackRate(player, 1);
				setPlaybackRate(player, newRate);
			});
		}

	}
}());

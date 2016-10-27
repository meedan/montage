(function () {
	angular.module('components')
		.directive('gdVideoControls', videoControls);

	/** @ngInject */
	function videoControls(YouTubePlayerService, hotkeys) {
		var directive = {
			templateUrl: 'components/gd-video-controls/gd-video-controls.html',
			restrict: 'E',
			controller: controller,
			controllerAs: 'ctrl',
			scope: {
				player: '=',
			}
		};

		return directive;

		/** @ngInject */
		function controller($scope, $element, $attrs) {
			var ctrl = this;

			// Prevent any default behaviour and stop the event bubbling and possibly
			// triggering handlers elsewhere.
			var handleHotkey = function (evt) {
				if (evt && evt.stopPropagation) {
					evt.stopPropagation();
					evt.preventDefault();
				}
			};

			/////////////////
			// Controller API
			/////////////////
			ctrl.skipTime = function (time) {
				YouTubePlayerService.skipTime($scope.player, time);
			};

			ctrl.skipFrames = function (frames) {
				YouTubePlayerService.skipFrames($scope.player, frames);
			};

			ctrl.togglePlay = function () {
				YouTubePlayerService.togglePlay($scope.player);
			};

			ctrl.toggleFullScreen = function () {
				YouTubePlayerService.toggleFullScreen($scope.player);
			};

			ctrl.increaseVolume = function () {
				YouTubePlayerService.increaseVolume($scope.player);
			};

			ctrl.decreaseVolume = function () {
				YouTubePlayerService.decreaseVolume($scope.player);
			};

			ctrl.toggleMute = function () {
				YouTubePlayerService.toggleMute($scope.player);
			};

			ctrl.seekToPercentage = function (percentage) {
				YouTubePlayerService.seekToPercentage($scope.player, percentage);
			};

			ctrl.speedUp = function () {
				YouTubePlayerService.speedUp($scope.player);
			};

			ctrl.slowDown = function () {
				YouTubePlayerService.slowDown($scope.player);
			};

			ctrl.hotkeyConfig = [{
				combo: ['space', 'k'],
				description: 'Play/pause video',
				callback: function (evt) {
					handleHotkey(evt);
					ctrl.togglePlay();
				}
			}, {
				combo: ['f'],
				description: 'Toggle fullscreen',
				callback: function (evt) {
					handleHotkey(evt);
					ctrl.toggleFullScreen();
				}
			}, {
				combo: ['up'],
				description: 'Increase volume',
				callback: function (evt) {
					handleHotkey(evt);
					ctrl.increaseVolume();
				}
			}, {
				combo: ['down'],
				description: 'Decrease volume',
				callback: function (evt) {
					handleHotkey(evt);
					ctrl.decreaseVolume();
				}
			}, {
				combo: ['left'],
				description: 'Seek backwards 5 seconds',
				callback: function (evt) {
					handleHotkey(evt);
					ctrl.skipTime(-5);
				}
			}, {
				combo: ['right'],
				description: 'Seek forwards 5 seconds',
				callback: function (evt) {
					handleHotkey(evt);
					ctrl.skipTime(5);
				}
			}, {
				combo: ['m'],
				description: 'Toggle mute',
				callback: function (evt) {
					handleHotkey(evt);
					ctrl.toggleMute();
				}
			}, {
				combo: ['j'],
				description: 'Seek backwards 10 seconds',
				callback: function (evt) {
					handleHotkey(evt);
					ctrl.skipTime(-10);
				}
			}, {
				combo: ['l'],
				description: 'Seek forwards 10 seconds',
				callback: function (evt) {
					handleHotkey(evt);
					ctrl.skipTime(10);
				}
			}, {
				combo: ['home'],
				description: 'Seek to beginning',
				callback: function (evt) {
					handleHotkey(evt);
					ctrl.seekToPercentage(0);
				}
			}, {
				combo: ['end'],
				description: 'Seek to end',
				callback: function (evt) {
					handleHotkey(evt);
					ctrl.seekToPercentage(100);
				}
			}, {
				combo: ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'],
				description: 'Seek to percentage',
				callback: function (evt) {
					var value = parseInt(String.fromCharCode(evt.charCode), 10);
					handleHotkey(evt);
					ctrl.seekToPercentage(value * 10);
				}
			}, {
				combo: ['<'],
				description: 'Slow down',
				callback: function (evt) {
					handleHotkey(evt);
					ctrl.slowDown();
				}
			}, {
				combo: ['>'],
				description: 'Speed up',
				callback: function (evt) {
					handleHotkey(evt);
					ctrl.speedUp();
				}
			}];

			// Hotkeys
			angular.forEach(ctrl.hotkeyConfig, function (config) {
				hotkeys.add(config);
			});

			$scope.$on('$destroy', function () {
				angular.forEach(ctrl.hotkeyConfig, function (config) {
					hotkeys.del(config.combo);
				});
			});
		}
	}
}());

(function () {
	angular.module('components')
		.constant('YT_THUMB_UPDATE_INTERVAL', 1000)
		.directive('gdYoutubeThumbnail', youtubeThumbnail);

	/** @ngInject */
	function youtubeThumbnail(_, imagePreloader, YT_THUMB_UPDATE_INTERVAL) {
		var STANDARD_THUMBNAIL_URL = '//img.youtube.com/vi/<VIDEO_ID>/<VARIANT>.jpg',
			THUMB_AT_TIME_URL = '/yt-thumbnail/?id=<VIDEO_ID>&ats=<TIME>';

		var directive = {
			templateUrl: 'components/gd-youtube-thumbnail/gd-youtube-thumbnail.html',
			restrict: 'E',
			controller: controller,
			controllerAs: 'ctrl',
			link: link,
			scope: {
				time: '=?',
				videoId: '='
			}
		};

		return directive;

		/** @ngInject */
		function controller($scope, $element, $attrs, $transclude) {
			var ctrl = this;
			ctrl.loaded = false;
		}

		/** @ngInject */
		function link(scope, element, attrs, ctrl) {
			var preloadPromise;

			element.addClass('gd-youtube-thumbnail');

			/////////////////
			// Scope API
			/////////////////
			scope.url = null;
			scope.loadedUrl = null;

			/////////////////
			// Scope watchers
			/////////////////
			scope.$watch('time', function (nv, ov) {
				if (angular.isDefined(nv)) {
					updateImage();
				}
			});

			/////////////////
			// Scope events
			/////////////////
			//scope.$on('$destroy', destroy);

			/////////////////
			// Setup
			/////////////////

			/////////////////
			// Private functions
			/////////////////
			var updateImage = _.debounce(function () {
				updateThumbnailUrl();
				preloadImage();
			}, YT_THUMB_UPDATE_INTERVAL);

			/*
			function destroy() {
			}
			*/

			function imagePreloadResolve(imageLocations) {
				ctrl.loaded = true;
				scope.loadedUrl = scope.url;
			}

			function imagePreloadReject(imageLocation) {
				console.error('Image Failed', imageLocation);
			}

			function updateThumbnailUrl() {
				var url;

				// timed thumbnail url no longer working
				// disabling until we have another solution
				var useTimedThumbnails = false;

				if (useTimedThumbnails && angular.isDefined(scope.time) && scope.time !== 0) {
					url = THUMB_AT_TIME_URL.replace('<VIDEO_ID>', scope.videoId);
					url = url.replace('<TIME>', Math.round(scope.time * 1000));
				} else {
					url = STANDARD_THUMBNAIL_URL.replace('<VIDEO_ID>', scope.videoId);
					url = url.replace('<VARIANT>', 'default');
				}

				scope.url = url;
			}

			function preloadImage() {
				ctrl.loaded = false;

				preloadPromise = imagePreloader
					.preloadImages([scope.url])
					.then(imagePreloadResolve, imagePreloadReject);
			}
		}
	}
}());

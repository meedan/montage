(function () {
	angular.module('components')
		.directive('gdVideoList', videoList);

	/** @ngInject */
	function videoList($routeParams, $filter, $location, $timeout, ToastService, PageService, _, hotkeys) {
		var directive = {
			templateUrl: 'components/gd-video-list/gd-video-list.html',
			restrict: 'E',
			scope: {
				options: '=',
				ordering: '=',
				videos: '=',
				isFiltering: '=',
				quickFilter: '='
			},
			link: link,
			controller: controller,
			controllerAs: 'ctrl',
			require: ['^gdVideoList']
		};

		return directive;

		function link(scope, element, attrs, controllers) {
			var videoListCtrl = controllers[0];

			scope.$watch('isFiltering', function (newVal, oldVal) {
				if (newVal !== oldVal) {
					if (scope.isFiltering === false) {
						videoListCtrl.enableManualOrdering = true;
					} else {
						videoListCtrl.enableManualOrdering = false;
					}
				}
			});
		}

		function controller($scope) {
			var ctrl = this,
				videoListItemSelector = '.video-list__item',
				hotkeyConfig = [{
					combo: ['j'],
					description: 'Highlight next video',
					callback: function () {
						highlightVideo(1);
					}
				}, {
					combo: ['k'],
					description: 'Highlight previous video',
					callback: function () {
						highlightVideo(-1);
					}
				}, {
					combo: ['x'],
					description: 'Select highlighted video',
					callback: function () {
						selectVideo();
					}
				}];

			ctrl.project = PageService.getPageData().project;
			ctrl.isCollection = !!$routeParams.collectionId;
			ctrl.selectedVideos = [];
			ctrl.allSelected = false;
			ctrl.enableManualOrdering = true;
			ctrl.visibleVideos = [];
			ctrl.fetchingInBackground = false;
			ctrl.highlightedIndex = null;
			ctrl.highlightedVideoEl = null;

			// Hotkeys
			angular.forEach(hotkeyConfig, function (config) {
				hotkeys.add(config);
			});

			$scope.$on('$destroy', function () {
				angular.forEach(hotkeyConfig, function (config) {
					hotkeys.del(config.combo);
				});
			});

			$scope.collectionId = $routeParams.collectionId || null;

			$scope.$watchCollection('videos', onDataFilterChange);
			$scope.$watch('quickFilter', onDataFilterChange);

			$scope.$on('video:selectedChange', updateSelectedVideos);

			$scope.$on('filterSet::background-fetch::start', function () {
				ctrl.fetchingInBackground = true;
			});

			$scope.$on('filterSet::fetch::end', function () {
				ctrl.fetchingInBackground = false;
			});

			$scope.$watch('ordering', function (newVal) {
				if (newVal) {
					orderBy(newVal);
				}
			});

			function highlightVideo(step) {
				var videoEls = angular.element(videoListItemSelector),
					highlightedVideos = angular.element(videoListItemSelector + '.highlighted'),
					currentIndex = ctrl.highlightedIndex !== null ? ctrl.highlightedIndex : -1,
					nextIndex = currentIndex + step,
					videoEl,
					container = angular.element('.project__main-content'),
					containerHeight = container.height(),
					offsetTop,
					scrollTop = container.scrollTop(),
					videoElHeight;

				if (nextIndex < 0) {
					nextIndex = videoEls.length - 1;
				} else if (nextIndex >= videoEls.length) {
					nextIndex = 0;
				}

				videoEl = videoEls[nextIndex];

				if (videoEl) {
					videoEl = angular.element(videoEl);
					ctrl.highlightedIndex = nextIndex;
					ctrl.highlightedVideoEl = videoEl;
					highlightedVideos.removeClass('highlighted');
					videoEl.addClass('highlighted');
					offsetTop = videoEl.position().top;
					videoElHeight = videoEl.height();

					if (offsetTop + videoElHeight - scrollTop > containerHeight) {
						container.scrollTop(offsetTop);
					} else if (scrollTop > offsetTop) {
						container.scrollTop(offsetTop - videoElHeight);
					}

				}
			}

			function selectVideo() {
				if (!ctrl.highlightedVideoEl) {
					return;
				}
				$timeout(function () {
					var gdButton = ctrl.highlightedVideoEl.find('.gd-select-video-button').eq(0);
					gdButton.trigger('click');
				});
			}

			ctrl.onDrop = function (moveVideoFromYtId, moveVideoToYtId) {
				// dont do any ordering if a video is dropped on itself or if we dont have a collection.
				if (ctrl.isCollection) {
					if (parseInt(moveVideoFromYtId, 10) !== parseInt(moveVideoToYtId, 10)) {
						var video = _.findLast($scope.videos, {youtube_id: moveVideoToYtId});
						$scope.$emit('collection:videosOrderChanged', $scope.collectionId, moveVideoFromYtId, video);
					}
				} else {
					ToastService.showError('Videos can only be ordered in a collection');
				}
			};

			ctrl.selectAllVideos = function (selected) {
				angular.forEach(ctrl.visibleVideos, function (video) {
					video.selected = selected;
				});

				ctrl.allSelected = selected;

				updateSelectedVideos();
			};

			ctrl.sort = sort;

			function orderBy(ordering) {
				var qs = $location.search();
				qs.orderBy = (ordering.reverse ? '-' : '') + ordering.currentKey;
				$location.search(qs);
				// Replace the history instead of adding a new entry
				$location.replace();
				ctrl.ordering = ordering;
			}

			function sort(key) {
				if ($scope.ordering.currentKey === key) {
					$scope.ordering.reverse = !$scope.ordering.reverse;
				} else {
					$scope.ordering.reverse = true;
				}
				$scope.ordering.currentKey = key;
				orderBy($scope.ordering);
			}

			function onDataFilterChange() {
				ctrl.highlightedIndex = null;
				ctrl.highlightedVideoEl = null;
				updateVisibleVideos();
				ctrl.listInfo = calculateCounts(ctrl.visibleVideos);
				updateSelectedVideos();
			}

			function updateSelectedVideos() {
				ctrl.selectedVideos = _.filter(ctrl.visibleVideos, {selected: true});
				if (ctrl.selectedVideos.length === ctrl.visibleVideos.length) {
					ctrl.allSelected = true;
				} else {
					ctrl.allSelected = false;
				}
			}

			function updateVisibleVideos() {
				ctrl.visibleVideos = $filter('filter')($scope.videos, $scope.quickFilter);
			}
		}

		function calculateCounts(videos) {
			var durations = _.pluck(videos, 'duration'),
				tagCounts = _.pluck(videos, 'tag_count'),
				totalDuration,
				totalTagCount,
				totalHours,
				remainderMinutes;

			totalDuration = _.reduce(durations, function (totalDuration, duration) {
				return parseInt(totalDuration, 10) + parseInt(duration, 10);
			});

			totalDuration = parseInt(totalDuration, 10);

			totalHours = Math.floor(totalDuration / 3600);
			remainderMinutes = Math.floor(totalDuration / 60) - (totalHours * 60);

			totalTagCount = _.reduce(tagCounts, function (totalTagCount, tagCount) {
				return parseInt(totalTagCount, 10) + parseInt(tagCount, 10);
			});

			return {
				videoCount: videos.length,
				totalTagCount: totalTagCount || 0,
				totalDuration: {
					hours: totalHours || 0,
					minutes: remainderMinutes || 0
				}
			};
		}
	}
}());

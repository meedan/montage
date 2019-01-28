(function () {
	angular.module('components.videoTimeline')
		.constant('RESIZE_DIRECTION', {
			'LEFT': 'RESIZE_DIRECTION_LEFT',
			'RIGHT': 'RESIZE_DIRECTION_RIGHT'
		})
		.constant('MINIMUM_TAG_DURATION', 0.5)
		.constant('MINIMUM_TAG_SEPARATION', 1)
		.directive('gdVideoTimelineTagInstance', videoTimelineTagInstance);

	/** @ngInject */
	function videoTimelineTagInstance(_, $q, $document, $timeout, VideoTagInstanceModel,
		ToastService, YouTubePlayerService,
		MINIMUM_TAG_DURATION, MINIMUM_TAG_SEPARATION,
		RESIZE_DIRECTION, TIMELINE_PX_PER_SECOND) {

		var directive = {
			templateUrl: 'components/gd-video-timeline/gd-video-timeline-tag-instance.html',
			restrict: 'E',
			controller: controller,
			controllerAs: 'ctrl',
			link: link,
			require: ['gdVideoTimelineTagInstance', '^gdVideoTimeline'],
			scope: {
				instance: '=',
				player: '=',
				video: '='
			}
		};

		return directive;

		/** @ngInject */
		function controller($scope, $element, $attrs, $transclude) {
			var ctrl = this;

			/////////////////
			// Controller API
			/////////////////
			ctrl.deleteInstance = function($event) {
				// FIXME: Doens't work, because gd-button doesn't support
				// passing $event :(.
				// $event.stopPropagation();

				return VideoTagInstanceModel.destroy($scope.instance);
			};

			ctrl.expandToDuration = function ($event) {
				$event.stopPropagation();

				ToastService.show('Expanding tag…', false, {
					hideDelay: 0
				});

				var save,
					instances = VideoTagInstanceModel.filter({
						video_tag_id: $scope.instance.video_tag_id,
						where: {
							id: {
								'!==': $scope.instance.id
							}
						}
					}),
					promises = [];

				angular.forEach(instances, function(instance) {
					promises.push(VideoTagInstanceModel.destroy(instance));
				});

				$scope.instance.start_seconds = 0;
				$scope.instance.end_seconds = $scope.video.duration;

				$q.all(promises).then(function () {
					ctrl.save(true);
				});

			};

			ctrl.getLeft = function() {
				return $scope.instance.start_seconds / $scope.video.duration * 100;
			};

			ctrl.getWidth = function() {
				var tagDuration = $scope.instance.end_seconds - $scope.instance.start_seconds;
				var tagWidth = tagDuration / $scope.video.duration * 100;
				return tagWidth;
			};

			ctrl.playFromTag = function($event) {
				if ($scope.player && $scope.player.$ytPlayerApi) {
					$scope.player.api.seekTo($scope.instance.start_seconds);
				}

				$event.stopPropagation();
			};

			ctrl.save = function (instant) {
				if (instant) {
					doSave();
				} else {
					debouncedSave();
				}
			};

			ctrl.fineTune = function(direction) {
				var newTime,
					timeProp,
					frames = (direction === 'forwards') ? 10 : -10;

				// Prevent timeline form updating in response to events while
				// we interact.
				$scope.timelineCtrl.onTagInteractionStart();

				if ($scope.fineTuneSide === 'start') {
					timeProp = 'start_seconds';
				} else {
					timeProp = 'end_seconds';
				}

				$scope.instance[timeProp] = YouTubePlayerService
					.getRelativeFrameTime($scope.player,
						$scope.instance[timeProp], frames);

				// Update the video frame
				$scope.player.$ytPlayerApi.pauseVideo();
				$scope.player.api.seekTo($scope.instance[timeProp], true);
				$scope.player.$ytPlayerApi.pauseVideo();

				ctrl.save();
			};

			/////////////////
			// Private functions
			/////////////////
			var debouncedSave = _.debounce(doSave, 2000);

			function doSave() {
				var savePromise = $scope.instance.DSSave();

				showSaveToast();

				savePromise.then(function () {
					ToastService.hide();
				});

				savePromise.catch(function (resp) {
					ToastService.show('There was a problem saving tag changes: ' +
						resp.data.error.message, true, {
							hideDelay: 0
						});
				});
			}

			function showSaveToast() {
				ToastService.show('Saving tags…', false, {
					hideDelay: 0
				});
			}
		}

		/** @ngInject */
		function link(scope, element, attrs, ctrls) {
			var $timeline = element.parents('.gd-video-timeline__timeline'),
				timelineOffset,
				timelineWidth,
				updateTimer;

			element.addClass('gd-video-timeline-tag-instance');

			/////////////////
			// Scope API
			/////////////////
			scope.timelineCtrl = ctrls[1];

			// State variables
			scope.resizing = false;
			scope.controlsVisible = false;
			scope.fineTuneVisible = false;

			scope.draggingLimits = {
				x: {
					min: null,
					max: null
				}
			};

			// Timers
			scope.hoverTimer = null;

			// Functions
			scope.scheduleControlsShow = scheduleControlsShow;
			scope.scheduleControlsHide = scheduleControlsHide;

			scope.showFineTuneControls = showFineTuneControls;
			scope.hideFineTuneControls = hideFineTuneControls;

			scope.onResizeHandleMouseEnter = onResizeHandleMouseEnter;

			// Callbacks
			scope.onResizeHandleMouseDown = onResizeHandleMouseDown;
			scope.onFineTuneMouseLeave = onFineTuneMouseLeave;
			scope.onTagMouseenter = onTagMouseenter;
			scope.onTagMouseleave = onTagMouseleave;

			/////////////////
			// Scope watchers
			/////////////////
			// FIXME: This would probably be better off done in the template,
			// perhaps with ng-style?
			scope.$watch('instance.start_seconds', function () {
				updatePosition();
			});

			scope.$watch('instance.end_seconds', function () {
				updatePosition();
			});

			scope.$watch('resizing', function (resizing, oldResizing) {
				if (angular.isDefined(resizing) && angular.isDefined(oldResizing)) {
					if (resizing) {
						element.addClass('is-resizing');
					} else {
						element.removeClass('is-resizing');
					}
				}
			});

			/////////////////
			// Scope events
			/////////////////
			//scope.$on('$destroy', destroy);

			/////////////////
			// Private functions
			/////////////////
			/*
			function destroy() {
			}
			*/

			function updatePosition() {
				element.attr('style', 'left: ' + scope.ctrl.getLeft() + '%; width: ' + scope.ctrl.getWidth() + '%;');
			}

			// FIXME:
			function onResizingMouseMove($event) {
				var x = $event.pageX - timelineOffset.left;
				var y = $event.pageY - timelineOffset.top;
				var xPerc;
				var time;
				var newWidth;
				var limits = scope.draggingLimits;

				if (scope.resizeDirection === RESIZE_DIRECTION.LEFT) {
					// Adjust the left of the tag

					// Convert the x offset into a percentage of the
					// timeline width
					xPerc = (x / timelineWidth) * 100;

					// Convert the start time from a percentage of the video's
					// total duration into to seconds and apply it to
					// the scope.
					time =
						(scope.video.duration / 100) * xPerc;

					// Cap new start time to prevent negative start_time
					if (time < 0) {
						time = 0;
					}

					// Apply limits
					if (time < limits.x.min) {
						time = limits.x.min;
					} else if (time > limits.x.max) {
						time = limits.x.max;
					}

					scope.$apply(function () {
						scope.instance.start_seconds = time;
					});
				} else {
					// Adjust the width of the tag
					xPerc = (x / timelineWidth) * 100;
					newWidth = xPerc - scope.ctrl.getLeft();

					time = scope.instance.start_seconds +
						((scope.video.duration / 100) * newWidth);

					// Cap minimum tag length to ensure the tag's end time is
					// always after it's start time.
					if (time - scope.instance.start_seconds < MINIMUM_TAG_DURATION) {
						time = scope.instance.start_seconds + MINIMUM_TAG_DURATION;
					}

					// Cap maximum tag width to prevent end_time longer than
					// video duration
					if (time > scope.video.duration) {
						time = scope.video.duration;
					}

					// Apply limits
					if (time < limits.x.min) {
						time = limits.x.min;
					} else if (time > limits.x.max) {
						time = limits.x.max;
					}

					scope.$apply(function () {
						scope.instance.end_seconds = time;
					});
				}

				// Update the players time
				scope.player.api.seekTo(time, true);

				scope.$digest();
			}

			function onResizeHandleMouseDown($event) {
				var $handle = $($event.currentTarget),
					isLeft = $handle.hasClass('gd-video-timeline-tag-instance__handle--left');

				// Prevent the click from calling the playFromTag callback which
				// is bound as an ng-click handler to the parent tag
				// content element.
				$event.stopPropagation();
				$event.preventDefault();

				// Prevent a second click on the handle from triggering
				// resizing again.
				if (scope.timelineCtrl.isResizingTag()) {
					return;
				}

				// Figure out the resize direction and update resizing state.
				scope.resizing = true;
				scope.resizeDirection =
					isLeft ? RESIZE_DIRECTION.LEFT: RESIZE_DIRECTION.RIGHT;

				// Let the timeline controller know we are resizing a tag.
				scope.timelineCtrl.setResizingTag(true);

				// Ensure fine-tune controls are hidden.
				hideFineTuneControls();

				// Freeze the timeline while we fine-tune.
				scope.timelineCtrl.onTagInteractionStart();

				// Pause the video if it's playing
				scope.player.$ytPlayerApi.pauseVideo();

				// Setup mousemove/mouseup handlers.
				$document.on('mouseup', onEndResize);
				$document.on('mousemove', onResizingMouseMove);

				timelineOffset = $timeline.offset();
				timelineWidth = $timeline.width();

				// Find limits.
				calculateDraggingLimits(scope.resizeDirection);
			}

			// TODO: Simplify this logic by using _.max()?
			function calculateDraggingLimits(direction) {
				var $sibling,
					instanceContainer = element.parents('.js-tag-instances'),
					nearestSibling,
					s,
					siblingModel,
					siblings;

				siblings = instanceContainer
					.find('gd-video-timeline-tag-instance')
					.not(element);

				for (s = 0; s < siblings.length; s++) {
					$sibling = siblings.eq(s);
					siblingModel = {};
					siblingModel.start_seconds = $sibling.data('startSeconds');
					siblingModel.end_seconds = $sibling.data('endSeconds');

					if (direction === RESIZE_DIRECTION.LEFT) {
						// If resizing the left handle, find the sibling to the
						// left (the sibling with a start_seconds lower than
						// the current item).
						if (siblingModel.start_seconds < scope.instance.start_seconds) {
							if (!nearestSibling || siblingModel.start_seconds > nearestSibling.start_seconds) {
								nearestSibling = siblingModel;
							}
						}
					} else {
						// If resizing the right handle, find the sibling to the
						// right (the sibling with a start_seconds greater than
						// the current item).
						if (siblingModel.start_seconds > scope.instance.start_seconds) {
							if (!nearestSibling || siblingModel.start_seconds < nearestSibling.start_seconds) {
								nearestSibling = siblingModel;
							}
						}
					}
				}

				// Apply limits imposed by adjacent sibling.
				if (nearestSibling) {
					if (direction === RESIZE_DIRECTION.LEFT) {
						scope.draggingLimits.x.min =
							nearestSibling.end_seconds + MINIMUM_TAG_SEPARATION;

					} else {
						scope.draggingLimits.x.max =
							nearestSibling.start_seconds - MINIMUM_TAG_SEPARATION;
					}
				} else {
					if (direction === RESIZE_DIRECTION.LEFT) {
						scope.draggingLimits.x.min = 0;
					} else {
						scope.draggingLimits.x.max = scope.video.duration;
					}
				}

				// Apply limits imposed by minimum tag sizes.
				if (direction === RESIZE_DIRECTION.LEFT) {
					scope.draggingLimits.x.max =
						scope.instance.end_seconds - MINIMUM_TAG_DURATION;
				} else {
					scope.draggingLimits.x.min =
						scope.instance.start_seconds + MINIMUM_TAG_DURATION;
				}
			}

			function onEndResize($event) {
				$document.off('mousemove', onResizingMouseMove);
				$document.off('mouseup', onEndResize);

				if (!!scope.video.archived_at) {
					return;
				}

				// Notify the timeline that the user has finished interacting
				// with the tag so it can bind it's UI events again.
				scope.timelineCtrl.onTagInteractionEnd();

				// Update state
				scope.resizing = false;
				scope.resizeDirection = null;

				// Let the timeline controller know are no longer resizing.
				scope.timelineCtrl.setResizingTag(false);

				// Save the changed model
				scope.ctrl.save();

				scope.$digest();
			}

			function scheduleControlsShow() {
				if (!!scope.video.archived_at) {
					return;
				}

				$timeout.cancel(scope.hoverTimer);
				scope.hoverTimer = $timeout(showControls, 1000);
			}

			function scheduleControlsHide() {
				if (!!scope.video.archived_at) {
					return;
				}

				$timeout.cancel(scope.hoverTimer);
				scope.hoverTimer = $timeout(hideControls, 1000);
			}

			function showControls() {
				if (!!scope.video.archived_at) {
					return;
				}

				scope.controlsVisible = true;
			}

			function hideControls() {
				// Cancel any scheduled controls showing.
				$timeout.cancel(scope.hoverTimer);
				scope.controlsVisible = false;
			}

			function showFineTuneControls(side, $event) {
				var controls,
					controlsWidth,
					offset;

				// If any of the following are true, then we don't want to show
				// the fine-tune controls:
				//
				// 	1. Video is archived.
				// 	2. User is dragging to resizing a tag.
				// 	3. User is already dragging the timeline's playhead.
				if (!!scope.video.archived_at ||
					scope.timelineCtrl.isResizingTag() ||
					scope.timelineCtrl.isDraggingPlayhead()) {
					return;
				}

				controls = element
					.find('.gd-video-timeline-tag-instance__fine-tune');

				// Hide the normal controls
				hideControls();

				// Ensure controls wrapper has a is visible before we
				// measure it's width.
				controls.addClass('gd-hide-override');

				controlsWidth = controls.width();
				offset = -(controlsWidth / 2) + 2;
				offset = offset - (
					parseInt(controls.css('paddingLeft'), 10) +
					parseInt(controls.css('paddingRight'), 10)
				);

				// Position the fine tune controls
				if (side === 'end') {
					controls.css({
						'display': '',
						'left': '',
						'right': offset + 'px'
					});
				} else {
					controls.css({
						'display': '',
						'left': offset + 'px',
						'right': ''
					});
				}

				controls.removeClass('gd-hide-override');

				scope.fineTuneSide = side;
				scope.fineTuneVisible = true;
			}

			function onResizeHandleMouseEnter(end, $event) {
				if (scope.timelineCtrl.isResizingTag()) {
					return;
				}

				showFineTuneControls(end);

				// Prevent the event from bubbling up to the tag instance and
				// causing the expand/delete controls from showing.
				$event.stopPropagation();
			}

			function onFineTuneMouseLeave(evnt) {
				if (scope.timelineCtrl.isResizingTag()) {
					return;
				}
			}

			function onTagMouseenter() {
				if (scope.timelineCtrl.isResizingTag()) {
					return;
				}

				scheduleControlsShow();
			}

			function onTagMouseleave() {
				if (scope.timelineCtrl.isResizingTag()) {
					return;
				}

				scheduleControlsHide();
				hideFineTuneControls();
			}

			function hideFineTuneControls() {
				scope.fineTuneSide = null;
				scope.fineTuneVisible = false;

				// Unfreeze the timeline if the
				if (!scope.timelineCtrl.isResizingTag()) {
					scope.timelineCtrl.onTagInteractionEnd();
				}
			}
		}
	}
}());

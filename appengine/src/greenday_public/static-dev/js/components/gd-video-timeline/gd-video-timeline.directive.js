(function () {
	angular.module('components.videoTimeline')
		.directive('gdVideoTimeline', videoTimeline);

	/** @ngInject */
	function videoTimeline($document, $timeout, $window, floatingElementService, ToastService, UserService, EventService, TimedVideoCommentThreadModel, TimedVideoCommentReplyModel, VideoTagModel, VideoTagInstanceModel, TIMELINE_PX_PER_SECOND, hotkeys) {
		var directive = {
			templateUrl: 'components/gd-video-timeline/gd-video-timeline.html',
			restrict: 'E',
			controller: controller,
			controllerAs: 'ctrl',
			link: link,
			scope: {
				projectId: '@',
				player: '=',
				video: '='
			}
		};

		return directive;

		/** @ngInject */
		function controller($scope) {
			var ctrl = this,
				$windowEl = angular.element($window),
				hotkeyConfig = [{
					combo: ['shift+1', 'shift+2', 'shift+3', 'shift+4', 'shift+5', 'shift+6', 'shift+7', 'shift+8', 'shift+9'],
					description: 'Quick add video tag',
					callback: function (event) {
						var keyCode = event.keyCode,
							index = keyCode - 49, // numkeys start from 49
							tag = ctrl.videoTags[index];

						ctrl.addTagInstance(tag);
					}
				}];

			// Hotkeys
			angular.forEach(hotkeyConfig, function (config) {
				hotkeys.add(config);
			});

			$scope.$on('$destroy', function () {
				angular.forEach(hotkeyConfig, function (config) {
					hotkeys.del(config.combo);
				});
			});

			/////////////////
			// Controller API
			/////////////////

			/////////////////
			// Controller API
			/////////////////
			ctrl.createThread = function () {
				UserService.getUser().then(function (user) {
					$scope.newThread = TimedVideoCommentThreadModel.createInstance({
						project_id: $scope.video.project_id,
						start_seconds: $scope.player.state.currentTime,
						text: '',
						youtube_id: $scope.video.youtube_id,
						user: {
							first_name: user.first_name,
							last_name: user.last_name,
							profile_img_url: user.profile_img_url
						}
					});
				});
			};

			ctrl.onTagInteractionStart = function () {
				$scope.disableJumpToTime = true;
				$scope.player.api.freeze();
			};

			ctrl.onTagInteractionEnd = function () {
				// We need to ensure that the disabling of the jumpToTime
				// doesn't occur until all events have been processed (after
				// they have bubbled), otherwise the disableJumpToTime get gets
				// reset too early.
				$timeout(function () {
					$scope.disableJumpToTime = false;
					if ($scope.player.state.frozenTime) {
						$scope.player.api.unfreeze();
					}
				});
			};

			ctrl.isDraggingPlayhead = function () {
				return $scope.draggingPlayhead;
			};

			ctrl.setResizingTag = function (value) {
				$scope.resizingTag = !!value;
			};

			ctrl.isResizingTag = function () {
				return $scope.resizingTag;
			};

			/////////////////
			// Scope API
			/////////////////
			$scope.component = '<gd-video-timeline>';
			$scope.newThread = null;
			$scope.draggingPlayhead = false;
			$scope.disableJumpToTime = false;
			$scope.resizingTag = false;

			/**
			 * Calculates the timed tag duration as a percentage of the
			 * video duration.
			 *
			 * @param  {Object} tagInstance
			 *         The tag for which to compute the width.
			 *
			 * @return {Number}
			 *         The width of the tag as a percentage of the duration
			 *         of the video which the tag is associated with.
			 */
			ctrl.getTagInstanceWidth = function(tagInstance) {
				return (tagInstance.end_seconds * TIMELINE_PX_PER_SECOND) -
					(tagInstance.start_seconds * TIMELINE_PX_PER_SECOND) + 'px';
			};

			/**
			 * Calculates the time duration/offset of the given time as a
			 * percentage of the video duration.
			 *
			 * @param  {Number} time
			 *         The time, in seconds, to compute the percentage of.
			 *
			 * @return {Number}
			 *         The offset of the playhead it's current point.
			 */
			ctrl.getTimeOffset = function(time) {
				var timePercentageElapsed = time / $scope.video.duration * 100;

				return timePercentageElapsed;
			};

			ctrl.addTagInstance = function (projectTag) {
				var tagInstance = VideoTagInstanceModel.createInstance({
					project_id: $scope.video.project_id,
					youtube_id: $scope.video.youtube_id,
					video_tag_id: projectTag.id
				});

				if ($scope.player) {
					tagInstance.start_seconds = $scope.player.state.currentTime;
				}

				ToastService.show('Adding "' + projectTag.project_tag.name + '"', {
					hideDelay: 0
				});

				tagInstance
					.DSCreate()
					.then(function () {
						ToastService.show('Tag added');
					}, function (response) {
						ToastService.show('Error: Could not add tag "' +
							projectTag.project_tag.name + '" to the video: ' +
							response.data.error.message);
					});
			};

			/////////////////
			// Setup
			/////////////////
			if (!$scope.video.archived_at) {
				// Only load comments if the video is not archived.

				TimedVideoCommentThreadModel.bindAll({
					project_id: $scope.video.project_id,
					youtube_id: $scope.video.youtube_id
				}, $scope, 'ctrl.commentThreads');

				// Fetch comments.
				TimedVideoCommentThreadModel.findAll({
						project_id: $scope.video.project_id,
						c_video_id: $scope.video.c_id
					}).then(angular.noop, function () {
						ToastService.showError('There was an error loading comments for this video.', 0);
					});
			}

			// Tags
			VideoTagModel.findAll({
				project_id: $scope.video.project_id,
				c_video_id: $scope.video.c_id
			});

			VideoTagModel.bindAll({
				project_id: $scope.video.project_id,
				c_video_id: $scope.video.c_id,
				orderBy: 'project_tag.name'
			}, $scope, 'ctrl.videoTags');

			$timeout(function() {
				EventService.pull(commentsListener, 'TIMED_VIDEO_COMMENT');
				EventService.pull(commentReplyListener, 'TIMED_VIDEO_COMMENT_REPLY');
			});

			/////////////////
			// Private functions
			/////////////////
			function destroy() {
				$windowEl.off('resize.gdVideoTimeline');
			}

			function commentsListener(message) {
				var thread;

				switch (message.event.event_type) {
					case 'CREATED':
						// Backend doesn't pass youtube_id, we need to inject it.
						message.model.youtube_id = $scope.video.youtube_id;

						thread = TimedVideoCommentThreadModel.createInstance(message.model);
						TimedVideoCommentThreadModel.inject(thread);

						break;

					case 'UPDATED':
						thread = TimedVideoCommentThreadModel.get(message.model.id);
						TimedVideoCommentThreadModel.inject(thread);

						break;

					case 'DELETED':
						thread = TimedVideoCommentThreadModel.get(message.event.object_id);
						TimedVideoCommentThreadModel.eject(message.event.object_id);

						break;

					default:
						return;
				}
			}

			function commentReplyListener(message) {
				var reply;

				switch (message.event.event_type) {
					case 'CREATED':
						reply = TimedVideoCommentReplyModel.createInstance(message.model);
						TimedVideoCommentReplyModel.inject(reply);

						break;

					case 'UPDATED':
						reply = TimedVideoCommentReplyModel.get(message.model.id);
						TimedVideoCommentReplyModel.inject(reply);

						break;

					case 'DELETED':
						reply = TimedVideoCommentReplyModel.get(message.event.object_id);
						TimedVideoCommentReplyModel.eject(reply.id);

						break;

					default:
						return;
				}
			}
		}

		/** @ngInject */
		function link(scope, element) {
			var playerApi,
				timelineOffset,
				timelineWidth,
				wasPlaying,
				$timeline = element.find('.gd-video-timeline__timeline'),
				$playhead = element
					.find('.gd-video-timeline__playhead-wrapper')
					.add('.gd-video-timeline__playhead-container');


			element.addClass('gd-video-timeline');

			/////////////////
			// DOM events
			/////////////////
			$playhead.on('mousedown', onPlayheadMouseDown);

			/////////////////
			// Scope API
			/////////////////
			scope.createThreadPopup = null;

			scope.jumpToTime = function ($event) {
				// Failsafe against player not being ready.
				if (!scope.player || !scope.player.$ytPlayerApi) {
					return;
				}

				// Don't jump to time if it's been disabled by a child component.
				if (scope.disableJumpToTime) {
					return;
				}

				// Calculate the percentage time at the clicked coordinate.
				var $timeline = element.find('.gd-video-timeline__timeline'),
					seekTime,
					startPercent,
					timelineOffset = $timeline.offset(),
					timelineXPx = $event.pageX - timelineOffset.left,
					timelineWidth = $timeline.width();

				// Calculate seek-to time as a percentage of the
				// video's duration.
				startPercent = timelineXPx / timelineWidth * 100;

				// Convert percentage into seconds
				seekTime = scope.video.duration * (startPercent / 100);

				// Ensure we call our version of the seekTo API so that our
				// local player state gets updated as well as YouTube internal
				// player state.
				scope.player.api.seekTo(seekTime);
			};

			/////////////////
			// Scope events
			/////////////////
			scope.$on('$destroy', function () {
				$playhead.off('mousedown', onPlayheadMouseDown);
				$document.off('mousemove', onPlayheadDragged);
				$document.off('mouseup', onPlayheadMouseUp);
			});

			/////////////////
			// Scope watchers
			/////////////////
			scope.$watch('player.state.isPlaying', function (nv, ov) {
				if (nv !== ov) {
					element.toggleClass('is-playing', nv);
				}
			});

			// When we have a new local comment, show the popup.
			scope.$watch('newThread', function (nv, ov) {
				if (nv && nv !== ov) {
					$timeout(function () {
						var $trigger = element.find('.js-placeholder-comment-btn');

						scope.createThreadPopup = floatingElementService.show(
							'gd-timed-comment-popup', {
							'scope': scope,
							'trigger': $trigger,
							'positioning': {
								'alignTo': 'top center',
								'alignEdge': 'bottom center',
								'position': 'outside',
								'gaps': {
									'y': 10
								}
							},
							'attributes': {
								'mode': 'CREATE',
								'thread': 'newThread'
							}
						});

						scope.createThreadPopup.promise.then(function(thread) {
							// TODO: open timed-comment-popup for new thread

							// Reset the temporary newThread as it's either been
							// saved or cancelled
							scope.newThread = null;
						});
					});
				}
			});

			/////////////////
			// Function definitions
			/////////////////
			function onPlayheadMouseDown($event) {
				element.addClass('is-scrubbing');

				// Allow the mouseup to occur anywhere on the document to release
				// the playhead grab.
				$document.on('mouseup', onPlayheadMouseUp);
				$document.on('mousemove', onPlayheadDragged);

				playerApi = scope.player.$ytPlayerApi;

				// We can't guarantee we have instantiated the YT api here.
				if (playerApi) {
					wasPlaying = playerApi.getPlayerState() === 1 ? true : false;
					playerApi.pauseVideo();
				}

				scope.draggingPlayhead = true;

				// Grab the position and width of the timeline so we can
				// calculate the relative mouse position in the drag handler.
				timelineOffset = $timeline.offset();
				timelineWidth = $timeline.width();

				scope.$digest();
			}

			function onPlayheadMouseUp($event) {
				element.removeClass('is-scrubbing');

				if (wasPlaying) {
					playerApi.playVideo();
				}

				scope.draggingPlayhead = false;

				$document.off('mouseup', onPlayheadMouseUp);
				$document.off('mousemove', onPlayheadDragged);

				scope.$digest();
			}

			function onPlayheadDragged($event) {
				var x = $event.pageX - timelineOffset.left;
				var y = $event.pageY - timelineOffset.top;
				var newPlayheadPercentage;
				var newPlayheadSeconds;

				if (!scope.player || !scope.player.$ytPlayerApi) {
					return;
				}

				// Convert the x offset into a percentage of the timeline width
				newPlayheadPercentage = (x / timelineWidth) * 100;

				// Convert the playhead time to seconds and apply it to the
				// video.
				newPlayheadSeconds =
					(scope.video.duration / 100) * newPlayheadPercentage;

				scope.player.api.seekTo(newPlayheadSeconds, true);

				scope.$digest();
			}
		}
	}
}());

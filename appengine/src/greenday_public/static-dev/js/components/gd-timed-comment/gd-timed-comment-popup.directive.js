(function () {
	angular.module('components.timedComment')
		.directive('gdTimedCommentPopup', timedCommentPopup);

	/** @ngInject */
	function timedCommentPopup($timeout, $analytics, $filter, ToastService, UserService, TimedVideoCommentThreadModel, TimedVideoCommentReplyModel, staticFileUrlService) {
		var directive = {
			templateUrl: 'components/gd-timed-comment/gd-timed-comment-popup.html',
			restrict: 'E',
			controller: controller,
			controllerAs: 'timedCommentPopupCtrl',
			require: ['gdTimedCommentPopup', '?^gdPopupElement'],
			link: link,
			scope: {
				'mode': '@',
				'thread': '='
			}
		};

		return directive;

		/** @ngInject */
		function controller($scope, $element, $attrs) {
			var ctrl = this;

		}

		function link(scope, element, attrs, ctrls) {
			var ctrl = ctrls[0],
				popupCtrl = ctrls[1];

			/////////////////
			// Scope API
			/////////////////
			scope.$watchCollection('thread.replies', function () {
				if (popupCtrl) {
					$timeout(function () {
						popupCtrl.reposition();
					});
				}
			});

			// Scope properties
			scope.defaultProfileImgUrl = staticFileUrlService.getFileUrl('img/gplus-default-s30.png');

			scope.component = '<gd-timed-comment-popup>';
			scope.state = {
				mode: scope.mode,
				newComment: null
			};

			/**
			 * Status indicator for when we are submitting the add reply form.
			 * @type {Boolean}
			 */
			scope.submitting = false;

			/**
			 * Status indicator for when we are deleting the thread.
			 * @type {Boolean}
			 */
			scope.deleting = false;

			// Scope functions
			scope.addComment = addComment;
			scope.cancel = cancel;
			scope.deleteThread = deleteThread;

			/////////////////
			// Initialisation
			/////////////////

			// Put the user object on the scope so we can access the avatar and
			// other bits needed for the popup.
			UserService.getUser().then(function (user) {
				scope.user = user;
			});

			// Focus the last input so the user can style typing straight away.
			$timeout(function () {
				element.find('input').last().focus();
			});

			/////////////////
			// Private functions
			/////////////////

			/**
			 * TODO: Add automatic link-ifying of hyperlinks found in the user
			 * submitted content parameter. This should probably be done in some
			 * sort of debounced watch (or filter, but that might be slow).
			 */
			function addComment(content) {
				var add = TimedVideoCommentReplyModel.create({
					thread_id: scope.thread.id,
					text: content
				});

				scope.submitting = true;

				add.then(function () {
					var durationFilter = $filter('duration'),
						duration = durationFilter(Math.round(scope.thread.start_seconds));

					$analytics.eventTrack('add reply', {
						category: 'video theatre',
						label: 'on ' + scope.thread.youtube_id + ' at ' + duration + ': ' + content
					});
					scope.state.newComment = '';

					// Schedule a reposition for the popup. We need to perform
					// this in a timeout because we need the reposition to
					// be called after Angular has updated the DOM as a result
					// of the add promise completing.
					$timeout(function () {
						if (popupCtrl) {
							popupCtrl.reposition();
						}
					});

				}, function(response) {
					ToastService.showError('Error: ' + response.data.error.message, 0);
				}).finally(function () {
					scope.submitting = false;
				});
			}

			function cancel() {
				if (popupCtrl) {
					popupCtrl.close();
				}
			}

			function deleteThread() {
				var promise;

				scope.deleting = true;

				promise = TimedVideoCommentThreadModel.destroy(scope.thread.id);
				promise.then(function () {
					if (popupCtrl) {
						popupCtrl.close();
					}
				}).finally(function () {
					scope.deleting = false;
				});

				return promise;
			}
		}
	}
}());

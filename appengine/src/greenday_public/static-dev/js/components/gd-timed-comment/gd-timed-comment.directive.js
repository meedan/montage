(function() {
	angular.module('components.timedComment')
		.directive('gdTimedComment', timedComment);

	/** @ngInject */
	function timedComment($timeout, UserService, ToastService, staticFileUrlService) {

		var directive = {
			restrict: 'E',
			templateUrl: 'components/gd-timed-comment/gd-timed-comment.html',
			scope: {
				'comment': '=',
				'thread': '=',
				'mode': '='
			},
			controller: controller,
			controllerAs: 'timedCommentCtrl',
			require: ['gdTimedComment', '?^mdContent'],
			link: link
		};

		return directive;

		/** @ngInject */
		function controller($scope, $element, $attrs) {
			this.editReply = function () {
				$scope.editing = true;

				// Set the temporary editing text to the comment value so it can
				// be edited without overwriting the comment.text model data (So
				// that we can revert changes if the user clicks "Cancel").
				$scope.data.editingText = $scope.comment.text;
			};

			this.cancelEditing = function () {
				$scope.editing = false;
			};

			this.save = function () {
				// If there were no changes don't bother making an API request
				if ($scope.comment.text === $scope.data.editingText) {
					return;
				}

				$scope.saving = true;

				var save = $scope.comment.DSSave();

				save.then(function (response) {
					$scope.editing = false;
				}, function (response) {
					ToastService.showError('Error: ' + response.data.error.message, 0);
				}).finally(function () {
					$scope.saving = false;
				});
			};

			this.deleteReply = function () {
				var	promise;

				$scope.deleting = true;

				promise = $scope.comment.DSDestroy().finally(function () {
					$scope.deleting = false;
				});
			};
		}

		function link(scope, element, attrs, ctrls) {
			var timedCommentCtrl = ctrls[0],
				mdContentCtrl = ctrls[1];

			/////////////////
			// Scope API
			/////////////////

			// TODO: Move this to a computed field once we introduce UserModel
			scope.defaultProfileImgUrl = staticFileUrlService.getFileUrl('img/gplus-default-s30.png');

			scope.component = '<gd-timed-comment>';
			scope.element = element;

			/**
			 * Status variable indicating if the comment is in edit mode.
			 * @type {Boolean}
			 */
			scope.editing = false;

			/**
			 * Temporary model used for when the user is editing the comment.
			 * We need this as we can't edit the models text value directly
			 * as we need to allow them to cancel changes they've made in
			 * the textarea.
			 *
			 * @type {String || null}
			 */
			scope.data = {
				editingText: null
			};

			/**
			 * Status variable indicating if an asynchronous delete operation
			 * is in progress.
			 *
			 * @type {Boolean}
			 */
			scope.deleting = false;

			/**
			 * Status variable indicating if an asynchronous save operation
			 * is in progress.
			 *
			 * @type {Boolean}
			 */
			scope.saving = false;

			/**
			 * Data and functionality we need to forward onto the floating menu.
			 * @type {Object}
			 */
			scope.menuData = {
				editReply: function () {
					timedCommentCtrl.editReply();
				},
				deleteReply: function () {
					timedCommentCtrl.deleteReply();
				},
				save: function () {
					timedCommentCtrl.save();
				},
				// don't show delete for the root comment
				showDelete: scope.comment.id !== scope.thread.id
			};

			/////////////////
			// Scope watchers
			/////////////////

			// FIXME: We should make sure that when clicking "Edit" for one
			// comment, any other comments which are currently in edit mode
			// get taken out of edit mode (discarding changes).
			scope.$watch('editing', function (nv, ov) {
				var $actions,
					$comment,
					$textarea,
					textareaBorderWidth,
					commentHeight;

				if (angular.isDefined(nv) && nv !== ov) {
					if (nv === true) {
						$actions = element.find('.gd-timed-comment__actions');
						$comment = element.find('.gd-timed-comment__comment');
						$textarea = element.find('.gd-multiline-field');

						// Make the textarea initially the size of the value
						commentHeight = $comment.height();
						textareaBorderWidth = parseInt(
							$textarea.css('border-bottom-width'), 10);

						$textarea.height(commentHeight + textareaBorderWidth);

						// Focus the textarea
						$textarea.focus();

						// Once Angular has updated the DOM and made the
						// textarea visible, scroll to the top of the comment.
						// FIXME: We should probably scroll the mdContent such
						// that the "Cancel" and "Save" actions are visible,
						// rather than just scrolling to the top of the comment.
						// With the current behaviour the action buttons won't
						// be visible if the comment is longer than the
						// mdContent is high.
						$timeout(scrollToComment);
					}

					// Clear the temporary comment model to discard changes
					if (nv === false) {
						scope.data.editingText = null;
					}
				}
			});

			/*
			scope.$watch('data.editingText', function (nv) {
			});
			*/

			/////////////////
			// Initialisation
			/////////////////

			UserService.getUser().then(function (user) {
				scope.user = user;
			});

			/////////////////
			// Private functions
			/////////////////
			function scrollToComment() {
				var mdContentOffset,
					scrollOffset;

				mdContentOffset = mdContentCtrl.$element.offset().top;
				scrollOffset = element.offset().top - mdContentOffset;

				mdContentCtrl.$element.get(0).scrollTop = scrollOffset;
			}
		}
	}

})();

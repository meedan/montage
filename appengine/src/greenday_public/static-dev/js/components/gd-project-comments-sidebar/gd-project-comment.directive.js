(function () {
	angular.module('components')
		.directive('gdProjectComment', gdProjectComment);

	/** @ngInject */
	function gdProjectComment($timeout, UserService, ToastService, DialogService) {
		var directive = {
			restrict: 'E',
			templateUrl: 'components/gd-project-comments-sidebar/gd-project-comment.html',
			link: link,
			controller: controller,
			controllerAs: 'ctrl',
			require: ['^gdProjectComment', '^gdProjectCommentsSidebar'],
			scope: {
				comment: '='
			}
		};
		return directive;

		function controller($scope) {
			var ctrl = this;

			ctrl.resetComment = function () {
				ctrl.newComment = {
					text: $scope.comment.text
				};
			};

			ctrl.cancelEdit = function () {
				ctrl.resetComment();
				ctrl.editing = false;
			};

			ctrl.editComment = function () {
				ctrl.editing = true;

				$timeout(function () {
					ctrl.element
						.find('.gd-pc-sidebar__add-reply-input')
						.get(0)
						.focus();
				}, 50);
			};

			ctrl.deleteComment = function () {
				var msg;

				if (!$scope.comment.thread_id) {
					msg = 'Are you sure you want to delete this comment and all its replies?';
				} else {
					msg = 'Are you sure you want to delete this comment?';
				}
				DialogService
					.confirm(null, msg)
					.then(function () {
						ToastService.show('Deleting comment...', false, { hideDelay: 0 });
						ctrl.pcSidebarCtrl.isBusy = true;
						$scope.comment
							.DSDestroy()
							.then(function () {
								ctrl.pcSidebarCtrl.isBusy = false;
								ToastService.show('Comment deleted');
							});
					});
			};

			ctrl.save = function () {
				ToastService.show('Saving comment...', false, { hideDelay: 0 });
				ctrl.pcSidebarCtrl.isBusy = true;
				$scope.comment.text = ctrl.newComment.text;
				$scope.comment.DSSave().then(function () {
					ctrl.resetComment();
					ctrl.editing = false;
					ctrl.pcSidebarCtrl.isBusy = false;
					ToastService.show('Comment saved');
				});
			};

			ctrl.resetComment();
		}

		function link(scope, element, attrs, controllers) {
			var commentCtrl = controllers[0];

			commentCtrl.pcSidebarCtrl = controllers[1];

			commentCtrl.element = element;

			UserService
				.getUser()
				.then(function (user) {
					scope.user = user;
				});

			scope.menuData = {
				editComment: function () {
					commentCtrl.editComment();
				},
				deleteComment: function () {
					commentCtrl.deleteComment();
				},
				save: function () {
					commentCtrl.save();
				}
			};
		}
	}

}());

(function () {
	angular.module('components')
		.directive('gdProjectCommentThread', gdProjectCommentThread);

	/** @ngInject */
	function gdProjectCommentThread($timeout, $analytics, UserService, ProjectCommentReplyModel, staticFileUrlService) {
		var directive = {
				restrict: 'E',
				templateUrl: 'components/gd-project-comments-sidebar/gd-project-comment-thread.html',
				link: link,
				controller: controller,
				controllerAs: 'threadCtrl',
				require: ['^gdProjectCommentThread', '^gdProjectCommentsSidebar'],
				scope: {
					thread: '=',
					projectId: '='
				}
			},
			analyticsCategory = 'project comments sidebar';

		return directive;

		function link(scope, element, attrs, controllers) {
			var threadCtrl = controllers[0],
				pcSidebarCtrl = controllers[1];

			scope.defaultProfileImgUrl = staticFileUrlService.getFileUrl('img/gplus-default-s40.png');
			scope.pcSidebarCtrl = pcSidebarCtrl;

			threadCtrl.replyInput = element.find('.gd-pc-sidebar__add-reply-input').get(0);

			// limit the number of replies shown
			threadCtrl.collapse();

			threadCtrl.resetComment();

			UserService
				.getUser()
				.then(function (user) {
					scope.user = user;
				});
		}

		function controller($scope) {
			var threadCtrl = this;

			threadCtrl.addComment = function () {
				$scope.pcSidebarCtrl.isBusy = true;
				ProjectCommentReplyModel
					.create(threadCtrl.newComment)
					.then(function () {
						$analytics.eventTrack('add reply', {
							category: analyticsCategory,
							label: threadCtrl.newComment.text
						});
						$scope.pcSidebarCtrl.isBusy = false;
						threadCtrl.resetComment();
					});
			};

			threadCtrl.resetComment = function () {
				threadCtrl.newComment = ProjectCommentReplyModel.createInstance({
					project_id: $scope.projectId,
					thread_id: $scope.thread.id,
					text: ''
				});
			};

			threadCtrl.expand = function () {
				if (!threadCtrl.expanded) {
					threadCtrl.expanded = true;
					$scope.maxRepliesToShow = 9999999;
					$timeout(function () {
						threadCtrl.replyInput.focus();
					}, 50);
				}
			};

			threadCtrl.collapse = function () {
				threadCtrl.expanded = false;
				// Only show the latest reply on collapse
				$scope.maxRepliesToShow = -1;
			};
		}
	}

}());

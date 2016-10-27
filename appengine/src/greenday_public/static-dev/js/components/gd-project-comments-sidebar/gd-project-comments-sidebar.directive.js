(function () {
	angular.module('components')
		.directive('gdProjectCommentsSidebar', pcSidebar);

	/** @ngInject */
	function pcSidebar($timeout, $analytics, UserService, EventService, ProjectCommentModel, ProjectCommentReplyModel, staticFileUrlService) {
		var directive = {
				restrict: 'E',
				templateUrl: 'components/gd-project-comments-sidebar/gd-project-comments-sidebar.html',
				link: link,
				controller: controller,
				controllerAs: 'pcSidebarCtrl',
				require: ['^gdProjectCommentsSidebar'],
				scope: {
					projectId: '='
				}
			},
			analyticsCategory = 'project comments sidebar';

		return directive;

		function link(scope, element, attrs, controllers) {
			var pcSidebarCtrl = controllers[0],
				trackOpenEvent = function () {
					$analytics.eventTrack('open', {
						category: analyticsCategory,
						label: 'sidebar open'
					});
				},
				unWatchIsOpen = scope.$watch('pcSidebarCtrl.isOpen', function (isOpen) {
					if (isOpen) {
						pcSidebarCtrl.openedOnce = true;
						trackOpenEvent();
						lazyLink();
						unWatchIsOpen();
					}
				});

			scope.defaultProfileImgUrl = staticFileUrlService.getFileUrl('img/gplus-default-s40.png');

			function lazyLink() {
				var commentInput = null;

				pcSidebarCtrl.resetComment();
				pcSidebarCtrl.getComments();

				scope.$watch('projectId', function (projectId, oldId) {
					if (angular.isDefined(projectId) && projectId !== oldId) {
						pcSidebarCtrl.getComments();
					}
				});

				scope.$watch('pcSidebarCtrl.isOpen', function (isOpen) {
					if (isOpen) {
						trackOpenEvent();
						$timeout(function () {
							if (!commentInput) {
								commentInput = element.find('.gd-pc-sidebar__add-update-input').get(0);
							}
							commentInput.focus();
						}, 600);
					}
				});

				UserService
					.getUser()
					.then(function (user) {
						scope.user = user;
					});

				EventService.pull(pcSidebarCtrl.listener, 'PROJECT_COMMENT');
			}
		}

		function controller($scope) {
			var pcSidebarCtrl = this;

			pcSidebarCtrl.openedOnce = false;

			pcSidebarCtrl.resetComment = function () {
				pcSidebarCtrl.newComment = ProjectCommentModel.createInstance({
					project_id: $scope.projectId,
					text: ''
				});
			};

			pcSidebarCtrl.addComment = function () {
				pcSidebarCtrl.isBusy = true;
				ProjectCommentModel
					.create(pcSidebarCtrl.newComment)
					.then(function () {
						$analytics.eventTrack('add comment', {
							category: analyticsCategory,
							label: pcSidebarCtrl.newComment.text
						});
						pcSidebarCtrl.isBusy = false;
						pcSidebarCtrl.resetComment();
					});
			};

			pcSidebarCtrl.getComments = function () {
				var projectFilter = { project_id: $scope.projectId };
				pcSidebarCtrl.isBusy = true;
				if (pcSidebarCtrl.commentUnbinder) {
					pcSidebarCtrl.commentUnbinder();
				}
				pcSidebarCtrl.commentUnbinder = ProjectCommentModel
					.bindAll(projectFilter, $scope, 'pcSidebarCtrl.threads');
				ProjectCommentModel
					.findAll(projectFilter)
					.then(function () {
						pcSidebarCtrl.isBusy = false;
					});
			};

			pcSidebarCtrl.listener = function (message) {
				var thread;

				switch (message.event.event_type) {
					case 'CREATED':
						thread = ProjectCommentModel.createInstance(message.model);
						ProjectCommentModel.inject(thread);

						break;
					case 'UPDATED':
						thread = ProjectCommentModel.get(message.model.id);
						ProjectCommentModel.inject(thread);

						break;
					case 'DELETED':
						thread = ProjectCommentModel.get(message.event.object_id);
						ProjectCommentModel.eject(thread);

						break;
					case 'PROJECTREPLYCOMMENTCREATED':
						var reply = ProjectCommentReplyModel.createInstance(message.model);
						ProjectCommentReplyModel.inject(reply);

						// FIXME: Update thread UPDATED attribute when backend exposes it.
						// This will fix thread ordering.
						break;
					default:
						return;
				}
			};
		}
	}
}());

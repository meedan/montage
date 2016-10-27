(function () {
	angular.module('components')
		.directive('gdOnlineCollaborators', onlineCollaboratorsDirective);

	/** @ngInject */
	function onlineCollaboratorsDirective(EventService, OnlineCollaboratorModel, staticFileUrlService) {
		var directive = {
			templateUrl: 'components/gd-online-collaborators/gd-online-collaborators.html',
			restrict: 'E',
			scope: {
				projectId: '=?'
			},
			controller: controller,
			controllerAs: 'ctrl',
			link: link
		};

		return directive;

		function link(scope, element, attrs, ctrl) {
			scope.$watch('projectId', ctrl.updateCollaborators);

			scope.defaultProfileImgUrl = staticFileUrlService.getFileUrl('img/gplus-default-s30.png');
		}

		function controller($scope) {
			var ctrl = this;

			ctrl.updateCollaborators = function (newProjectId) {
				// FIXME: We show people also in the same project who aren't
				// necessarily looking at the same video as you (if you are on a video
				// page). Does this make sense? Should we show people "in the project"
				// or "looking at the same thing as me"?
				if (ctrl.collaboratorUnbinder) {
					ctrl.collaboratorUnbinder();
					OnlineCollaboratorModel.ejectAll();
				}

				if (angular.isDefined(newProjectId)) {
					var projectFilter = {
						project_id: newProjectId
					};
					ctrl.collaboratorUnbinder = OnlineCollaboratorModel.bindAll(
						projectFilter, $scope, 'collaborators');

					OnlineCollaboratorModel.findAll(projectFilter);

					EventService.pull(ctrl.listener, 'USER');
				}
			};

			ctrl.listener = function (message) {
				var user;

				switch (message.event.event_type) {
					case 'PROJECTCOLLABORATORONLINE':
						if (message.model) {
							user = OnlineCollaboratorModel.createInstance(message.model);

							user.project_id = message.event.project_id;
							user.video_id = message.event.video_id;

							OnlineCollaboratorModel.inject(user);
						}

						break;
					case 'PROJECTCOLLABORATOROFFLINE':
						if (message.model) {
							OnlineCollaboratorModel.eject(message.model.id);
						}
						break;
					default:
						return;
				}
			};
		}
	}
})();

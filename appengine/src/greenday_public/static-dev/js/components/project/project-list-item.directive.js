(function () {
	angular.module('components')
		.directive('projectListItem', projectListItem);

	/** @ngInject */
	function projectListItem($timeout, $analytics, ProjectModel, DialogService, ToastService) {
		var directive = {
			link: link,
			controller: controller,
			controllerAs: 'ctrl',
			templateUrl: 'components/project/project-list-item.html',
			restrict: 'E',
			replace: true,
			scope: {
				project: '=?',
				index: '@',
				isVisible: '=',
				onSave: '&?',
				onCancel: '&?',
				onRemove: '&?',
				userId: '@?'
			}
		};

		return directive;

		function link(scope, element, attrs) {
			if (!scope.project) {
				scope.project = {
					image_url: null
				};
			}
		}

		/** @ngInject */
		function controller($scope, $element, $attrs) {
			var ctrl = this;

			ctrl.loading = false;
			ctrl.isVisible = $scope.isVisible;
			ctrl.project = $scope.project;
			ctrl.originalProject = angular.copy(ctrl.project);
			ctrl.saveProject = saveProject;
			ctrl.removeProject = removeProject;
			ctrl.inviteAccept = inviteAccept;
			ctrl.inviteReject = inviteReject;
			ctrl.cancel = cancel;
			ctrl.modes = {
				edit: !ctrl.project.id
			};
			ctrl.imageUploaderBusy = false;
			ctrl.showInfo = false;
			ctrl.fetchedExtraInfo = false;

			$scope.$watch('isVisible', function (newVal, oldVal) {
				if (!ctrl.project.id && newVal === true) {
					ctrl.modes.edit = true;
				}
			});

			$scope.$watch('ctrl.showInfo', function (newVal, oldVal) {
				if (ctrl.project.id && newVal === true && ctrl.fetchedExtraInfo === false) {
					fetchExtraInfo();
				}
			});

			$scope.menuData = {
				ctrl: ctrl
			};

			function inviteAccept(project) {
				ToastService.show('Accepting Invite', false, { hideDelay: 0 });
				project
					.accept({ project_id: project.id })
					.then(function (project) {
						$scope.project = project;
						ToastService.update({
							content: 'You are now a collaborator on this project',
							showClose: true
						});
						ToastService.closeAfter(3000);
					}, function () {
						ToastService.update({ content: 'OOPS! Something went wrong'});
					});
			}

			function inviteReject($event, project) {
				DialogService
					.confirm($event, 'Are you sure you want to reject this invitation?')
					.then(function () {
						ToastService.show('Rejecting invitation', false, { hideDelay: 0 });
						project
							.reject()
							.then(function () {
								ToastService.update({
									content: 'You have declined to be a collaborator on this project',
									showClose: true
								});
								ToastService.closeAfter(3000);
							}, function () {
								ToastService.update({ content: 'OOPS! Something went wrong'});
							});
					});
			}

			function saveProject() {
				var promise;

				// RobC 10/04/2015 - manually set tag privacy to private by
				// default as we are removing all references to public and
				// private tags from the interfaces. All projects going forward
				// will be private.
				// TODO: Might need to remove tag privacy from the API itself at some
				// point. However, due to fluid spec at the minute we may find
				// we still need the attribute on the endpoint itself.
				ctrl.project.privacy_tags = 1;

				if (ctrl.project.id) {
					promise = ctrl.project.DSSave();
				} else {
					promise = ctrl.project.DSCreate();
					// Only track when we are creating the project
					promise.then(function () {
						$analytics.eventTrack('create', {
							category: 'project',
							label: ctrl.project.name
						});
					});
				}

				ctrl.loading = true;
				ToastService.show('Saving project', false, { hideDelay: 0 });

				promise
					.then(function () {
						ctrl.modes.edit = false;
						ToastService.update({
							content: 'Project saved',
							showClose: true
						});
						ToastService.closeAfter(3000);
						// Wait for the digest cycle to complete
						$timeout(function () {
							$scope.onSave();
						});
					}, function () {
						ToastService.update({ content: 'OOPS! Something went wrong'});
					})
					.finally(function () {
						ctrl.loading = false;
					});
			}

			function removeProject($event, project) {
				DialogService
					.confirm($event, 'Are you sure to remove this project?')
					.then(function () {
						ctrl.loading = true;
						ToastService.show('Removing project', false, { hideDelay: 0 });
						ProjectModel
							.destroy(project.id)
							.then(function () {
								ToastService.update({
									content: 'Project removed',
									showClose: true
								});
								ToastService.closeAfter(3000);
								// Wait for the digest cycle to complete
								$timeout(function () {
									$scope.onRemove();
								});
							}, function () {
								ToastService.update({ content: 'OOPS! Something went wrong'});
							})
							.finally(function () {
								ctrl.loading = false;
							});
					});
			}

			// KEEP

			ctrl.toggleKeep = toggleKeep;
			ctrl.toggleKeepService = toggleKeepService;

			ctrl.keepSettings = {
				isActive: false,
				services: {
					all: true,
					archiveOrg: true,
					archiveIs: true
				}
			};

			function toggleKeep() {
				ctrl.loading = true;
				// setTimeout(function() { // TODO: setting timeout to emulate lentghy api call — remove this
					ctrl.loading = false;
					// }, 500);
					console.log('New Keep Settings:', ctrl.keepSettings); // TODO: set Keep settings via API
			}

			function toggleKeepService(service) {

				var services = ctrl.keepSettings.services;
				ctrl.loading = true;

				// setTimeout(function() { // TODO: setting timeout to emulate lentghy api call — remove this
					if (service === 'all') {
						for (var key in services) {
							services[key] = services.all;
						}
					} else {
						if (!services.all && services.archiveIs && services.archiveOrg) {
							services.all = true;
						} else if (services[service] === false) {
							services.all = false;
						}
					}
					ctrl.loading = false;
				// }, 500);
					console.log('New Keep Settings:', ctrl.keepSettings); // TODO: set Keep settings via API

			}

			function fetchExtraInfo() {
				return ProjectModel
					.find(ctrl.project.id, {
						bypassCache: true
					})
					.then(function (project) {
						ctrl.fetchedExtraInfo = true;
					});
			}

			function cancel() {
				ctrl.project = angular.copy(ctrl.originalProject);

				if (!ctrl.project.id) {
					$scope.isVisible = false;
					$scope.onCancel();
				} else {
					ctrl.modes.edit = false;
				}
			}
		}
	}
}());

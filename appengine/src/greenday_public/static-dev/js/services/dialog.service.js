/**
 * Dialog service
 *
 */
(function () {
	angular
		.module('app.services')
		.factory('DialogService', DialogService);

	/** @ngInject */
	function DialogService ($q, $mdDialog) {
		var service = {
				confirm: confirm,
				showAddCollectionDialog: showAddCollectionDialog,
				showAddCollaboratorsDialog: showAddCollaboratorsDialog,
				showKeepSettingsDialog: showKeepSettingsDialog,
				showUserSettingsDialog: showUserSettingsDialog,
				hide: hide,
				cancel: cancel
			};

		return service;

		function confirm(e, content) {
			var dialogPromise = $mdDialog.show({
				templateUrl: 'components/modals/confirm.html',
				targetEvent: e,
				controller: confirmController,
				locals: {
					content: content
				}
			});

			return dialogPromise;
		}

		function showAddCollectionDialog(e) {
			var dialogPromise = $mdDialog.show({
				templateUrl: 'components/modals/addCollection.html',
				targetEvent: e,
				controller: addCollectionController,
				controllerAs: 'ctrl'
			});

			return dialogPromise;
		}

		function showAddCollaboratorsDialog(e) {
			var dialogPromise = $mdDialog.show({
				templateUrl: 'components/modals/addCollaborators.html',
				targetEvent: e,
				controller: addCollaboratorsController,
				controllerAs: 'ctrl'
			});

			return dialogPromise;
		}

		function showKeepSettingsDialog(e) {
			var dialogPromise = $mdDialog.show({
				templateUrl: 'components/modals/keepSettings.html',
				targetEvent: e,
				// controller: addCollaboratorsController,
				controller: keepSettingsController,
				controllerAs: 'ctrl'
			});

			return dialogPromise;
		}

		function showUserSettingsDialog(e, user) {
			var dialogPromise = $mdDialog.show({
				templateUrl: 'components/modals/userSettings.html',
				targetEvent: e,
				controller: userSettingsController,
				controllerAs: 'ctrl',
				locals: {
					user: user
				}
			});

			return dialogPromise;
		}

		/* istanbul ignore next */
		/** @ngInject */
		function confirmController($scope, content) {
			$scope.content = content;
			$scope.ok = hide;
			$scope.close = cancel;
		}

		/* istanbul ignore next */
		/** @ngInject */
		function userSettingsController($scope, user, UserService) {
			var ctrl = this;

			ctrl.user = user;

			ctrl.deleteAccount = UserService.deleteAccount;

			ctrl.ok = hide;
			ctrl.close = cancel;
		}

		/* istanbul ignore next */
		/** @ngInject */
		function addCollectionController($scope, $timeout, $analytics, PageService, CollectionModel) {
			var ctrl = this;

			ctrl.$input = $('#collectionName');

			$timeout(function() {
				ctrl.$input.focus();
			});

			ctrl.collection = CollectionModel.createInstance({
				project_id: PageService.getPageData().projectId
			});

			ctrl.addCollection = function () {
				PageService.startLoading();
				CollectionModel
					.create(ctrl.collection)
					.then(function () {
						$analytics.eventTrack('add collection', {
							category: 'project sidebar',
							label: ctrl.collection.name
						});
						ctrl.ok();
						PageService.stopLoading();
					});
			};

			ctrl.ok = hide;
			ctrl.close = cancel;
		}

		/* istanbul ignore next */
		/** @ngInject */
		function addCollaboratorsController($scope, PageService, CollaboratorService, UserService, _) {
			var ctrl = this,
				projectId = PageService.getPageData().projectId,
				projectFilter = { project_id: projectId };

			ctrl.newCollaborator = {};
			ctrl.possibleUsers = [];

			CollaboratorService
				.bindAll(projectFilter, $scope, 'ctrl.collaborators');

			// get current project collaborators.
			ctrl.getProjectCollaborators = function() {
				ctrl.isBusy = true;
				CollaboratorService
					.list(projectId)
					.then(function () {
						ctrl.isBusy = false;
					});
			};

			ctrl.getProjectCollaborators();

			// setup watcher to listen for changes to the add collaborator input
			$scope.$watch('ctrl.newCollaborator', function (newVal, oldVal) {
				if (newVal && newVal.email && newVal.email !== oldVal.email) {
					ctrl.isBusy = true;
					UserService
						.queryUserContacts(newVal.email)
						.then(function (users) {
							// filter out users already assigned to the project
							var assignedUserEmails = _.pluck(ctrl.collaborators, 'email'),
								autocompleteEmails = _.transform(users, function(result, user) {
									if (angular.isDefined(user.gd$email) && user.gd$email.length && user.gd$email[0].address) {
										result.push({
											name: user.title.$t,
											email: user.gd$email[0].address
										});
									}
								});

							ctrl.possibleUsers = _.difference(autocompleteEmails, assignedUserEmails);
						})
						.finally(function() {
							ctrl.newCollaborator.email = ctrl.newCollaborator.email.toLowerCase();
							ctrl.isBusy = false;
						});
				}
			}, true);

			ctrl.resetCollaborator = function () {
				ctrl.newCollaborator = CollaboratorService.createInstance({
					email: '',
					as_admin: false,
					project_id: projectId
				});
			};

			// method to add new collaborator
			ctrl.addCollaborator = function () {
				ctrl.isBusy = true;
				ctrl.newCollaborator.as_admin = false;
				ctrl.newCollaborator.project_id = projectId;
				CollaboratorService
					.create(ctrl.newCollaborator)
					.then(function() {
						var metadata = {
						  invitee_email: ctrl.newCollaborator.email,
						  invite_code: 'ADDACOLLABORATOR'
						};
						ctrl.resetCollaborator();
						ctrl.isBusy = false;
				});
			};

			ctrl.removeCollaborator = function (collaborator) {
				ctrl.isBusy = true;
				CollaboratorService
					.remove(collaborator.id)
					.then(function() {
						ctrl.isBusy = false;
				});
			};

			// configure modal buttons.
			ctrl.ok = hide;
			ctrl.close = cancel;

			ctrl.resetCollaborator();
		}

		function keepSettingsController($scope) { 
			console.log($scope)
			return null;
		}

		function hide() {
			$mdDialog.hide();
		}

		function cancel(reason) {
			$mdDialog.cancel(reason);
		}

	}
}());

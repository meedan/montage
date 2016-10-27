/**
 * pages.projects Module
 *
 * The project list module.
 */
(function () {
	angular
		.module('pages')
		.controller('ProjectsPageCtrl', ProjectsPageCtrl);

	/** @ngInject */
	function ProjectsPageCtrl($scope, PageService, ProjectModel, UserService, projects, EventService, hotkeys) {
		var ctrl = this;

		EventService.setVideo();

		ProjectModel.bindAll({}, $scope, 'ctrl.projects');

		ctrl.loaders = {
			project: false
		};

		ctrl.newProject = null;
		ctrl.onProjectAddCancel = onProjectAddCancel;
		ctrl.onProjectSave = onProjectSave;
		ctrl.addBlankProject = addBlankProject;

		PageService.updatePageData({
			title: 'Your projects',
			section: 'my-projects',
			loading: false
		});

		UserService.getUser().then(function (user) {
			ctrl.user = user;
		});

		UserService.getUserStats(true).then(function (userStats) {
			ctrl.userStats = userStats;
		});

		ctrl.hotkeyConfig = [{
			combo: ['ctrl+p'],
			description: 'Create new project',
			callback: function () {
				addBlankProject();
			}
		}];

		// Hotkeys
		angular.forEach(ctrl.hotkeyConfig, function (config) {
			hotkeys.add(config);
		});

		$scope.$on('$destroy', function () {
			angular.forEach(ctrl.hotkeyConfig, function (config) {
				hotkeys.del(config.combo);
			});
		});

		function onProjectAddCancel() {
			ctrl.addMode = false;
			ctrl.newProject = null;
		}

		function addBlankProject() {
			ctrl.newProject = ProjectModel.createInstance({
				privacy_tags: 2
			});
			ctrl.addMode = true;
		}

		function onProjectSave() {
			ctrl.newProject = null;
			ctrl.addMode = false;
		}
	}
}());

(function () {
	angular
		.module('app')
		.controller('AppCtrl', AppCtrl);

	/** @ngInject */
	function AppCtrl(
			$scope,
			$rootScope,
			$location,
			$timeout,
			$mdSidenav,
			$analytics,
			DialogService,
			PageService,
			UserService,
			CollectionModel,
			EventService,
			_,
			hotkeys) {
		var ctrl = this;

		UserService.getUser().then(function (user) {
			ctrl.user = user;
		});

		ctrl.page = PageService.getPageData();

		ctrl.openSideBar = function(sidebarId) {
			if (sidebarId === 'left') {
				$analytics.eventTrack('open', {
					category: 'project sidebar',
					label: 'hamburger menu'
				});
			}
			$mdSidenav(sidebarId).toggle();
		};

		ctrl.openKeepControls = function() {
			console.log("THIS");
		};

		ctrl.closeSideBar = function(sidebarId) {
			$timeout(function () {
				$mdSidenav(sidebarId).close();
			});
		};

		ctrl.showSearch = function () {
			var qs = $location.search();
			qs.searchVisible = 'true';
			$location.search(qs);
		};

		ctrl.showAddCollectionDialog = function () {
			DialogService
				.showAddCollectionDialog()
				.then(function () {
					ctrl.getCollections();
				});
		};

		ctrl.getCollections = function () {
			var projectFilter = { project_id: ctrl.page.projectId };

			if (ctrl.collectionUnbinder) {
				ctrl.collectionUnbinder();
			}

			ctrl.collectionUnbinder = CollectionModel
				.bindAll(projectFilter, $scope, 'appctrl.collections');
			CollectionModel
				.findAll(projectFilter);
		};

		ctrl.showAddCollaboratorsDialog = function (evt) {
			DialogService.showAddCollaboratorsDialog(evt);
		};

		ctrl.showKeepSettingsDialog = function (evt) {
			DialogService.showKeepSettingsDialog(evt);
		};

		ctrl.onRouteChangeUpdate = function () {
			ctrl.closeSideBar('left');
			var qs = $location.search();
			if (qs.searchVisible === 'true') {
				ctrl.searchVisible = true;
			} else {
				ctrl.searchVisible = false;
			}
		};

		function parseRouteChangeError(error) {
			var qs = {};

			if (error.reason === 'immediate_failed' || error.reason === 'popup_blocked_by_browser') {
				if ($location.path() !== '/welcome') {
					qs.next = $location.search().next || $location.url();
					$location.path('/welcome').search(qs);
				}
			} else if (error.reason === 'not_accepted_nda') {
				if ($location.path() !== '/accept-terms') {
					qs.next = $location.search().next || $location.url();
					$location.path('/accept-terms').search(qs);
				}
			} else if (error.status === 404) {
				$location.path('/404');
			} else if (error.status === 403) {
				$location.path('/403');
			}
		}

		ctrl.hotkeyConfig = [{
			combo: ['g p'],
			description: 'Go to my projects',
			callback: function () {
				$location.url('/my-projects');
			}
		}];

		// Hotkeys
		angular.forEach(ctrl.hotkeyConfig, function (config) {
			hotkeys.add(config);
		});

		$scope.$on('pagedata:changed', function ($event, pageData) {
			ctrl.page = pageData;

			$timeout(function() {
				EventService.setProject(ctrl.page.projectId);
			});

			if (ctrl.page.projectId) {
				ctrl.getCollections();
			}
		});

		$scope.$on('user:signIn:start', function ($event, user) {
			PageService.startLoading();
		});

		$scope.$on('user:signIn:failed', function ($event, response) {
			ctrl.user = null;
			ctrl.closeSideBar('left');
			PageService.stopLoading();
			parseRouteChangeError(response);
		});

		$scope.$on('user:signOut:start', function ($event, user) {
			PageService.startLoading();
		});

		$scope.$on('user:signOut:complete', function ($event, user) {
			ctrl.user = null;
			ctrl.closeSideBar('left');
			$location.url('/welcome');
		});

		$rootScope.$on('$locationChangeStart', function (event, next, current) {
			var currentBaseUrl = current.split('?')[0],
				nextBaseUrl = next.split('?')[0],
				nextBasePath = _.last(nextBaseUrl.split('/'));

			// Don't show the loading if the base urls are the same
			// e.g. only the query string is changed
			if (nextBasePath !== 'welcome' && nextBasePath !== 'accept-terms' && currentBaseUrl !== nextBaseUrl) {
				PageService.startLoading();
				UserService.getUser().then(function (user) {
					ctrl.user = user;
				});
			}
		});

		$rootScope.$on('$routeChangeError', function (evt, next, current, error) {
			parseRouteChangeError(error);
		});

		$rootScope.$on('$routeChangeSuccess', ctrl.onRouteChangeUpdate);
		$rootScope.$on('$routeUpdate', ctrl.onRouteChangeUpdate);

		// TODO: Do it nicer, Rui said so!
		ctrl.imOnWelcomePage = false;
		$scope.$watch( function(){ return $location.path();}, function(newValue){
			ctrl.imOnWelcomePage = newValue === '/welcome';
		});

	}
}());

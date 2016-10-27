/**
 * pages.welcome Module
 *
 * The welcome page module.
 */
(function () {
	angular
		.module('pages')
		.controller('AcceptNDACtrl', AcceptNDACtrl);

	/** @ngInject */
	function AcceptNDACtrl($location, PageService, UserService) {
		var ctrl = this;

		PageService.updatePageData({
			title: 'Montage',
			loading: false
		});

		UserService
			.getUser()
			.then(function (user) {
				ctrl.user = user;
				if (user.accepted_nda === true) {
					$location.path('/');
				}
			}, function (error) {
				ctrl.user = error.user;
			}).finally(function () {
				PageService.stopLoading();
			});

		ctrl.gotoStep = function (step) {
			ctrl.step = step;
		};

		ctrl.acceptNDA = function () {
			ctrl.accepting = true;
			PageService.startLoading();
			UserService
				.acceptNDA()
				.then(function (user) {
					var nextUrl = $location.search().next;
					if (!nextUrl || nextUrl === '/welcome') {
						nextUrl = '/';
					}
					$location.url(nextUrl);
				});
		};

		ctrl.gotoStep(1);
	}
}());

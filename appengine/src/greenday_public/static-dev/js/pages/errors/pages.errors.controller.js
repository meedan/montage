/**
 * pages.Error Module
 *
 * The Error page module.
 */
(function () {
	angular
		.module('pages')
		.controller('ErrorPageCtrl', ErrorPageCtrl);

	/** @ngInject */
	function ErrorPageCtrl($scope, PageService) {
		var ctrl = this;

		PageService.updatePageData({
			title: 'Montage',
			loading: false
		});

		$scope.$on('user:signIn:complete', function () {
			PageService.stopLoading();
		});

		ctrl.isBusy = false;
	}
}());

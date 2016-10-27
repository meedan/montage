/**
 * pages.legal Module
 *
 * The legal page module.
 */
(function () {
	angular
		.module('pages')
		.controller('LegalCtrl', LegalCtrl);

	/** @ngInject */
	function LegalCtrl(PageService, UserService) {
		UserService
			.getUser()
			.finally(function () {
				PageService.stopLoading();
			});

		PageService.updatePageData({
			title: 'Montage',
			loading: false
		});
	}
}());

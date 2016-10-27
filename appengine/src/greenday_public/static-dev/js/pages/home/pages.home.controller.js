/**
 * pages.home Module
 *
 * The home page module.
 */
(function () {
	angular
		.module('pages')
		.controller('HomePageCtrl', HomePageCtrl);

	/** @ngInject */
	function HomePageCtrl(PageService, user) {
		PageService.updatePageData({
			title: 'Montage',
			loading: false
		});
	}
}());

/**
 * pages.service service
 *
 */
(function () {
	angular
		.module('pages')
		.factory('PageService', PageService);

	/** @ngInject */
	function PageService ($rootScope, DS) {
		var defaultPageData = {
				title: 'Montage',
				section: '',
				subSection: '',
				loading: true
			},
			pageData = angular.copy(defaultPageData),
			service = {
				getPageData: getPageData,
				updatePageData: updatePageData,
				startLoading: startLoading,
				stopLoading: stopLoading,
				clearDataCache: clearDataCache
			};

		return service;

		function getPageData () {
			return pageData;
		}

		function updatePageData (newPageData, partial) {
			if (partial === true) {
				angular.extend(pageData, newPageData);
			} else {
				pageData = angular.extend({}, defaultPageData, newPageData);
			}
			$rootScope.$broadcast('pagedata:changed', pageData);
		}

		function startLoading () {
			$rootScope.$broadcast('pagedata:changed', pageData);
			updatePageData({loading: true}, true);
		}

		function stopLoading () {
			updatePageData({loading: false}, true);
		}

		function clearDataCache () {
			angular.forEach(Object.keys(DS.definitions), function (resourceName) {
				DS.definitions[resourceName].ejectAll();
			});
		}
	}
}());

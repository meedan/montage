(function () {
	angular.module('components')
		.directive('gdVideoBackButton', videoBackButtonDirective);

	/** @ngInject */
	function videoBackButtonDirective($location, $timeout, PageService) {
		var directive = {
			template: '<a ng-href="{{ url }}"><icon class="ic-arrow-back"></icon></a>',
			restrict: 'E',
			link: link,
			scope: {
				projectId: '@'
			}
		};

		return directive;

		/** @ngInject */
		function link(scope, element, attrs, controllers) {
			scope.url = '';

			scope.$on('pagedata:changed', function (evt, newData) {
				if (newData.projectId) {
					buildUrl(newData.projectId);
				}
			});

			function buildUrl(projectId) {
				var params = [],
					qs = $location.search(),
					url = ['project', projectId];

				if (qs.collectionId) {
					url.push('collection', qs.collectionId);
				}

				angular.forEach(qs, function (value, key) {
					if (key !== 'collectionId') {
						params.push(key + '=' + value);
					}
				});

				url = url.join('/');

				if (params.length) {
					url += '?' + params.join('&');
				}

				scope.url = url;
			}

		}
	}
}());

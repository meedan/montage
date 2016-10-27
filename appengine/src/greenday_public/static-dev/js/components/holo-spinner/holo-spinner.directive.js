(function () {
	angular.module('components')
		.directive('holoSpinner', holoSpinner);

	/** @ngInject */
	function holoSpinner() {
		var directive = {
			templateUrl: 'components/holo-spinner/holo-spinner.html',
			restrict: 'E'
		};

		return directive;
	}
}());

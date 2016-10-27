(function () {
	angular
		.module('app.filters')
		.filter('round', roundFilter);

	/** @ngInject */
	function roundFilter(moment, _) {
		return function(n) {
			return Math.round(n);
		};
	}
}());

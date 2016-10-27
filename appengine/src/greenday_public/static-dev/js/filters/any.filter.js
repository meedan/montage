(function () {
	angular
		.module('app.filters')
		.filter('any', findWhereFilter);

	/** @ngInject */
	function findWhereFilter(_) {
		return function(value, expression) {
			return _.findWhere(value, expression);
		};
	}
}());

(function() {
	angular.module('app.services')
		.factory('IdGenerator', IdGenerator);

	/** @ngInject */
	function IdGenerator() {
		var idCounter = 0;

		function generateId(prefix) {
			var id = ++idCounter;
			return String(prefix === null ? '' : prefix) + id;
		}

		return {
			generate: generateId
		};
	}
}());

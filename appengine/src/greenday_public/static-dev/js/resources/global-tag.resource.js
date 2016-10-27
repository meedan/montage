(function () {
	angular
		.module('app.resources')
		.factory('GlobalTagModel', GlobalTagModel);

	/** @ngInject */
	function GlobalTagModel(DS) {
		return DS.defineResource({
			name: 'global-tag',
			endpoint: 'tags',
			actions: {
				search: {
					method: 'GET'
				}
			}
		});
	}

}());

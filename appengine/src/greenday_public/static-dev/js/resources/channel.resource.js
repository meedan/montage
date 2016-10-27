(function () {
	angular
		.module('app.resources')
		.factory('ChannelModel', ChannelModel);

	/** @ngInject */
	function ChannelModel(DS) {
		return DS.defineResource({
			name: 'channels',
			endpoint: 'distinct_channels',
			relations: {
				belongsTo: {
					project: {
						parent: true,
						localField: 'project',
						localKey: 'project_id'
					}
				}
			}
		});
	}

}());

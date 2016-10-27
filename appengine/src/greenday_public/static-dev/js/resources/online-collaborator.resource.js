(function () {
	angular
		.module('app.resources')
		.factory('OnlineCollaboratorModel', OnlineCollaboratorModel);

	/** @ngInject */
	function OnlineCollaboratorModel(DS) {
		return DS.defineResource({
			name: 'online-collaborator',
			endpoint: 'collaborators',
			relations: {
				belongsTo: {
					project: {
						parent: true,
						localField: 'project',
						localKey: 'project_id'
					},
					video: {
						localField: 'video',
						localKey: 'video_id'
					}
				}
			}
		});
	}
}());

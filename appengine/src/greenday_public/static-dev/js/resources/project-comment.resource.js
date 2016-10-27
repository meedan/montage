(function () {
	angular
		.module('app.resources')
		.factory('ProjectCommentModel', ProjectCommentModel);

	/** @ngInject */
	function ProjectCommentModel(DS) {
		return DS.defineResource({
			name: 'projectComment',
			endpoint: 'comments',
			relations: {
				belongsTo: {
					project: {
						parent: true,
						localField: 'project',
						localKey: 'project_id'
					}
				},
				hasMany: {
					projectCommentReply: {
						localField: 'replies',
						foreignKey: 'thread_id'
					}
				}
			}
		});
	}
}());

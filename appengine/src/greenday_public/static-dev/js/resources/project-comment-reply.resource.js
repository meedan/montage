(function () {
	angular
		.module('app.resources')
		.factory('ProjectCommentReplyModel', ProjectCommentReplyModel);

	/** @ngInject */
	function ProjectCommentReplyModel(DS) {
		return DS.defineResource({
			name: 'projectCommentReply',
			endpoint: 'replies',
			relations: {
				belongsTo: {
					projectComment: {
						parent: true,
						localField: 'comment',
						localKey: 'thread_id'
					}
				}
			}
		});
	}
}());

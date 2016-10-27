(function () {
	angular
		.module('app.resources')
		.factory('VideoTagModel', VideoTagModel);

	/** @ngInject */
	function VideoTagModel(DS, getEndpoint, COMPOUND_KEY_SEPARATOR) {
		var videoTagModel = DS.defineResource({
			name: 'video-tag',
			endpoint: 'tags',
			idAttribute: 'id',
			relations: {
				belongsTo: {
					'video': {
						parent: true,
						localField: 'video',
						localKey: 'c_video_id'
					},
					'project-tag': {
						localField: 'project_tag',
						localKey: 'project_tag_id'
					}
				},
				hasMany: {
					'video-tag-instance': {
						localField: 'instances',
						foreignKey: 'video_tag_id'
					}
				}
			},
			computed: {
				c_video_id: ['project_id', 'youtube_id', function (projectId, youtubeId) {
					return projectId + COMPOUND_KEY_SEPARATOR + youtubeId;
				}],
			}
		});

		videoTagModel.getEndpoint = getEndpoint;

		return videoTagModel;
	}
}());

(function () {
	angular
		.module('app.resources')
		.factory('TimedVideoCommentThreadModel', TimedVideoCommentThreadResource)
		.factory('TimedVideoCommentReplyModel', TimedVideoCommentReplyResource)
		.constant('COMMENT_DATE_FORMAT', 'h.mma MMM Do');

	/** @ngInject */
	function TimedVideoCommentThreadResource (DS, moment, getEndpoint, VideoModel, COMPOUND_KEY_SEPARATOR, COMMENT_DATE_FORMAT) {
		var model = DS.defineResource({
			name: 'timed-video-comment-thread',
			endpoint: 'comments',
			relations: {
				belongsTo: {
					'video': {
						parent: true,
						localField: 'video',
						localKey: 'c_video_id'
					}
				},
				hasMany: {
					'timed-video-comment-reply': {
						localField: 'replies',
						foreignKey: 'thread_id'
					}
				}
			},
			computed: {
				c_video_id: ['project_id', 'youtube_id', function (projectId, videoId) {
					return projectId + COMPOUND_KEY_SEPARATOR + videoId;
				}],
				c_timeline_offset: ['c_video_id', 'start_seconds', function (videoId, startTime) {
					var video = VideoModel.get(videoId);
					return startTime / video.duration * 100;
				}],
				c_pretty_created_date: ['created', function (created) {
					var date = moment(created);
					return date.format(COMMENT_DATE_FORMAT);
				}]
			}
		});

		model.getEndpoint = getEndpoint;

		return model;
	}

	/** @ngInject */
	function TimedVideoCommentReplyResource (DS, moment, COMMENT_DATE_FORMAT) {
		return DS.defineResource({
			name: 'timed-video-comment-reply',
			endpoint: 'replies',
			relations: {
				belongsTo: {
					'timed-video-comment-thread': {
						parent: true,
						localField: 'thread',
						localKey: 'thread_id'
					}
				}
			},
			computed: {
				c_pretty_created_date: ['created', function (created) {
					var date = moment(created);
					return date.format(COMMENT_DATE_FORMAT);
				}]
			},
		});
	}
}());


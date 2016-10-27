(function () {
	angular
		.module('app.resources')
		.constant('VIDEO_TAG_INSTANCE_DEFAULT_DURATION', 5)
		.factory('VideoTagInstanceModel', VideoTagInstanceModel);

	/** @ngInject */
	function VideoTagInstanceModel(DS, VideoTagModel, VIDEO_TAG_INSTANCE_DEFAULT_DURATION) {
		var videoTagInstanceModel = DS.defineResource({
			name: 'video-tag-instance',
			endpoint: 'instances',
			relations: {
				belongsTo: {
					'video-tag': {
						parent: true,
						localField: 'tag',
						localKey: 'video_tag_id'
					}
				}
			},
			beforeCreate: function (resource, data, cb) {
				var instanceData = {};
				var defaults = {
					start_seconds: 0,
					end_seconds: VIDEO_TAG_INSTANCE_DEFAULT_DURATION
				};

				angular.extend(instanceData, defaults, data);

				// Adjust the default end time if only a start time was provided.
				if (angular.isDefined(data.start_seconds) && !angular.isDefined(data.end_seconds)) {
					instanceData.end_seconds = data.start_seconds + VIDEO_TAG_INSTANCE_DEFAULT_DURATION;
				}

				cb(null, instanceData);
			},
			afterDestroy: function (resource, data, cb) {
				var tag = VideoTagModel.get(data.video_tag_id);

				// Replicate the behaviour on the BE that happens when deleting the
				// last video tag instance. Once the last instance is deleteed, we also
				// ensure the video tag itself is removed from the frontend store.
				//
				// Note: We check if the number of instances is 1 (not 0) since the
				// count will not have been decremented until after this afterDestroy
				// hook has executed.
				if (tag && tag.instances.length === 1) {
					VideoTagModel.eject(data.video_tag_id);
				}

				cb(null, data);
			}
		});

		return videoTagInstanceModel;
	}
}());

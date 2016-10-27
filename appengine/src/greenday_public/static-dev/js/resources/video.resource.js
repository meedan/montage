(function () {
	angular
		.module('app.resources')
		.factory('VideoModel', VideoResource);

	/** @ngInject */
	function VideoResource(_, DS, DSHttpAdapter, moment, FilterUtils, API_BASE_URL, COMPOUND_KEY_SEPARATOR, getEndpoint) {

		var videoModel = DS.defineResource({
			name: 'video',
			idAttribute: 'c_id',
			relations: {
				belongsTo: {
					project: {
						parent: true,
						localField: 'project',
						localKey: 'project_id'
					}
				}
			},
			computed: {
				c_id: ['project_id', 'youtube_id', function (projectId, youtubeId) {
					return projectId + COMPOUND_KEY_SEPARATOR + youtubeId;
				}],
				c_thumbnail_url: ['youtube_id', function (youtubeId) {
					return '//i3.ytimg.com/vi/' + youtubeId + '/default.jpg';
				}],
				c_theatre_url: ['project_id', 'youtube_id', function (projectId, youtubeId) {
					return '/project/' + projectId + '/video/' + youtubeId;
				}]
			},
			methods: {
				batchUnduplicate: function (duplicateVideoIds) {
					var self = this,
						endpoint = getMethodUrl(self, 'batch-delete-duplicate-markers');

					return DSHttpAdapter
						.PUT(endpoint, {
							youtube_ids: duplicateVideoIds
						})
						.then(deserializeAndInject);
				},
				getDuplicates: function () {
					var self = this;

					return DSHttpAdapter
						.GET(getMethodUrl(self, 'duplicates'))
						.then(function (data) {
							return deserializeResponse(data);
						});
				},
				setFavourite: function (value) {
					var self = this;

					return DSHttpAdapter
						.PUT(getMethodUrl(self, 'set-favourite'), {
							value: value
						})
						.then(deserializeAndInject);
				},
				save: function () {
					var self = this,
						video = DSHttpAdapter.defaults.serialize(videoModel, self);

					return DSHttpAdapter
						.PUT(getMethodUrl(self), video)
						.then(deserializeAndInject);
				},
				setArchived: function (value) {
					var self = this,
						promise,
						unarchiveEndpoint = getMethodUrl(self, 'unarchive'),
						archiveEndpoint = [
							API_BASE_URL,
							'project', self.project_id,
							'video', 'batch-archive'
						].join('/');

					if (value === false) {
						promise = DSHttpAdapter.PUT(archiveEndpoint, {
							youtube_ids: [self.youtube_id]
						});
					} else {
						promise = DSHttpAdapter.PUT(unarchiveEndpoint);
					}

					promise.then(function (response) {
						if (response.data && response.data.videos) {
							var item = _.find(response.data.videos, {
								youtube_id: self.youtube_id
							});

							self.archived_at = item.archived_at;
						} else {
							self.archived_at = null;
						}

						// Update the project meta
						self.project.DSRefresh();
					});

					return promise;
				},
				setWatched: function (value) {
					var self = this;

					return DSHttpAdapter
						.PUT(getMethodUrl(self, 'mark-watched'), {
							value: value
						})
						.then(function (data) {

						});
				}
			},
			actions: {
				batchMarkAsDuplicate: {
					pathname: 'batch-mark-as-duplicate',
					method: 'PUT'
				},
				batchArchive: {
					pathname: 'batch-archive',
					method: 'PUT'
				},
				fetchTagList: {
					pathname: 'filter_by_tags',
					method: 'GET'
				}
			}
		});

		var getMethodUrl = function (instance, methodEndpoint) {
			var params = [
				API_BASE_URL,
				'project', instance.project_id,
				'video', instance.youtube_id
			];

			if (methodEndpoint) {
				params.push(methodEndpoint);
			}

			return params.join('/');
		};

		var deserializeAndInject = function (data) {
			return videoModel.inject(deserializeResponse(data));
		};

		var deserializeResponse = function (data) {
			return DSHttpAdapter.defaults.deserialize(videoModel, data);
		};

		// Patch getEndpoint to allow for our compound key.
		// TODO: Avoid doing this when we can override the URL in js-data in a
		// nicer way.
		videoModel.getEndpoint = getEndpoint;

		return videoModel;
	}

}());

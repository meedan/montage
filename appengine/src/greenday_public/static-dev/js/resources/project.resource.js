(function () {
	angular
		.module('app.resources')
		.factory('ProjectModel', ProjectResource);

	/** @ngInject */
	function ProjectResource(DS, DSHttpAdapter, API_BASE_URL, PageService) {
		var endpoint = 'project';

		var projectModel = DS.defineResource({
			name: endpoint,
			relations: {
				hasMany: {
					'video': {
						localField: 'videos',
						foreignKey: 'project_id'
					}
				}
			},
			methods: {
				accept: function () {
					var promise = doRequest.call(this, 'accept'),
						self = this;

					promise.then(function (data) {
						projectModel.inject(data);
					});

					return promise;
				},
				reject: function () {
					var promise = doRequest.call(this, 'reject'),
						self = this;

					promise.then(function () {
						projectModel.eject(self.id);
					});

					return promise;
				},
				addVideos: function (youtubeIds) {
					var self = this,
						params = [
							API_BASE_URL,
							'project', this.id,
							'video',
							'batch-create'
						];

					if (!angular.isArray(youtubeIds)) {
						youtubeIds = [youtubeIds];
					}

					return DSHttpAdapter
						.PUT(params.join('/'), {
							youtube_ids: youtubeIds
						})
						.then(function (data) {
							var videoCollection = PageService.getPageData().videos,
								videos = data.data.videos,
								results = data.data.items,
								result;

							if (videoCollection) {
								angular.forEach(videos, function (video, index) {
									result = results[index];
									if (results.success === true) {
										videoCollection.items.push(video);
									}
								});

								videoCollection.findAll();
							}

							// Update the project meta so we can get the correct video_count
							self.DSRefresh();

							return data.data;
						});
				}
			}
		});

		var doRequest = function (method) {
			var self = this;

			return DSHttpAdapter
				.POST([API_BASE_URL, endpoint, 'my', self.id, method].join('/'), {
					project_id: self.id
				})
				.then(function (data) {
					return DSHttpAdapter.defaults.deserialize(projectModel, data);
				});
		};

		return projectModel;
	}
}());

(function () {
	angular
		.module('app.resources')
		.factory('CollectionModel', CollectionModel);

	/** @ngInject */
	function CollectionModel($timeout, DS, DSHttpAdapter, API_BASE_URL, PageService, VideoModel, _) {
		var collectionModel = DS.defineResource({
			name: 'collection',
			relations: {
				belongsTo: {
					project: {
						parent: true,
						localField: 'project',
						localKey: 'project_id'
					}
				}
			},
			methods: {
				addVideos: function (youtubeIds) {
					var self = this,
						params = [
							API_BASE_URL,
							'project', this.project_id,
							'collection', this.id,
							'add_batch'
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
							}

							return data.data;
						});
				},
				removeVideos: function (youtubeIds) {
					var self = this,
						params = [
							API_BASE_URL,
							'project', this.project_id,
							'collection', this.id,
							'remove_batch'
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
								youtubeIds = data.config.data.youtube_ids,
								videos;

							if (videoCollection) {
								videos = _.remove(videoCollection.items, function (video) {
									return youtubeIds.indexOf(video.youtube_id) > -1;
								});
							}

							angular.forEach(videos, function (video) {
								VideoModel.eject(video.c_id);
							});
						});
				},
				moveVideo: function (moveFromVideoId, video) {
					var self = this,
						params = [
							API_BASE_URL,
							'project', this.project_id,
							'collection', this.id,
							'video', moveFromVideoId,
							'move'
						];

					return DSHttpAdapter
						.POST(params.join('/'), {
							before: false,
							sibling_youtube_id: video.youtube_id
						});
				}
			}
		});

		return collectionModel;
	}
}());

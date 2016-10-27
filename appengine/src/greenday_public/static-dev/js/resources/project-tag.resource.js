(function () {
	angular
		.module('app.resources')
		.factory('ProjectTagModel', ProjectTagModel);

	/** @ngInject */
	function ProjectTagModel(DS, DSHttpAdapter, API_BASE_URL) {
		var endpoint = 'tags',
			projectTagModel = DS.defineResource({
				name: 'project-tag',
				endpoint: endpoint,
				relations: {
					belongsTo: {
						project: {
							parent: true,
							localField: 'project',
							localKey: 'project_id'
						}
					},
					hasMany: {
						'project-tag': {
							localField: 'subTags',
							foreignKey: 'parent_id'
						}
					}
				},
				actions: {
					search: {
						method: 'GET'
					},
					merge: {
						method: 'POST'
					}
				},
				methods: {
					move: function (parentTagId) {
						var self = this;

						return DSHttpAdapter
							.PUT([API_BASE_URL, 'project', self.project_id, endpoint, self.id, 'move'].join('/'), {
								parent_tag_id: parentTagId
							})
							.then(function (data) {
								var tag = DSHttpAdapter.defaults.deserialize(ProjectTagModel, data);
								projectTagModel.inject(tag);
								return tag;
							});
					}
				}
			});

		return projectTagModel;
	}
}());

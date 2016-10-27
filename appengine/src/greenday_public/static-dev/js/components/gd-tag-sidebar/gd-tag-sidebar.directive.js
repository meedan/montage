(function () {
	angular.module('components')
		.directive('gdTagSidebar', tagSidebar);

	/** @ngInject */
	function tagSidebar($analytics, ProjectTagModel, GlobalTagModel, treefyService, _, PageService, DialogService, ToastService) {
		var directive = {
				restrict: 'E',
				templateUrl: 'components/gd-tag-sidebar/gd-tag-sidebar.html',
				link: link,
				controller: controller,
				controllerAs: 'tagSidebarCtrl',
				require: ['^gdTagSidebar'],
				scope: {
					projectId: '='
				}
			},
			analyticsCategory = 'project tag sidebar';

		return directive;

		function link(scope, element, attrs, controllers) {
			var tagSidebarCtrl = controllers[0];

			// Disable autocompleting global tags for now
			// scope.$watch('newTag.name', tagSidebarCtrl.searchTags);
			scope.$watch('tagSidebarCtrl.isOpen', tagSidebarCtrl.trackOpenEvent);
			scope.$watch('projectId', tagSidebarCtrl.updateProjectId);
			scope.$watchCollection('tagSidebarCtrl.projectTags', tagSidebarCtrl.updateProjectTags);

			scope.$on('onTagClick', function (evt, tag) {
				tag.selected = true;
			});
			scope.$on('onTagDrop', tagSidebarCtrl.onTagDrop);
			scope.tagTemplateUrl = 'components/gd-tag-sidebar/tag-template.html';
			scope.tagController = tagSidebarCtrl.tagController;
		}

		function controller($scope) {
			var tagSidebarCtrl = this;

			tagSidebarCtrl.isBusy = false;

			tagSidebarCtrl.reset = function () {
				$scope.newTag = {
					name: '',
					projectId: PageService.getPageData().projectId
				};
			};

			tagSidebarCtrl.reset();

			tagSidebarCtrl.trackOpenEvent = function (isOpen) {
				if (isOpen) {
					$analytics.eventTrack('open', {
						category: analyticsCategory,
						label: 'sidebar open'
					});
				}
			};

			tagSidebarCtrl.onTagDrop = function (evt, tagId, parentTagId) {
				tagSidebarCtrl.moveTag(tagId, parentTagId);
			};

			tagSidebarCtrl.moveTag = function (tagId, parentTagId) {
				// Prevent dropping tags on themselves
				if (parentTagId !== tagId) {
					var tagModel = ProjectTagModel.get(tagId);
					tagSidebarCtrl.isBusy = true;

					tagModel
						.move(parentTagId)
						.then(function () {
							$analytics.eventTrack('move tag', {
								category: analyticsCategory,
								label: tagModel.name
							});
							tagSidebarCtrl.updateProjectTags(tagSidebarCtrl.projectTags);
						}, function(response) {
							ToastService.showError('Error: ' + response.data.error.message, 0);
						})
						.finally(function () {
							tagSidebarCtrl.isBusy = false;
						});
				}
			};

			tagSidebarCtrl.updateProjectId = function (projectId) {
				if (projectId) {
					$scope.newTag.project_id = projectId;
					if (tagSidebarCtrl.tagUnbinder) {
						tagSidebarCtrl.tagUnbinder();
					}
					tagSidebarCtrl.tagUnbinder = ProjectTagModel
						.bindAll({ project_id: $scope.projectId }, $scope, 'tagSidebarCtrl.projectTags');
					ProjectTagModel
						.findAll({ project_id: $scope.projectId });
				}
			};

			tagSidebarCtrl.updateProjectTags = function (newTags, oldTags) {
				if (newTags && !angular.equals(newTags, oldTags)) {
					var treefiedTags = treefyService.treefy(tagSidebarCtrl.projectTags, 'subTags', 'parent_id', 'id');
					$scope.tags = _.filter(treefiedTags, function (tag) {
						return !tag.parent_id;
					});
				}
			};

			tagSidebarCtrl.searchTags = function (query, oldQuery) {
				if (query && !angular.equals(query.toLowerCase(), oldQuery.toLowerCase())) {
					tagSidebarCtrl.isBusy = true;
					GlobalTagModel
						.search({
							params: {
								project_id: $scope.newTag.project_id,
								q: query
							}
						})
						.then(function (data) {
							var tags = data.data;
							$scope.autoCompleteTags = tags.global_tags;
							tagSidebarCtrl.isBusy = false;
						});
				}
			};

			tagSidebarCtrl.addTag = function (tag) {
				if (tag.name) {
					var projectId = PageService.getPageData().projectId,
						tagModel = ProjectTagModel.createInstance(tag),
						promise;

					tagModel.project_id = projectId;

					if (tag.id) {
						promise = ProjectTagModel.save(tag.id);
					} else {
						promise = ProjectTagModel.create(tagModel);
						promise.then(function () {
							$analytics.eventTrack('add tag', {
								category: analyticsCategory,
								label: tagModel.name
							});
						});
					}

					tagSidebarCtrl.isBusy = true;

					promise
						.then(function() {
							ToastService.show('Tag added');
							tagSidebarCtrl.reset();
						}, function (response) {
							ToastService.showError('Error: ' + response.data.error.message, 0);
						})
						.finally(function () {
							tagSidebarCtrl.isBusy = false;
						});
				}
			};

			tagSidebarCtrl.tagController = function ($scope) {
				$scope.menuData = {
					editTag: editTag,
					removeTag: removeTag
				};

				$scope.cancelEdit = cancelEdit;
				$scope.saveTag = saveTag;

				function editTag () {
					$scope.originalModel = angular.copy($scope.ngModel);
					$scope.editMode = true;
				}

				function removeTag (evt) {
					DialogService
						.confirm(evt, 'Are you sure to remove this tag from the project?')
						.then(function () {
							var tagId = $scope.ngModel.id;

							tagSidebarCtrl.isBusy = true;

							ProjectTagModel
								.destroy(tagId)
								.then(function () {
									ToastService.show('Tag removed');
								}, function (response) {
									ToastService.error(response);
								})
								.finally(function () {
									tagSidebarCtrl.isBusy = false;
								});
						});
				}

				function cancelEdit () {
					$scope.ngModel = angular.copy($scope.originalModel);
					$scope.editMode = false;
				}

				function saveTag (tagData) {
					ProjectTagModel
						.update(tagData.id, tagData)
						.then(function () {
							$scope.editMode = false;
							ToastService.show('Tag updated');
						}, function (response) {
							ToastService.error(response);
						})
						.finally(function () {
							tagSidebarCtrl.isBusy = false;
						});
				}
			};
		}

	}
}());

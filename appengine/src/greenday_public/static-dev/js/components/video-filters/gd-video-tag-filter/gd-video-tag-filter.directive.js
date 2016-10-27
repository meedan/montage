(function () {
	angular.module('components')
		.directive('gdVideoTagFilter', videoTagFilter);

	/** @ngInject */
	function videoTagFilter($filter, ProjectTagModel, treefyService, _) {
		var directive = {
			templateUrl: 'components/video-filters/gd-video-tag-filter/gd-video-tag-filter.html',
			restrict: 'E',
			scope: {
				ngModel: '=',
				project: '=?'
			},
			link: link,
			require: ['^gdVideoFilter', '^gdVideoTagFilter', '^ngModel'],
			controller: controller,
			controllerAs: 'tagFilterCtrl'
		};

		return directive;

		function link(scope, element, attrs, controllers) {
			var filterCtrl = controllers[0],
				tagFilterCtrl = controllers[1],
				ngModelCtrl = controllers[2];

			scope.filterCtrl = filterCtrl;
			scope.ngModelCtrl = ngModelCtrl;

			scope.$on('onTagClick', function ($event, tag) {
				toggleTag(tag.id);
				tagFilterCtrl.update();
			});

			scope.$watch('ngModel', tagFilterCtrl.onModelUpdate);
			scope.$watchCollection('tagFilterCtrl.cleanTags', function () {
				tagFilterCtrl.onModelUpdate(scope.ngModel);
			});
		}

		function controller($scope) {
			var tagFilterCtrl = this,
				filterObj = {};

			tagFilterCtrl.tagTemplateUrl = 'components/video-filters/gd-video-tag-filter/gd-video-tag-template.html';

			if ($scope.project) {
				filterObj = { project_id: $scope.project.id };
			}

			if (tagFilterCtrl.cleanTagsUnbinder) {
				tagFilterCtrl.cleanTagsUnbinder();
			}

			if (tagFilterCtrl.allTagsUnbinder) {
				tagFilterCtrl.allTagsUnbinder();
			}

			tagFilterCtrl.cleanTagsUnbinder = ProjectTagModel
				.bindAll(angular.extend({}, filterObj, {parent_id: null}), $scope, 'tagFilterCtrl.cleanTags');
			tagFilterCtrl.allTagsUnbinder = ProjectTagModel
				.bindAll(filterObj, $scope, 'tagFilterCtrl.allTags');
			ProjectTagModel
				.findAll(filterObj);

			tagFilterCtrl.update = function () {
				var markedTags;
				markedTags = getMarkedTags(tagFilterCtrl.allTags);
				$scope.ngModelCtrl.$setViewValue(_.pluck(markedTags, 'id').join(','));

				tagFilterCtrl.markedTags = markedTags;

				$scope.filterCtrl.setTitle({
					items: markedTags,
					titleKey: 'name',
					prefix: 'Tagged with',
					offset: 2,
					conjunctive: 'and',
					separator: ','
				});
			};

			tagFilterCtrl.onModelUpdate = function (newVal, oldVal) {
				if (tagFilterCtrl.cleanTags && tagFilterCtrl.cleanTags.length && !angular.equals(newVal, oldVal)) {
					var tagIdValues = newVal ? newVal.split(',') : [];

					angular.forEach(tagIdValues, function (tagIdValue) {
						var tagId = parseInt(tagIdValue, 10),
							state = (tagId > 0) ? 1 : -1,
							tag;

						tagId = Math.abs(tagId);

						tag = ProjectTagModel.get(tagId);

						if (tag) {
							tag.state = state;
						}
					});

					tagFilterCtrl.update();
				}
			};

			tagFilterCtrl.deselectAll = function () {
				angular.forEach(tagFilterCtrl.allTags, function (tag) {
					tag.state = 0;
				});
				tagFilterCtrl.update();
			};
		}

		function toggleTag(tagId) {
			// States:
			// 0 for not selected at all
			// 1 for selected
			// -1 for excluded
			var tag = ProjectTagModel.get(tagId),
				tagState = tag.state || 0;

			tagState++;

			// cycle between states one-way
			if (tagState > 1) {
				tagState = -1;
			}

			setTagState(tag, tagState);
		}

		function setTagState(tag, state) {
			tag.state = state;
			if (tag.subTags.length > 0) {
				angular.forEach(tag.subTags, function(tag) {
					setTagState(tag, state);
				});
			}
		}

		function getMarkedTags(tags) {
			var markedTags = [];
			angular.forEach(tags, function (tag) {
				if (tag.state === 1) {
					markedTags.push({
						id: tag.id.toString(),
						name: tag.name
					});
				} else if (tag.state === -1) {
					markedTags.push({
						id: '-' + tag.id,
						name: 'not ' + tag.name
					});
				}
			});
			return markedTags;
		}

	}
}());

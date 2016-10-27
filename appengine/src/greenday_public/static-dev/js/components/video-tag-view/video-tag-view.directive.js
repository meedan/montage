(function () {
	angular.module('components')
		.directive('videoTagView', videoTagView);

	/** @ngInject */
	function videoTagView($timeout, _, PageService) {
		var directive = {
			templateUrl: 'components/video-tag-view/video-tag-view.html',
			restrict: 'E',
			scope: {
				tags: '='
			},
			require: ['^videoTagView'],
			link: link,
			controller: controller,
			controllerAs: 'ctrl'
		};

		return directive;

		function link(scope, element, attrs, controllers) {
			var ctrl = controllers[0];

			scope.$watch('tags', function (newTags) {
				if (newTags) {
					ctrl.updateTags(newTags);
				}
			});
		}

		function controller($scope, $element, $attrs) {
			var ctrl = this;

			ctrl.initialised = false;
			ctrl.maxItemsVisible = 6;
			ctrl.projectId = PageService.getPageData().projectId;

			ctrl.toggleTag = function (tag) {
				if (tag.limit === ctrl.maxItemsVisible) {
					tag.limit = tag.instanceCount;
					tag.expanded = true;
				} else {
					$timeout(function () {
						tag.limit = ctrl.maxItemsVisible;
					}, 500);
					tag.expanded = false;
				}
			};

			ctrl.updateTags = function (tags) {
				angular.forEach(tags, function (tag) {
					var tagVideos = _.pluck(tag.instances, 'youtube_id'),
						uniqueVideos = _.uniq(tagVideos);

					tag.expanded = false;
					tag.videoCount = uniqueVideos.length;
					tag.instanceCount = tag.instances.length;
					tag.hiddenInstanceCount = tag.instanceCount - ctrl.maxItemsVisible;
					tag.limit = ctrl.maxItemsVisible;
				});

				ctrl.initialised = true;

				$scope.tagList = tags;
			};
		}
	}
}());

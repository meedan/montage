(function () {
	angular.module('components')
		.directive('gdTagAutocompletePopup', tagAutocompletePopup);

	/** @ngInject */
	function tagAutocompletePopup() {
		var directive = {
			templateUrl: 'components/gd-tag-autocomplete/gd-tag-autocomplete-popup.html',
			restrict: 'E',
			controller: controller,
			controllerAs: 'ctrl',
			link: link,
			scope: {
				'query': '@',
				'highlightedIndex': '=',
				'highlightedSection': '=',
				'showPopup': '=',
				'player': '=',
				'tags': '=',
				'video': '=',
				'onFreeTextClicked': '&?',
				'onTagClicked': '&?',
				'excludeTags': '@'
			}
		};

		return directive;

		/** @ngInject */
		function controller($scope, $analytics, ToastService, ProjectTagModel, VideoTagModel, VideoTagInstanceModel) {
			var ctrl = this;
			var lastQuery = null;

			ctrl.globalTagsPromise = null;

			ctrl.createNewVideoTag = function (def) {
				var create,
					newTag = VideoTagModel.createInstance({
						project_id: $scope.video.project_id,
						youtube_id: $scope.video.youtube_id
					});

				console.warn('gd-tag-autocomplete-popup.directive.js: createNewVideoTag()');

				if (ProjectTagModel.is(def)) {
					newTag.global_tag_id = def.global_tag_id;
					newTag.project_tag_id = def.id;
				} else {
					// def is not a Project Tag Model, so probably a definition for a
					// new tag.
					newTag.name = def.name;
				}

				create = newTag.DSCreate();

				ToastService.show('Creating tag "' + def.name + '"', false, {
					hideDelay: 0
				});

				create.then(function(data) {
					ctrl.createTagInstance(data);
					$analytics.eventTrack('add tag', {
						category: 'video theatre',
						label: def.name
					});
				}, function (response) {
					ToastService.showError('Error: ' + response.data.error.message, 0);
				});
			};

			ctrl.createTagInstance = function (tag) {
				console.warn('gd-tag-autocomplete-popup.directive.js: createTagInstance()');

				// FIXME: Add the new tag to the videos tag list immediately on the UI
				// while saving in the background.
				//
				// FIXME: Add error handling.
				var create = VideoTagInstanceModel.create({
					video_tag_id: tag.id,
					start_seconds: $scope.player.state.currentTime
				});

				ToastService.show('Adding tag to video', false, {
					hideDelay: 0
				});

				create.then(function () {
					ToastService.show('Tag added');
				}, function (response) {
					ToastService.showError('Error: ' + response.data.error.message, 0);
				});
			};
		}

		/** @ngInject */
		function link(scope, element, attrs, ctrl) {

			element.addClass('gd-tag-autocomplete-popup');
			element.attr('layout', 'vertical');

			/////////////////
			// Scope API
			/////////////////
			scope.loading = false;

			scope.freeTextClicked = function (query) {
				var tag = { name: query };
				if (angular.isDefined(attrs.onFreeTextClicked)) {
					scope.onFreeTextClicked()(tag);
				} else {
					ctrl.createNewVideoTag(tag);
				}
			};

			scope.tagClicked = function (tag) {
				if (angular.isDefined(attrs.onTagClicked)) {
					scope.onTagClicked()(tag);
				} else {
					ctrl.createNewVideoTag(tag);
				}
			};

			/////////////////
			// Scope watchers
			/////////////////

			/////////////////
			// Scope events
			/////////////////
			scope.$on('$destroy', destroy);

			/////////////////
			// Setup
			/////////////////

			/////////////////
			// Private functions
			/////////////////
			function destroy() {
				console.log('<gd-tag-autocomplete-popup> $destoy');
			}
		}
	}
}());

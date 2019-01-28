(function () {
	angular.module('components.videoTimeline')
		.directive('gdVideoTimelineTagLabel', videoTimelineTagLabel);

	/** @ngInject */
	function videoTimelineTagLabel(_, $timeout, $mdDialog, ToastService, floatingElementService, ProjectTagModel, VideoTagModel) {

		var directive = {
			templateUrl: 'components/gd-video-timeline/gd-video-timeline-tag-label.html',
			restrict: 'E',
			controller: controller,
			controllerAs: 'ctrl',
			link: link,
			require: ['^gdVideoTimeline'],
			scope: {
				player: '=',
				tag: '=',
				video: '='
			}
		};

		return directive;

		/** @ngInject */
		function controller($scope, $element, $attrs, $transclude, VideoTagModel, VideoTagInstanceModel) {
			var ctrl = this;

			/////////////////
			// Controller API
			/////////////////
			ctrl.addTagInstance = function () {
				if (!!$scope.video.archived_at) {
					return;
				}

				$scope.gdVideoTimelineCtrl.addTagInstance($scope.tag);
			};

			ctrl.enableEditing = function () {
				$scope.tag.newName = $scope.tag.project_tag.name;
				$scope.tag.oldName = $scope.tag.project_tag.name;
				$scope.editing = true;

				// Highlight the text
				$timeout(function () {
					$element.find('input').focus().select();
				});

				ctrl.showAutocompletePopup();
			};

			ctrl.finishEditing = function () {
				var saving;

				// Don't do anything if the name wasn't actaully changed.
				if ($scope.tag.project_tag.name === $scope.tag.newName) {
					return;
				}

				$scope.busy = true;

				// Use update instead of save so that the updated name only get's
				// injected into the store once the save completes.
				saving = ProjectTagModel.update($scope.tag.project_tag_id, {
					name: $scope.tag.newName
				});

				ToastService.show('Saving tag');

				saving.then(function () {
					$scope.editing = false;
					$scope.tag.newName = '';
					ToastService.show('Tag Saved');
				}, function(response) {
					// Handle tag name already exists on video (tag merge).
					if (response.data.error.error_code === 1000) {
						var dupeTagId = parseInt(response.data.error.message.match(/{(\d+)}/)[1]);

						ToastService.hide();

						// Show the merge dialog
						$mdDialog.show({
							templateUrl: 'components/gd-video-timeline/tag-merge-dialog/components.gd-video-timeline.tag-merge.html',
							controller: 'TagMergeDialogCtrl',
							controllerAs: 'ctrl',
							locals: {
								projectId: $scope.video.project_id,
								video: $scope.video,
								mergingFromTag: $scope.tag,
								mergingToTagId: dupeTagId
							}
						}).then(function () {
							// Merge successful. The tag which was renamed
							// will have it's row automatically disappear.
							$scope.busy = false;
						}, function () {
							// Merge cancelled.
							$scope.busy = false;

							// Highlight the text
							$timeout(function () {
								$element.find('input').focus().select();
							});
						});
					} else {
						ToastService.showError('Error: ' + response.data.error.message, 0);

						ctrl.cancelEditing();

						$scope.busy = false;
					}
				});

				saving.finally(function () {
					ctrl.hidePopup();
				});
			};

			ctrl.cancelEditing = function () {
				$scope.editing = false;

				ctrl.hidePopup();

				// Reset the name
				$scope.tag.project_tag.name = $scope.tag.oldName;
				delete $scope.tag.oldName;
				delete $scope.tag.newName;
			};

			ctrl.removeTagRow = function () {
				var remove;

				$scope.busy = true;

				remove = VideoTagModel.destroy($scope.tag.id)
					.finally(function () {
						$scope.busy = false;
					});

				// TODO: Eject instances from store once tag is removed?

				return remove;
			};

			ctrl.checkKey = function($event) {
				if ($event.which === 27) {
					ctrl.cancelEditing();
				}
			};

			ctrl.showAutocompletePopup = function() {
				$scope.autocompletePopup = floatingElementService.show(
					'gd-tag-autocomplete-popup', {
						'scope': $scope,
						'trigger': $element,
						'backdrop': false,
						'positioning': {
							'alignTo': 'top right',
							'alignEdge': 'top left',
							'position': 'outside',
							'gaps': {
								'x': 10,
								'y': 0
							}
						},
						'attributes': {
							'query': '{{ tag.newName }}',
							'tags': 'results',
							'highlighted-index': 'highlightedIndex',
							'highlighted-section': 'highlightedSection',
							'player': 'player',
							'show-popup': 'true',
							'video': 'video',
							'on-free-text-clicked': 'renameTag',
							'on-tag-clicked': 'renameTag',
							'exclude-tags': '{{ [tag.id] }}'
						}
					});
			};

			ctrl.hidePopup = function() {
				floatingElementService.hide($scope.autocompletePopup.id);
 			};

 			ctrl.renameTag = function(tagName) {
 				if (_.isObject(tagName)) {
 					tagName = tagName.name;
 				}

 				$scope.tag.newName = tagName;
 				ctrl.finishEditing();
 			};
		}

		function link(scope, element, attrs, ctrl) {
			/////////////////
			// Scope API
			/////////////////
			scope.busy = false;
			scope.tagResults = {};
			scope.gdVideoTimelineCtrl = ctrl[0];

			scope.renameTag = ctrl.renameTag;

			var videoTags = VideoTagModel.filter({
				project_id: scope.video.project_id,
				c_video_id: scope.video.c_id
			});

			ProjectTagModel.bindAll({
				project_id: scope.video.project_id
			}, scope, 'results');
		}
	}
}());

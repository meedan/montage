(function () {
	angular.module('components')
		.directive('gdTagAutocomplete', tagAutocomplete);

	/** @ngInject */
	function tagAutocomplete(_, $compile, $timeout, $rootScope, floatingElementService, ProjectTagModel, VideoTagModel, hotkeys) {
		var directive = {
			templateUrl: 'components/gd-tag-autocomplete/gd-tag-autocomplete.html',
			restrict: 'E',
			controller: controller,
			controllerAs: 'ctrl',
			link: link,
			require: ['ngModel', 'gdTagAutocomplete'],
			scope: {
				'player': '=',
				'video': '='
			}
		};

		return directive;

		/** @ngInject */
		function controller($scope, $element, $attrs, $transclude) {
			var ctrl = this,
				hotkeyConfig = [{
					combo: ['t'],
					description: 'Add new tag',
					callback: function (event, hotkey) {
						$scope.showPopup();
					}
				}];

			// Hotkeys
			angular.forEach(hotkeyConfig, function (config) {
				hotkeys.add(config);
			});

			$scope.$on('$destroy', function () {
				angular.forEach(hotkeyConfig, function (config) {
					hotkeys.del(config.combo);
				});
			});
		}

		/** @ngInject */
		function link(scope, element, attrs, controllers) {
			var ngModelCtrl = controllers[0];
			var gdTagAutocompleteCtrl = controllers[1];

			element.addClass('gd-tag-autocomplete');

			/////////////////
			// Private variables
			/////////////////
			var HIGHLIGHTED_CLASS = 'is-highlighted',
				compileFn,
				$input = element.find('input'),
				$compiledPopup,
				$popup;

			// DEBUGGING
			window.highlightNextItem = highlightNextItem;
			window.highlightPrevItem = highlightPrevItem;
			window.selectCurrentItem = selectCurrentItem;

			/////////////////
			// Scope API
			/////////////////
			scope.query = null;
			scope.showPopup = showPopup;
			scope.hidePopup = hidePopup;

			scope.highlightedSection = 'recent';
			scope.highlightedIndex = 0;

			/////////////////
			// Scope watchers
			/////////////////
			scope.$watch('query', function (newQuery, oldQuery) {
				// Ensure the recent tags section becomes highlighted if no
				// query is present.

				if (newQuery && newQuery !== oldQuery) {
					if (!newQuery) {
						scope.highlightedSection = 'recent';
						scope.highlightedIndex = 0;
					} else if (!oldQuery && newQuery) {
						scope.highlightedSection = 'create';
						scope.highlightedIndex = 0;
					}
				}
			});

			/////////////////
			// Scope events
			/////////////////
			scope.$on('$destroy', destroy);

			/////////////////
			// Setup
			/////////////////

			// Bind DOM Events.

			// Prevent any interactions with this directive from closing the
			// autocomplete popup.
			element.on('click', function (evnt) {
				evnt.stopPropagation();
			});

			// Setup the autocomplete behaviour.
			element.on('keydown', onKeyDown);

			/////////////////
			// Private functions
			/////////////////
			function bindBodyHandler() {
				// Ensure we don't have double bindings.
				unbindBodyHandler();

				// Ensure any click away from this directive causes the popup to be
				// closed.
				$('body').on('click.gdTagAutocomplete', function (evnt) {
					scope.$apply(function () {
						hidePopup();
					});
				});
			}

			function unbindBodyHandler() {
				$('body').off('click.gdTagAutocomplete');
			}

			function destroy() {
				$input.off('focus', showPopup);
				element.off('keydown', onKeyDown);
			}

			function showPopup() {
				var videoTags = VideoTagModel.filter({
					project_id: scope.video.project_id,
					c_video_id: scope.video.c_id
				});

				ProjectTagModel.bindAll({
					project_id: scope.video.project_id,
					where: {
						id: {
							'notIn': _.pluck(videoTags, 'project_tag_id')
						}
					}
				}, scope, 'results');

				scope.popup = floatingElementService.show(
					'gd-tag-autocomplete-popup', {
						'scope': scope,
						'trigger': element,
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
							'query': '{{ query }}',
							'tags': 'results',
							'highlighted-index': 'highlightedIndex',
							'highlighted-section': 'highlightedSection',
							'player': 'player',
							'show-popup': 'showPopup',
							'video': 'video'
						}
					});

				bindBodyHandler();

				// We must defer the focus call until the input becomes visible
				// once the digest is complete as calling focus on a hidden
				// input does not work.
				$timeout(function () {
					element.find('.gd-tag-autocomplete__input').focus();
				});
			}

			function hidePopup() {
				unbindBodyHandler();

				floatingElementService.hide(scope.popup.id);
				scope.popup = null;
				scope.query = null;
			}

			function onKeyDown(evt) {
				scope.$apply(function () {

					// Up arrow
					if (evt.which === 38) {
						highlightPrevItem();
					}

					// Down arrow
					else if (evt.which === 40) {
						highlightNextItem();
					}

					// Enter
					else if (evt.which === 13) {
						// Defer this until the current digest ends as the click
						// will call ng-click start it's own digest cycle.
						$timeout(selectCurrentItem);
					}

					// Esc
					else if (evt.which === 27) {
						element.trigger('focusout');
					}

				});
			}

			function selectCurrentItem() {
				// Trigger action for the highlighted item
				scope.popup.element.find('.' + HIGHLIGHTED_CLASS).trigger('click');

				// Reset query
				scope.query = null;
			}

			// FIXME: This is not working properly.
			function highlightNextItem() {
				var sectionData = scope.tagResults[scope.highlightedSection];

				scope.highlightedIndex = scope.highlightedIndex + 1;

				// If there is no user query we only show recent tags
				if (!scope.query) {
					scope.highlightedIndex = scope.highlightedIndex % sectionData.length;
				} else {
					if (scope.highlightedSection === 'create') {
						scope.highlightedSection = 'project';
						scope.highlightedIndex = 0;
					} else if (scope.highlightedIndex >= sectionData.length) {
						// Move to the next section
						if (scope.highlightedSection === 'project') {
							scope.highlightedSection = 'global';
							scope.highlightedIndex = 0;
						} else if (scope.highlightedSection === 'global') {
							scope.highlightedSection = 'create';
							scope.highlightedIndex = 0;
						}
					}
				}
			}

			function highlightPrevItem() {
				var sectionData = scope.tagResults[scope.highlightedSection];

				scope.highlightedIndex = scope.highlightedIndex - 1;

				// If there is no user query we only show recent tags
				if (!scope.query) {
					if (scope.highlightedIndex === -1) {
						scope.highlightedIndex = sectionData.length - 1;
					}
				} else {
					if (scope.highlightedSection === 'create' && scope.highlightedIndex === -1) {
						scope.highlightedSection = 'global';
						scope.highlightedIndex = scope.tagResults.global.length - 1;
					} else if (scope.highlightedSection === 'project' && scope.highlightedIndex === -1) {
						scope.highlightedSection = 'create';
						scope.highlightedIndex = 0;
					} else if (scope.highlightedSection === 'global' && scope.highlightedIndex === -1) {
						scope.highlightedSection = 'project';
						scope.highlightedIndex = scope.tagResults.project.length - 1;
					}
				}
			}
		}
	}
}());

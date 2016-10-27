(function () {
	angular.module('components')
		.directive('oneSearchResultItem', oneSearchResultItem);

	/** @ngInject */
	function oneSearchResultItem($timeout, $compile) {
		var directive = {
			templateUrl: 'components/one-search/one-search-result-item.html',
			restrict: 'EA',
			scope: {
				video: '=',
				project: '=',
				collection: '='
			},
			link: link
		};
		return directive;

		function link (scope, element, attrs) {
			var listItemEl = element.find('.video-list-item'),
				descriptionEl = element.find('.video-list-item__description'),
				videoImageEl = element.find('.video-list-item__video-link'),
				videoPlayerEl = $compile('<youtube-video video-id="::video.youtube_id" player="ctrl.player"></youtube-video>'),
				expanded = false,
				expandedOnce = false;

			scope.toggleDescription = function () {
				descriptionEl.toggleClass('video-list-item__description--expanded');
			};

			scope.toggleExpanded = function () {
				expanded = !expanded;
				listItemEl.toggleClass('video-list-item--expanded', expanded);

				if (expanded && !expandedOnce) {
					expandedOnce = true;
					maybeHideDescriptionToggle();
					videoPlayerEl(scope).insertAfter(videoImageEl);
				}

			};

			function maybeHideDescriptionToggle () {
				var textEl = descriptionEl.find('.video-list-item__description__text');

				if (textEl.height() < 128) {
					descriptionEl
						.find('.video-list-item__description__controls')
						.remove();
				}
			}
		}
	}
}());

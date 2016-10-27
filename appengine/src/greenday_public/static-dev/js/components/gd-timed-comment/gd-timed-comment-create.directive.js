(function() {
	angular.module('components.timedComment')
		.directive('gdTimedCommentCreate', timedCommentCreate);

	/** @ngInject */
	function timedCommentCreate($analytics, $filter, moment, $timeout, ToastService, TimedVideoCommentThreadModel, staticFileUrlService) {

		var directive = {
			restrict: 'E',
			templateUrl: 'components/gd-timed-comment/gd-timed-comment-create.html',
			scope: {
				'thread': '=',
				'state': '='
			},
			require: '^gdFloatingElement',
			link: link
		};

		return directive;

		function link(scope, element, attrs, floatingElementCtrl) {
			scope.component = '<gd-timed-comment-create>';
			scope.saving = false;

			scope.defaultProfileImgUrl = staticFileUrlService.getFileUrl('img/gplus-default-s30.png');

			scope.save = function() {
				if (scope.thread.text === '') {
					ToastService.showError('Please enter some comment text before saving');
					return;
				}

				scope.saving = true;

				TimedVideoCommentThreadModel.create(scope.thread).then(function (thread) {
					var durationFilter = $filter('duration'),
						duration = durationFilter(Math.round(scope.thread.start_seconds));

					$analytics.eventTrack('add comment', {
						category: 'video theatre',
						label: 'on ' + scope.thread.youtube_id + ' at ' + duration + ': ' + scope.thread.text
					});
					floatingElementCtrl.close(thread);
				}, function (response) {
					ToastService.showError('Error: ' + response.data.error.message, 0);
				}).finally(function () {
					scope.saving = false;
				});
			};

			scope.cancel = function () {
				floatingElementCtrl.close();
			};
		}
	}
})();

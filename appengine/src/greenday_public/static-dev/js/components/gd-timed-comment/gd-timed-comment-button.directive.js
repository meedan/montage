(function() {
	angular.module('components.timedComment')
		.directive('gdTimedCommentButton', timedCommentButton);

	/** @ngInject */
	function timedCommentButton($timeout, floatingElementService, staticFileUrlService) {

		var directive = {
			restrict: 'E',
			templateUrl: 'components/gd-timed-comment/gd-timed-comment-button.html',
			controller: controller,
			controllerAs: 'ctrl',
			scope: {
				'thread': '='
			}
		};


		return directive;

		/** @ngInject */
		function controller($scope, $element, $attrs) {
			var ctrl = this,
				floatingElement;

			$scope.defaultProfileImgUrl = staticFileUrlService.getFileUrl('img/gplus-default-s30.png');

			$scope.component = '<gd-timed-comment-button>';
			$scope.previewPopup = null;

			ctrl.showPreview = function ($event) {
				var options = getPopupOptions();

				angular.extend(options, {
					'backdrop': false
				});

				options.attributes.mode = 'PREVIEW';

				// Call the floatingElement service to show the popup
				// FIXME: Use a "locals" approach to allow things to be injected
				// into the floating element controller rather than proxing data
				// manually through attributes as below.
				$scope.previewPopup = floatingElementService.show(
					'gd-timed-comment-popup', options);

				$scope.previewPopup.promise.then(function () {
					$scope.previewPopup = null;
				});
			};

			ctrl.hidePreview = function ($event) {
				// The user may have clicked the avatar which will already have
				// hidden the preview, so we need to check if the preview still
				// exists before trying to hide it.
				if (!$scope.previewPopup) {
					return;
				}

				floatingElementService.hide($scope.previewPopup.id);
				$scope.previewPopup = null;
			};

			function getPopupOptions() {
				return {
					'scope': $scope,
					'trigger': $element,
					'positioning': {
						'alignTo': 'top center',
						'alignEdge': 'bottom center',
						'position': 'outside',
						'gaps': {
							'y': 10
						}
					},
					'attributes': {
						'mode': 'REPLY',
						'thread': 'thread'
					}
				};
			}
		}
	}

})();

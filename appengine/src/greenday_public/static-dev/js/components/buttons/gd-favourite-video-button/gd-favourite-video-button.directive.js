(function () {
	angular.module('components.buttons')
		.directive('gdFavouriteVideoButton', favouriteVideoButton);

	/** @ngInject */
	function favouriteVideoButton() {
		var directive = {
			templateUrl: 'components/buttons/gd-favourite-video-button/gd-favourite-video-button.html',
			restrict: 'E',
			scope: {
				video: '='
			},
			link: link,
			controller: controller,
			controllerAs: 'ctrl',
			require: ['^gdFavouriteVideoButton']
		};

		return directive;

		/** @ngInject */
		function link(scope, element, attrs, controllers) {
			var ctrl = controllers[0];
			ctrl.gdButton = element.find('gd-button').eq(0);

			ctrl.updateClass();
		}

		/** @ngInject **/
		function controller($scope) {
			var ctrl = this,
				toggledClass = 'is-toggled-on',
				busyClass = 'is-busy';

			ctrl.toggleFavourite = function toggleFavourite() {
				var promise = $scope.video.setFavourite(!$scope.video.favourited);

				ctrl.gdButton.addClass(busyClass);

				promise
					.then(function () {
						ctrl.updateClass();
						ctrl.gdButton.removeClass(busyClass);
					});

				return promise;
			};

			ctrl.updateClass = function() {
				if ($scope.video.favourited === true) {
					ctrl.gdButton.addClass(toggledClass);
				} else {
					ctrl.gdButton.removeClass(toggledClass);
				}
			};
		}
	}
}());

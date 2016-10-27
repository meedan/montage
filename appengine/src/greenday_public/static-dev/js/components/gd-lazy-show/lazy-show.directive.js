// see http://developers.lendio.com/blog/combining-ng-if-and-ng-show-for-better-angularjs-performance/

(function () {
	angular.module('components.lazyShow')
		.directive('lazyShow', lazyShowDirective);


	function lazyShowDirective($animate) {
		var directive = {
			multiElement: true,
			transclude: 'element',
			priority: 600,
			terminal: true,
			restrict: 'A',
			link: link
		};

		function link($scope, $element, $attr, $ctrl, $transclude) {
			var loaded;
			$scope.$watch($attr.lazyShow, function lazyShowWatchAction(value) {
				if (loaded) {
					$animate[value ? 'removeClass' : 'addClass']($element, 'ng-hide');
				}
				else if (value) {
					loaded = true;
					$transclude(function (clone) {
						clone[clone.length++] = document.createComment(' end lazyShow: ' + $attr.lazyShow + ' ');
						$animate.enter(clone, $element.parent(), $element);
						$element = clone;
					});
				}
			});
		}
		return directive;
	}
}());
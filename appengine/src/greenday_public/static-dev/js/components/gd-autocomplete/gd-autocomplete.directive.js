(function () {
	angular.module('components')
		.directive('gdAutocomplete', gdAutocomplete);

		/** @ngInject */
		function gdAutocomplete($timeout) {
			var directive = {
				templateUrl: 'components/gd-autocomplete/gd-autocomplete.html',
				restrict: 'E',
				link: link,
				require: ['ngModel'],
				transclude: true,
				scope: {
					results: '=',
					ngModel: '=',
					displayProperty: '@',
					onSelect: '&?'
				}
			};

			return directive;

			/** @ngInject */
			function link($scope, $element, $attrs) {
				var $input = $element.find('input'),
					keys = {
						'UP': 38,
						'DOWN': 40,
						'ENTER': 13
					},
					hideDropdown = function () {
						$scope.showDropdown = false;
						$scope.currentIndex = -1;
					},
					showDropdown = function () {
						$scope.showDropdown = true;

						if ($scope.results.length) {
							// Automatically highlight the first result
							$scope.currentIndex = 0;
						}
					},
					handleKeydown = function (evt) {
						$scope.$apply(function () {
							if ($scope.showDropdown === true) {
								if (evt.keyCode === keys.UP || evt.keyCode === keys.DOWN) {
									evt.preventDefault();
									if (evt.keyCode === keys.DOWN) {
										if ($scope.currentIndex + 1 < $scope.results.length) {
											$scope.currentIndex++;
										} else {
											$scope.currentIndex = 0;
										}
									} else if (evt.keyCode === keys.UP) {
										if ($scope.currentIndex - 1 >= 0) {
											$scope.currentIndex--;
										} else {
											$scope.currentIndex = $scope.results.length - 1;
										}
									}
									$scope.$apply();
								} else if (evt.keyCode === keys.ENTER) {
									if ($scope.currentIndex !== -1) {
										evt.preventDefault();
										select($scope.results[$scope.currentIndex]);
									}
								}
							}
						});
					},
					select = function (result) {
						if (!result) {
							result = {};
							result[$scope.displayProperty] = $scope.ngModel[$scope.displayProperty];
						}
						$scope.ngModel = result;
						hideDropdown();
						$input.focus();
						if (angular.isFunction($scope.onSelect)) {
							$timeout(function () {
								$scope.onSelect();
							});
						}
					};

				$scope.$watch('results', function (results, ov) {
					if (results && results !== ov) {
						if (results.length) {
							showDropdown();
						} else {
							hideDropdown();
						}
					}
				});

				hideDropdown();
				$input.on('blur', hideDropdown);
				// $input.on('focus', showDropdown);
				$input.on('keydown', handleKeydown);
				$scope.select = select;
			}
		}
}());

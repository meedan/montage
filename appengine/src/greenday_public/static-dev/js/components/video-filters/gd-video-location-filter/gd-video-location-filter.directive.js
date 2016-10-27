(function () {
	angular.module('components')
		.directive('gdVideoLocationFilter', videoLocationFilter);

	/** @ngInject */
	function videoLocationFilter($timeout, PageService, _, uiGmapGoogleMapApi) {
		var directive = {
			templateUrl: 'components/video-filters/gd-video-location-filter/gd-video-location-filter.html',
			restrict: 'E',
			scope: {
				ngModel: '='
			},
			link: link,
			require: ['^gdVideoFilter', '^gdVideoLocationFilter', '^ngModel'],
			controller: controller,
			controllerAs: 'locationFilterCtrl'
		};

		return directive;

		function link(scope, element, attrs, controllers) {
			var filterCtrl = controllers[0],
				locationFilterCtrl = controllers[1],
				ngModelCtrl = controllers[2];

			scope.ngModelCtrl = ngModelCtrl;
			scope.filterCtrl = filterCtrl;
			scope.autocompleteEl = element.find('.location-filter__input--autocomplete').get(0);

			scope.$watch('ngModel', locationFilterCtrl.onModelUpdate, true);
			scope.$watch('mode', locationFilterCtrl.onModeUpdate);
		}

		function controller($scope) {
			var locationFilterCtrl = this;

			uiGmapGoogleMapApi.then(function (maps) {
				var searchBox = new maps.places.Autocomplete($scope.autocompleteEl);
				maps.event.addListener(searchBox, 'place_changed', locationFilterCtrl.onLocationUpdate);
				locationFilterCtrl.searchBox = searchBox;
			});

			locationFilterCtrl.clear = function () {
				$scope.mode = '';
				$scope.location = {
					radius: 10
				};
			};

			locationFilterCtrl.clear();

			locationFilterCtrl.onLocationUpdate = function () {
				var location = locationFilterCtrl.searchBox.getPlace();
				if (location) {
					angular.extend($scope.location, {
						lat: location.geometry.location.lat(),
						lng: location.geometry.location.lng(),
						name: location.name
					});
					locationFilterCtrl.applyFilter();
				}
			};

			locationFilterCtrl.applyFilter = function () {
				if ($scope.location.lat && $scope.location.lng && $scope.location.radius) {
					var parts = [
						$scope.location.lat,
						$scope.location.lng,
						$scope.location.radius,
						$scope.location.name
					];

					$scope.ngModelCtrl.$setViewValue(encodeURIComponent(parts.join('__')));
				}
			};

			locationFilterCtrl.update = function () {
				var items = [],
					prefix,
					radius = $scope.location ? parseInt($scope.location.radius, 10) : null;

				if ($scope.mode === '0') {
					items = [{name: 'Has no location'}];
				} else if ($scope.mode === '1') {
					items = [{name: 'Has location'}];
				} else if ($scope.mode === '2') {
					items = [
						{name: $scope.location.radius},
						{name: $scope.location.name || $scope.location.lat + ', ' + $scope.location.lng}
					];

					prefix = 'Within';
				}
				$scope.filterCtrl.setTitle({
					items: items,
					titleKey: 'name',
					prefix: prefix,
					offset: 2,
					conjunctive: radius > 1 ? 'miles of' : 'mile of',
					separator: ','
				});
			};

			locationFilterCtrl.onModelUpdate = function (newVal, oldVal) {
				if (angular.isDefined(newVal) && !(angular.equals(newVal, oldVal))) {
					var parts = decodeURIComponent(newVal).split('__');

					if (newVal === 'false') {
						$scope.mode = '0';
					} else if (newVal === 'true') {
						$scope.mode = '1';
					} else if (parts.length === 4) {
						$scope.mode = '2';
						$scope.location = {
							lat: parseFloat(parts[0]),
							lng: parseFloat(parts[1]),
							radius: parseInt(parts[2], 10),
							name: parts[3]
						};
					} else {
						$scope.mode = '';
					}
					locationFilterCtrl.update();
				}
			};

			locationFilterCtrl.onModeUpdate = function (mode, oldMode) {
				if (angular.isDefined(mode) && !angular.equals(mode, oldMode)) {
					if (mode === '0') {
						$scope.ngModelCtrl.$setViewValue('false');
					} else if (mode === '1') {
						$scope.ngModelCtrl.$setViewValue('true');
					} else if (mode === '') {
						$scope.ngModelCtrl.$setViewValue('');
					}
					if (mode !== '2') {
						locationFilterCtrl.update();
					}
				}
			};
		}

	}
}());

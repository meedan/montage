(function() {
	angular
		.module('gdOnboarding')
		.directive('gdOnboardingPopover', gdOnboardingPopover);

	/** @ngInject */
	function gdOnboardingPopover($timeout, $window, localStorageService, floatingElementService, _) {
		var directive = {
			restrict: 'E',
			templateUrl: 'components/gd-onboarding/gd-onboarding-popover.html',
			link: link,
			controller: controller,
			controllerAs: 'onboardingCtrl',
			require: ['^gdOnboardingPopover'],
			scope: {
				ngModel: '='
			}
		};

		return directive;

		function link(scope, element, attrs, controllers) {
			var onboardingCtrl = controllers[0];

			onboardingCtrl.containerEl = element.find('.gd-onboarding-container').eq(0);

			onboardingCtrl.debouncedPosition = _.debounce(onboardingCtrl.position, 200);

			scope.$watch('ngModel', function (model, oldSteps) {
				var onboardingCookie = localStorageService.get('onboarding') || {};

				if (model && model.steps && model.steps.length) {
					scope.enabled = onboardingCookie[model.id] !== true;

					if (scope.enabled) {
						onboardingCtrl.goto(0);
					}
				}
			});

			scope.$watch('currentIndex', function (newIndex, oldIndex) {
				if (angular.isDefined(newIndex) && newIndex !== oldIndex) {
					onboardingCtrl.showStep(scope.currentIndex);
				}
			});

		}

		function controller($scope) {
			var onboardingCtrl = this,
				classNames = 'top center-y left right center-x',
				onboardingCookie = localStorageService.get('onboarding') || {};

			onboardingCtrl.close = function (isAllSeen) {
				$scope.enabled = false;

				if (isAllSeen) {
					onboardingCookie[$scope.ngModel.id] = true;
					localStorageService.set('onboarding', onboardingCookie);
				}

				$($window).off('resize', onboardingCtrl.debouncedPosition);
			};

			onboardingCtrl.showStep = function (index) {
				$scope.currentStep = $scope.ngModel.steps[$scope.currentIndex];

				onboardingCtrl.position();

				$($window).on('resize', onboardingCtrl.debouncedPosition);
			};

			onboardingCtrl.position = function () {
				var container = onboardingCtrl.containerEl,
					triggerEl,
					positioningOptions,
					newClassNames;

				if ($scope.currentStep.attachTo) {
					triggerEl = $($scope.currentStep.attachTo).eq(0);
					positioningOptions = $scope.currentStep.positioning;
				} else {
					triggerEl = $('body');
					positioningOptions = {
						alignTo: 'center center',
						alignEdge: 'center center',
						position: 'outside',
						gaps: {
							x: 0,
							y: 0
						}
					};
				}

				newClassNames = positioningOptions.alignEdge.split(' ');

				if (newClassNames[0] === 'center') {
					newClassNames[0] = 'center-y';
				}
				if (newClassNames[1] === 'center') {
					newClassNames[1] = 'center-x';
				}

				$timeout(function () {
					floatingElementService.positionElement(container, triggerEl, positioningOptions);
					container.removeClass(classNames).addClass(newClassNames.join(' '));
				});
			};

			onboardingCtrl.goto = function (newIndex) {
				if (newIndex < $scope.ngModel.steps.length && newIndex >= 0) {
					$scope.currentIndex = newIndex;

					if ($scope.currentIndex === 0) {
						$scope.isAtStart = true;
					} else {
						$scope.isAtStart = false;
					}

					if ($scope.currentIndex + 1 === $scope.ngModel.steps.length) {
						$scope.isAtEnd = true;
					} else {
						$scope.isAtEnd = false;
					}
				}
			};

			onboardingCtrl.next = function () {
				onboardingCtrl.goto($scope.currentIndex + 1);
			};

			onboardingCtrl.previous = function () {
				onboardingCtrl.goto($scope.currentIndex - 1);
			};
		}
	}

}());

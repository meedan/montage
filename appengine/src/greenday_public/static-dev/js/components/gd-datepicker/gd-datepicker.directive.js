(function() {
	angular
		.module('components.datepicker')
		.directive('gdDatepicker', datepicker);

	/** @ngInject */
	function datepicker($log, $timeout, gdCalendarService, moment) {
		var directive = {
			templateUrl: 'components/gd-datepicker/gd-datepicker.html',
			restrict: 'E',
			scope: {
				ngModel: '=',
				minDate: '=?',
				maxDate: '=?',
				highlightMaxDate: '=?',
				onDateSelect: '&?'
			},
			link: link,
			require: ['^gdDatepicker', '^ngModel'],
			controller: controller,
			controllerAs: 'datepickerCtrl'
		};

		return directive;

		function link(scope, element, attrs, controllers) {
			$log.debug('<gd-datepicker>:link');

			var datepickerCtrl = controllers[0],
				ngModelCtrl = controllers[1],
				selectors = {
					weekNumber: '.gd-datepicker__week-number',
					day: '.gd-datepicker__week-day',
					disabledDay: '.gd-datepicker__week-day--disabled',
					calendar: '.gd-datepicker__calendar',
					content: '.gd-datepicker__content',
				},
				$calendarEl = element.find(selectors.calendar).eq(0),
				$contentEl = element.find(selectors.content).eq(0);

			datepickerCtrl.ngModelCtrl = ngModelCtrl;
			datepickerCtrl.$calendarEl = $calendarEl;
			datepickerCtrl.$contentEl = $contentEl;

			/////////////////
			// Scope API
			/////////////////

			/////////////////
			// Custom events
			/////////////////
			$calendarEl.on('click', selectors.day, datepickerCtrl.onDayClick);

			/////////////////
			// Scope events
			/////////////////
			scope.$on('$destroy', function () {
				$log.debug('<gd-datepicker>:$destroy');
				$calendarEl.off('click', selectors.day, datepickerCtrl.onDayClick);
			});

			/////////////////
			// Scope watchers
			/////////////////
			scope.$watch('ngModel', datepickerCtrl.onModelUpdate);
			scope.$watch('datepicker.currentDate', datepickerCtrl.onCurrentDateChange, true);
			scope.$watch('datepicker.selectedMonth', datepickerCtrl.onSelectedMonthChange);
			scope.$watch('datepicker.selectedYear', datepickerCtrl.onSelectedYearChange);
		}

		function controller($scope) {
			var datepickerCtrl = this;

			$log.debug('<gd-datepicker>:controller');

			datepickerCtrl.onSelectedMonthChange = function (newVal, oldVal) {
				if (newVal && newVal !== oldVal) {
					var month = $scope.datepicker.selectedMonth,
						year = $scope.datepicker.selectedYear;

					$scope.datepicker.redraw(month, year);
				}
			};

			datepickerCtrl.onSelectedYearChange = function (newVal, oldVal) {
				if (newVal && newVal !== oldVal) {
					var month = $scope.datepicker.selectedMonth,
						year = $scope.datepicker.selectedYear;

					$scope.datepicker.redraw(month, year);
				}
			};

			datepickerCtrl.onModelUpdate = function (newVal, oldVal) {
				$log.debug('<gd-datepicker>:onModelUpdate', newVal, oldVal);

				$scope.datepicker.setDate(newVal);
			};

			datepickerCtrl.onCurrentDateChange = function (newVal, oldVal) {
				if (newVal && !angular.equals(newVal, oldVal)) {
					datepickerCtrl.ngModelCtrl.$setViewValue(newVal.toDate());
				}
			};

			datepickerCtrl.render = function () {
				if (!$scope.datepicker) {
					$log.debug('<gd-datepicker>:controller:render');
					var now = moment.utc();
					now.hours(0).minutes(0).seconds(0).milliseconds(0);

					$scope.datepicker = gdCalendarService.create({
						minDate: $scope.minDate ? moment.utc($scope.minDate) : null,
						maxDate: $scope.maxDate ? moment.utc($scope.maxDate) : now,
						highlightMaxDate: $scope.highlightMaxDate,
						currentDate: $scope.ngModel
					});
				}
			};

			datepickerCtrl.onDayClick = function (event) {
				event.preventDefault();

				$log.debug('<gd-datepicker>:onDayClick');

				var $el = $(event.currentTarget),
					date = moment.utc($el.data('date'));

				if (!$el.hasClass('gd-datepicker__week-day--disabled')) {
					$scope.$apply(function () {
						datepickerCtrl.ngModelCtrl.$setViewValue(date.toDate());
					});
					$scope.onDateSelect();
				}

			};

			datepickerCtrl.gotoMonth = function (step) {
				var month = parseInt($scope.datepicker.selectedMonth, 10) + 1,
					year = $scope.datepicker.selectedYear,
					date = [month, year].join('-'),
					m = moment.utc(date, 'MM-YYYY');

				m.add(step, 'months');
				$scope.datepicker.selectedMonth = m.month();
				$scope.datepicker.selectedYear = m.year();
			};

			datepickerCtrl.render();
		}
	}
}());

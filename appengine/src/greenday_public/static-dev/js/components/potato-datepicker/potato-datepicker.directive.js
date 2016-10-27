(function() {
	angular
		.module('potato-datepicker')
		.directive('ptDatepicker', datepicker);

	/** @ngInject */
	function datepicker($log, $timeout, ptCalendarService, moment) {
		var directive = {
			templateUrl: 'components/potato-datepicker/potato-datepicker.html',
			restrict: 'E',
			scope: {
				ngModel: '=',
				isOpened: '='
			},
			link: link,
			require: ['^ptDatepicker', '^ngModel'],
			controller: controller,
			controllerAs: 'datepickerCtrl'
		};

		return directive;

		function link(scope, element, attrs, controllers) {
			$log.debug('<pt-datepicker>:link');

			var datepickerCtrl = controllers[0],
				ngModelCtrl = controllers[1],
				selectors = {
					weekNumber: '.pt-datepicker__week-number',
					day: '.pt-datepicker__week-day',
					calendar: '.pt-datepicker__calendar',
					content: '.pt-datepicker__content',
				},
				$calendarEl = element.find(selectors.calendar).eq(0),
				$contentEl = element.find(selectors.content).eq(0),
				defaultCalendarOptions = {
					maxDate: moment.utc(new Date()),
					type: 'publish_date',
					mode: 'exact',
					monthOffset: 12
				};

			datepickerCtrl.ngModelCtrl = ngModelCtrl;
			datepickerCtrl.$calendarEl = $calendarEl;
			datepickerCtrl.$contentEl = $contentEl;

			/////////////////
			// Scope API
			/////////////////
			scope.calendarOptions = angular.extend({}, defaultCalendarOptions, scope.options || {});

			/////////////////
			// Custom events
			/////////////////
			$calendarEl.on('click', selectors.weekNumber, datepickerCtrl.onWeekNumberClick);
			$calendarEl.on('click', selectors.day, datepickerCtrl.onDayClick);

			/////////////////
			// Scope events
			/////////////////
			scope.$on('$destroy', function () {
				$log.debug('<pt-datepicker>:$destroy');
				$calendarEl.off('click', selectors.weekNumber, datepickerCtrl.onWeekNumberClick);
				$calendarEl.off('click', selectors.day, datepickerCtrl.onDayClick);
			});

			/////////////////
			// Scope watchers
			/////////////////
			// scope.$watch('options', datepickerCtrl.onOptionsUpdate, true);
			scope.$watch('ngModel', datepickerCtrl.onModelUpdate, true);
			scope.$watch('datepicker.currentDate', datepickerCtrl.onCurrentDateChange, true);
			scope.$watch('datepicker.months', datepickerCtrl.onDatepickerRedraw);
		}

		/** @ngInject */
		function controller($scope, $element, $attrs) {
			var datepickerCtrl = this;

			$log.debug('<pt-datepicker>:controller');

			datepickerCtrl.onModelUpdate = function (newVal, oldVal) {
				$log.debug('<pt-datepicker>:onModelUpdate', newVal, oldVal);

				if (newVal) {
					if (newVal.currentDate) {
						if (newVal.mode !== 'between' && newVal.mode !== 'notbetween') {
							newVal.currentDate.end = null;
						}
						// Since we are now lazy loading the datepicker ensure that its
						// rendering does not rely on the onModelUpdate callback.
						datepickerCtrl.render();

						$scope.datepicker.setOptions(newVal);
						$scope.datepicker.setDate(newVal.currentDate);
					}
				}
			};

			datepickerCtrl.scrollToMonth = function (monthId) {
				var datepickerCtrl = this,
					monthEl = $('#' + monthId),
					contentEl = datepickerCtrl.$contentEl,
					currentScrollTop = $(contentEl).scrollTop(),
					currentOffset = $(contentEl).offset().top,
					monthOffset = $(monthEl).offset().top,
					finalScrollTop = currentScrollTop - currentOffset + monthOffset;

				contentEl.scrollTop(finalScrollTop);
			};

			datepickerCtrl.onCurrentDateChange = function (newVal, oldVal) {
				if (newVal && !angular.equals(newVal, oldVal)) {
					datepickerCtrl.ngModelCtrl.$setViewValue({
						currentDate: {
							start: newVal.start ? newVal.start.toDate() : null,
							end: newVal.end ? newVal.end.toDate() : null
						},
						type: $scope.datepicker.options.type || 'published_date',
						mode: $scope.datepicker.options.mode || 'exact'
					});
				}
			};

			datepickerCtrl.onDatepickerRedraw = function (calendarData) {
				$log.debug('<pt-datepicker>:onDatepickerRedraw', calendarData);
				if (calendarData) {
					var dp = $scope.datepicker,
						formats = ptCalendarService.idFormats;

					if (dp.currentDate && dp.currentDate.start) {
						$timeout(function () {
							datepickerCtrl.scrollToMonth(dp.currentDate.start.format(formats.month));
						});
					}
				}
			};

			datepickerCtrl.render = function () {
				$log.debug('<pt-datepicker>:controller:render', $scope.calendarOptions);
				$scope.datepicker = ptCalendarService.create($scope.calendarOptions);
			};

			datepickerCtrl.onWeekNumberClick = function (event) {
				// TODO: select all days in the week
				event.preventDefault();
			};

			datepickerCtrl.onDayClick = function (event) {
				event.preventDefault();

				$log.debug('<pt-datepicker>:onDayClick');

				var $el = $(event.currentTarget),
					date = moment.utc($el.data('date')),
					dateVal = date.toDate(),
					currentDate = $scope.datepicker.currentDate,
					dateObj = {
						start: currentDate.start ? currentDate.start : null,
						end: currentDate.end ? currentDate.end : null
					},
					mode = $scope.datepicker.options.mode,
					type = $scope.datepicker.options.type,
					viewValue = {
						mode: mode,
						type: type
					};

				if (mode === 'between' || mode === 'notbetween') {
					if (!currentDate.start) {
						dateObj.start = dateVal;
					} else if (!currentDate.end && date > currentDate.start) {
						dateObj.end = dateVal;
					} else {
						// work out if dateVal is closer to the start or end of the range
						var startDistance = Math.min(dateVal - currentDate.start, currentDate.start - dateVal),
							endDistance = Math.min(dateVal - currentDate.end, currentDate.end - dateVal);

						if (startDistance >= endDistance) {
							dateObj.start = dateVal;
						}
						else {
							dateObj.end = dateVal;
						}
					}
				} else {
					dateObj.start = dateVal;
				}

				$scope.$apply(function () {
					// datepickerCtrl.ngModelCtrl.$viewValue.currentDate = dateObj;
					// datepickerCtrl.ngModelCtrl.$viewValue.currentDate = dateObj;
					var vv = angular.copy(datepickerCtrl.ngModelCtrl.$viewValue);
					angular.copy(dateObj, vv.currentDate);
					datepickerCtrl.ngModelCtrl.$setViewValue(vv);
				}.bind(this));
			};
		}

		/////////////////
		// Private functions
		/////////////////
	}

}());


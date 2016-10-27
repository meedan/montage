(function() {
	angular
		.module('potato-datepicker')
		.factory('ptCalendarService', calendarService);

	/** @ngInject */
	function calendarService(moment) {
		var service = {
				create: create,
				idFormats: {
					month: 'YYYY-MM',
					week: 'YYYY-MM-ww',
					day: 'YYYY-MM-ww-DD'
				}
			},
			modes = {
				exact: 'exact',
				before: 'before',
				after: 'after',
				between: 'between',
				notbetween: 'notbetween'
			};

		/////////////////
		// Public functions
		/////////////////

		function create(options) {
			return new PtDatepicker(options);
		}

		/**
		 * The main datepicker class
		 * @param {Object} The options object. See defaults for valid options.
		 */
		function PtDatepicker(options) {
			var defaultOptions = {
					currentDate: {
						start: null,
						end: null
					},
					minDate: null,
					maxDate: null,
					monthOffset: null,
					showWeekNumbers: true,
					showWeekDays: true,
					mode: modes.exact,
					type: 'publish_date'
				},
				weekdays = moment.weekdaysMin();

			// Set the moment's locale to have Monday as the first day of the week
			// TODO: make this configurable
			moment.locale('en', {
				week: { dow: 1 }
			});

			// Move Sunday to the end of the list
			// TODO: make this configurable as well
			weekdays.push(weekdays.shift());

			this.options = {};
			this.setOptions(angular.extend({}, defaultOptions, options));
			this.setDate(this.options.currentDate);
			this.weekdays = weekdays;
		}

		/**
		 * Datepicker mods
		 * @type {Object}
		 */
		PtDatepicker.prototype.modes = modes;

		/**
		 * Redraws the calendar with the current options
		 */
		PtDatepicker.prototype.redraw = function () {
			this.months = this.generateCalendarData();
			this.forceRedraw = false;
		};

		/**
		 * Generates the calendar data
		 * @return {Array.Object}
		 */
		PtDatepicker.prototype.generateCalendarData = function () {
			var dateRange = _getDateRange(this.options);

			return _generateMonths(dateRange, this.options);
		};

		/**
		 * Sets the options for the datepicker
		 * @param {Object} The options object
		 */
		PtDatepicker.prototype.setOptions = function (options) {
			if (angular.isObject(options)) {
				if (this.options.type !== options.type || this.options.mode !== options.mode) {
					this.forceRedraw = true;
				}
				angular.extend(this.options, options);
			}
		};

		/**
		 * Sets the current date of the datepicker
		 * @param {Date} The date to be set
		 */
		PtDatepicker.prototype.setDate = function (newDate, preventRedraw) {
			var startDate = newDate.start,
				startDateValid = startDate && moment(startDate).isValid(),
				endDate = newDate.end,
				endDateValid = endDate && moment(endDate).isValid(),
				currentDate = this.currentDate,
				isSameStartDate,
				isSameEndDate,
				isSameDate,
				needsRedraw = false;

			if (startDateValid) {
				startDate = moment.utc(startDate);

				isSameStartDate = (currentDate && currentDate.start) ? startDate.toISOString() === currentDate.start.toISOString() : false;

				if (endDateValid) {
					endDate = moment.utc(endDate);
					isSameEndDate = (currentDate && currentDate.end) ? endDate.toISOString() === currentDate.end.toISOString() : false;
				} else {
					endDate = null;
					isSameEndDate = (currentDate && currentDate.end) ? endDate === currentDate.end : false;
				}
			} else {
				startDate = null;
				isSameStartDate = (currentDate && currentDate.start) ? startDate === currentDate.start : false;
				endDate = null;
				isSameEndDate = (currentDate && currentDate.end) ? endDate === currentDate.end : false;
			}

			isSameDate = isSameStartDate && isSameEndDate;
			needsRedraw = !isSameDate;

			this.setOptions({
				currentDate: {
					start: startDate,
					end: endDate
				}
			});

			this.currentDate = {
				start: startDate,
				end: endDate
			};

			this.currentDateISO = {
				start: startDate ? startDate.toISOString() : '',
				end: endDate ? endDate.toISOString() : ''
			};

			if (this.forceRedraw || needsRedraw) {
				this.redraw();
			}
		};

		/**
		 * Sets the minimum date to be active on the datepicker
		 * @param {Date|null} The minimum date. If null passed, min date is removed.
		 */
		PtDatepicker.prototype.setMinimumDate = function (minDate) {
			if (moment(minDate).isValid()) {
				this.setOptions({minDate: minDate});
				this.redraw();
			} else {
				throw 'Date is not valid';
			}
		};

		/**
		 * Sets the maximum date to be active on the datepicker
		 * @param {Date|null} The maximum date. If null passed, max date is removed.
		 */
		PtDatepicker.prototype.setMaximumDate = function (maxDate) {
			if (moment(maxDate).isValid()) {
				this.setOptions({maxDate: maxDate});
				this.redraw();
			} else {
				throw 'Date is not valid';
			}
		};

		// We need to return the service after all the PtDatepicker stuff
		return service;

		/////////////////
		// Private functions
		/////////////////

		/**
		 * Gets a date range between two dates with a given offset
		 * @param {Date} The current date
		 * @param {Number} Number of months to render before and after the current date
		 * @param {Date} The minimum date to make active
		 * @param {Date} The maximum date to make active
		 * @return {moment.range}
		 */
		function _getDateRange(options) {
			var startDate = options.currentDate.start || new Date(),
				endDate = options.currentDate.end || new Date(),
				minMonth = moment.utc(startDate),
				maxMonth = moment.utc(endDate),
				dateRange;

			if (options.monthOffset) {
				minMonth.subtract(options.monthOffset, 'months');
				maxMonth.add(options.monthOffset, 'months');
			}

			if (options.minDate && moment(options.minDate).isValid()) {
				minMonth = moment.max(minMonth, moment.utc(options.minDate));
			}

			if (options.maxDate && moment(options.maxDate).isValid()) {
				maxMonth = moment.min(maxMonth, moment.utc(options.maxDate));
			}

			dateRange = moment.range(minMonth.startOf('month'), maxMonth.endOf('month'));

			return dateRange;
		}

		function _isHighlighted(mode, currentDate, startDate, endDate) {
			var isHighlighted = false;

			if (mode === modes.between) {
				isHighlighted = startDate > currentDate.start && endDate < currentDate.end;
			} else if (mode === modes.notbetween) {
				var startDateExcluded = startDate < currentDate.start && endDate < currentDate.start,
					endDateExcluded = startDate > currentDate.end && endDate > currentDate.end;

				isHighlighted = startDateExcluded || endDateExcluded;
			} else if (mode === modes.before) {
				isHighlighted = currentDate.start > endDate;
			} else if (mode === modes.after) {
				isHighlighted = currentDate.start < startDate;
			}

			return isHighlighted;
		}

		/**
		 * Generates the month data for the given range
		 * @param {moment.range}
		 * @return {Array.Object} The list of months
		 */
		function _generateMonths(range, options) {
			var startOfMonth,
				startOfFirstWeek,
				endOfMonth,
				endOfLastWeek,
				monthRange,
				monthData,
				isMonthHighlighted,
				months = [];


			range.by('months', function (month) {
				startOfMonth = moment.utc(month).startOf('month');
				startOfFirstWeek = moment.utc(month).startOf('month').startOf('week');
				endOfMonth = moment.utc(month).endOf('month');
				endOfLastWeek = moment.utc(month).endOf('month').endOf('week');

				monthRange = moment.range(startOfFirstWeek, endOfLastWeek);

				isMonthHighlighted = _isHighlighted(options.mode, options.currentDate, startOfMonth, endOfMonth);

				monthData = {
					// id will be used in ng-repeat blocks as the tracker
					id: month.format(service.idFormats.month),
					name: moment.months(month.month()),
					weeks: _generateWeeks(monthRange, month.month(), options, isMonthHighlighted),
					moment: month,
					year: month.year(),
					isHighlighted: isMonthHighlighted
				};

				months.push(monthData);
			});

			return months;
		}

		/**
		 * Generates the week data for the given range
		 * @param {moment.range}
		 * @return {Array.Object} The list of weeks
		 */
		function _generateWeeks(range, month, options, isMonthHighlighted) {
			var weeks = [],
				weekData,
				startOfWeek,
				endOfWeek,
				weekRange,
				isWeekHighlighted;

			range.by('weeks', function (week) {
				startOfWeek = moment.utc(week).startOf('isoWeek');
				endOfWeek = moment.utc(week).endOf('isoWeek');
				weekRange = moment.range(startOfWeek, endOfWeek);
				isWeekHighlighted = _isHighlighted(options.mode, options.currentDate, startOfWeek, endOfWeek);

				weekData = {
					id: week.format(service.idFormats.week),
					week: week.week(),
					days: _generateDays(weekRange, month, options, isWeekHighlighted),
					isHighlighted: !isMonthHighlighted && isWeekHighlighted
				};

				weeks.push(weekData);
			});

			return weeks;
		}

		/**
		 * Generates the day data for the given range
		 * @param {Moment.range}
		 * @param {Moment}
		 * @return {Array.Object} The list of days
		 */
		function _generateDays(range, month, options, isWeekHighlighted) {
			var days = [],
				dayData,
				dayISO,
				isSelected,
				isHighlighted,
				isStartDate,
				isEndDate,
				currentDate = options.currentDate,
				currentDateISO = {
					start: currentDate.start ? currentDate.start.toISOString() : null,
					end: currentDate.end ? currentDate.end.toISOString() : null
				};

			range.by('days', function (day) {
				dayISO = day.toISOString();
				isStartDate = currentDateISO.start === dayISO;
				isEndDate = currentDateISO.end === dayISO;
				isSelected = isStartDate || isEndDate;
				isHighlighted = _isHighlighted(options.mode, options.currentDate, day, day);
				dayData = {
					// id will be used in ng-repeat blocks as the tracker
					id: day.format(service.idFormats.day),
					name: moment.weekdays(day.weekday()),
					dayNumber: day.date(),
					date: day.toISOString(),
					moment: day,
					isInCurrentMonth: day.month() === month,
					isSelected: isSelected,
					isStartDate: isStartDate,
					isEndDate: isEndDate,
					isHighlighted: !isWeekHighlighted && isHighlighted
				};
				days.push(dayData);
			});

			return days;
		}
	}

}());

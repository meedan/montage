(function() {
	angular
		.module('components.datepicker')
		.factory('gdCalendarService', calendarService);

	/** @ngInject */
	function calendarService(moment) {
		var service = {
				create: create,
				idFormats: {
					month: 'YYYY-MM',
					week: 'YYYY-MM-ww',
					day: 'YYYY-MM-ww-DD'
				}
			};

		/////////////////
		// Public functions
		/////////////////

		function create(options) {
			return new GDDatepicker(options);
		}

		/**
		 * The main datepicker class
		 * @param {Object} The options object. See defaults for valid options.
		 */
		function GDDatepicker(options) {
			var defaultOptions = {
					currentDate: null,
					minDate: null,
					maxDate: null
				},
				weekdays = moment.weekdaysMin(),
				years = [],
				thisYear = moment.utc().year(),
				startYear = 1970,
				i;

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
			this.months = moment.months();

			for (i=startYear; i<=thisYear; i++) {
				years.push(i);
			}
			this.years = years;
		}

		/**
		 * Redraws the calendar with the current options
		 */
		GDDatepicker.prototype.redraw = function (month, year) {
			this.currentMonth = this.generateCalendarData(month, year);
			this.forceRedraw = false;
		};

		/**
		 * Generates the calendar data
		 * @return {Array.Object}
		 */
		GDDatepicker.prototype.generateCalendarData = function (month, year) {
			var date = this.options.currentDate || moment.utc();

			if (!month) {
				month = date.month();
			}

			if (!year) {
				year = date.year();
			}

			return _generateMonth(month, year, this.options);
		};

		/**
		 * Sets the options for the datepicker
		 * @param {Object} The options object
		 */
		GDDatepicker.prototype.setOptions = function (options) {
			if (angular.isObject(options)) {
				angular.extend(this.options, options);
			}
		};

		/**
		 * Sets the current date of the datepicker
		 * @param {Date} The date to be set
		 */
		GDDatepicker.prototype.setDate = function (newDate) {
			var date = newDate,
				dateValid = date && moment(date).isValid(),
				currentDate = this.currentDate,
				isSameDate,
				needsRedraw = false;

			if (dateValid) {
				date = moment.utc(date);
				isSameDate = currentDate ? date.toISOString() === currentDate.toISOString() : false;

				this.selectedMonth = date.month();
				this.selectedYear = date.year();

			} else {
				date = null;
				isSameDate = currentDate ? date === currentDate : false;

				this.selectedMonth = moment.utc().month();
				this.selectedYear = moment.utc().year();
			}

			needsRedraw = !isSameDate;

			this.setOptions({
				currentDate: date
			});

			this.currentDate = date;

			this.currentDateISO = date ? date.toISOString() : '';

			if (this.forceRedraw || needsRedraw) {
				this.redraw(this.selectedMonth, this.selectedYear);
			}
		};

		// We need to return the service after all the GDDatepicker stuff
		return service;

		/////////////////
		// Private functions
		/////////////////
		/**
		 * Generates the month data for the given range
		 * @param {moment.range}
		 * @return {Array.Object} The list of months
		 */
		function _generateMonth(month, year, options) {
			var monthData,
				monthNum = parseInt(month, 10) + 1,
				dateStr = [monthNum % 12, year].join(' '),
				dateFmt = 'M YYYY',
				startDate = moment.utc(dateStr, dateFmt).startOf('month'),
				endDate = moment.utc(dateStr, dateFmt).endOf('month'),
				monthRange = moment.range(startDate, endDate),
				startOfFirstWeek = moment.utc(dateStr, dateFmt).startOf('month').startOf('week'),
				endOfLastWeek = moment.utc(dateStr, dateFmt).endOf('month').endOf('week');

			monthRange = moment.range(startOfFirstWeek, endOfLastWeek);

			monthData = {
				name: moment.months(startDate.month()),
				weeks: _generateWeeks(monthRange, startDate.month(), options),
				moment: startDate,
				year: startDate.year()
			};

			return monthData;
		}

		/**
		 * Generates the week data for the given range
		 * @param {moment.range}
		 * @return {Array.Object} The list of weeks
		 */
		function _generateWeeks(range, month, options) {
			var weeks = [],
				weekData,
				startOfWeek,
				endOfWeek,
				weekRange;

			range.by('weeks', function (week) {
				startOfWeek = moment.utc(week).startOf('isoWeek');
				endOfWeek = moment.utc(week).endOf('isoWeek');
				weekRange = moment.range(startOfWeek, endOfWeek);

				weekData = {
					id: week.format(service.idFormats.week),
					week: week.week(),
					days: _generateDays(weekRange, month, options)
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
		function _generateDays(range, month, options) {
			var days = [],
				dayData,
				dayISO,
				isSelected,
				isMax,
				isMin,
				isMinMax,
				isAfterMax,
				isBeforeMin,
				isInCurrentMonth,
				isFaded,
				isHighlighted,
				isDisabled,
				currentDate = options.currentDate,
				currentDateISO = currentDate ? currentDate.toISOString() : null,
				minDate = options.minDate || null,
				maxDate = options.maxDate || null,
				minDateISO = minDate ? minDate.toISOString() : null,
				maxDateISO = maxDate ? maxDate.toISOString() : null;

			range.by('days', function (day) {
				dayISO = day.toISOString();
				isSelected = currentDateISO === dayISO;
				isMax = maxDateISO === dayISO;
				isMin = minDateISO === dayISO;
				isMinMax = isMin || isMax;
				isInCurrentMonth = day.month() === month;
				isHighlighted = false;
				isAfterMax = (maxDate && day > maxDate);
				isBeforeMin = (minDate && day < minDate);

				isDisabled = isAfterMax || isBeforeMin;
				isFaded = !isInCurrentMonth || isDisabled || (!isSelected && isMinMax);

				dayData = {
					// id will be used in ng-repeat blocks as the tracker
					id: day.format(service.idFormats.day),
					name: moment.weekdays(day.weekday()),
					dayNumber: day.date(),
					date: day.toISOString(),
					moment: day,
					isFaded: isFaded,
					isDisabled: isDisabled,
					isSelected: isSelected || (options.highlightMaxDate && isMinMax) || isMin,
					isHighlighted: isHighlighted
				};
				days.push(dayData);
			});

			return days;
		}
	}

}());

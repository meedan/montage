(function () {
	angular.module('components')
		.directive('gdVideoDateFilter', videoDateFilter);

	/** @ngInject */
	function videoDateFilter($log, moment) {
		var directive = {
				templateUrl: 'components/video-filters/gd-video-date-filter/gd-video-date-filter.html',
				restrict: 'E',
				scope: {
					ngModel: '=',
					project: '=?',
					filterMeta: '='
				},
				link: link,
				require: ['^gdVideoFilter', '^gdVideoDateFilter', '^ngModel'],
				controller: controller,
				controllerAs: 'dateFilterCtrl'
			},
			dateFormat = 'YYYY-MM-DD',
			prettyDateFormat = 'D MMM YYYY',
			titles = {
				publish_date: 'Uploaded',
				recorded_date: 'Recorded',
				no_recorded_date: 'Has no recorded date',
				exact: 'On',
				before: 'Before',
				after: 'After',
				between: 'Between',
				notbetween: 'Excluding',
			},
			modes = [{
				mode: 'exact',
				text: titles.exact
			}, {
				mode: 'before',
				text: titles.before
			}, {
				mode: 'after',
				text: titles.after
			}, {
				mode: 'between',
				text: titles.between
			}, {
				mode: 'notbetween',
				text: titles.notbetween
			}],
			types = [{
				type: 'publish_date',
				text: titles.publish_date
			}, {
				type: 'recorded_date',
				text: titles.recorded_date
			}, {
				type: 'no_recorded_date',
				text: titles.no_recorded_date
			}];

		return directive;

		function link(scope, element, attrs, controllers) {
			var filterCtrl = controllers[0],
				dateFilterCtrl = controllers[1],
				ngModelCtrl = controllers[2];

			$log.debug('<gd-video-date-filter>:link');

			scope.ngModelCtrl = ngModelCtrl;
			scope.filterCtrl = filterCtrl;
			scope.data = {
				selectedDate: {}
			};

			scope.modes = modes;
			scope.types = types;

			scope.$watch('ngModel', dateFilterCtrl.onModelUpdate);
			scope.$watch('data.selectedDate', dateFilterCtrl.onDateUpdate, true);
			scope.$watch('data.selectedMode', dateFilterCtrl.onDateUpdate);
			scope.$watch('data.selectedType', dateFilterCtrl.onDateUpdate);
		}

		function controller($scope) {
			var dateFilterCtrl = this;

			$log.debug('<gd-video-date-filter>:controller');

			dateFilterCtrl.reset = function () {
				$scope.ngModelCtrl.$setViewValue(undefined);
			};

			dateFilterCtrl.clear = function () {
				$scope.data.selectedDate = null;
				$scope.data.startDateString = '';
				$scope.data.endDateString = '';
				dateFilterCtrl.setMode('exact');
				dateFilterCtrl.setType('publish_date');
			};

			dateFilterCtrl.setMode = function (mode) {
				$scope.currentModeTitle = titles[mode];
				$scope.data.selectedMode = mode;
			};

			dateFilterCtrl.setType = function (type) {
				var oldType = $scope.data.selectedType;
				$scope.currentTypeTitle = titles[type];
				$scope.data.selectedType = type;
				if (type === 'no_recorded_date' && oldType !== type) {
					dateFilterCtrl.onModelUpdate(['recorded_date', 'false'].join('__'));
				}
			};

			dateFilterCtrl.onModelUpdate = function (newVal, oldVal) {
				$log.debug('<gd-video-date-filter>:onModelUpdate', newVal);
				var items = [],
					prefix = '',
					conjunctive = 'and';

				if (angular.isUndefined(newVal)) {
					dateFilterCtrl.clear();
				} else if (angular.isDefined(newVal) && !(angular.equals(newVal, oldVal))) {
					var parts = decodeURIComponent(newVal).split('__'),
						selectedDate = null,
						startDate = parts[2] || null,
						startDateString = '',
						endDate = parts[3] || null,
						endDateString = '',
						selectedType = 'publish_date',
						selectedMode = 'exact';

					if (newVal !== null) {
						if (parts[0] === 'recorded_date' && parts[1] === 'false') {
							selectedDate = {
								start: new Date(),
								end: null
							};
							selectedType = 'no_recorded_date';
							items.push({ name: titles.no_recorded_date });
						} else {
							startDate = startDate ? moment.utc(startDate, dateFormat) : null;
							endDate = endDate ? moment.utc(endDate, dateFormat) : null;
							selectedType = parts[0] || 'publish_date';
							selectedMode = parts[1] || 'exact';
							selectedDate = {
								start: startDate ? startDate.toDate() : null,
								end: endDate ? endDate.toDate() : null
							};

							if (startDate) {
								startDateString = startDate.format(prettyDateFormat);
								items.push({ name: startDateString});

								if (endDate) {
									endDateString = endDate.format(prettyDateFormat);
									items.push({ name: endDateString });
								}
							}

							prefix = [titles[selectedType], titles[selectedMode].toLowerCase()].join(' ');
						}

						dateFilterCtrl.setType(selectedType);
						dateFilterCtrl.setMode(selectedMode);

						$scope.data.selectedDate = selectedDate;

						if (selectedMode === 'notbetween') {
							conjunctive = 'to';
						}
					}
				}

				$scope.filterCtrl.setTitle({
					items: items,
					titleKey: 'name',
					prefix: prefix,
					offset: 2,
					conjunctive: conjunctive,
					separator: ','
				});
			};

			dateFilterCtrl.onDateUpdate = function (newVal) {
				$log.debug('<gd-video-date-filter>:onDateUpdate', newVal);
				if (newVal) {
					var values = [],
						date = $scope.data.selectedDate,
						mode = $scope.data.selectedMode,
						type = $scope.data.selectedType,
						startDate,
						endDate,
						isRange = (mode === 'notbetween' || mode === 'between'),
						viewValue = null;

					if (type === 'no_recorded_date') {
						values.push('recorded_date', 'false');
						viewValue = values.join('__');
					} else if (date) {
						values.push(type, mode);

						if (!isRange) {
							$scope.data.selectedDate.end = null;
						}

						if (date.start) {
							startDate = moment.utc(date.start);
							values.push(startDate.format(dateFormat));
							$scope.data.startDateString = startDate.format(prettyDateFormat);

							if (isRange && date.end) {
								endDate = moment.utc(date.end);
								values.push(endDate.format(dateFormat));
								$scope.data.endDateString = endDate.format(prettyDateFormat);
							}
						}


						if ((isRange && date.end) || !isRange) {
							viewValue = values.join('__');
						}
					} else {
						viewValue = undefined;
					}

					if (viewValue !== null) {
						$scope.ngModelCtrl.$setViewValue(viewValue);
					}
				}
			};
		}

	}
}());

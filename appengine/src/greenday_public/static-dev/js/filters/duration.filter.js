(function () {
	angular
		.module('app.filters')
		.filter('duration', durationFilter);

	/** @ngInject */
	function durationFilter(moment, _) {
		return function(durationInSeconds) {
			var duration = moment.duration(durationInSeconds, 'seconds'),
				formattedParts = [],
				days = duration.days(),
				hours = duration.hours(),
				minutes = duration.minutes(),
				seconds = duration.seconds(),
				parts;

			if (seconds < 10) {
				seconds = '0' + seconds;
			}

			if (hours) {
				if (minutes < 10) {
					minutes = '0' + minutes;
				}
			}

			parts = [days, hours, minutes, seconds];
			formattedParts = _.compact(parts);

			// We never want to show *just* the seconds when showing a duration
			// as then it's not at all clear what the units are. We should
			// always show the minutes, even if they are 0 so we have a time
			// which looks like 0:xx.
			if (minutes === 0) {
				formattedParts.unshift(0);
			}

			return formattedParts.join(':');
		};
	}
}());

/* global _:false, moment:false */
(function () {
	angular.module('app')
		.constant('_', _)
		.constant('moment', moment)
		.constant('DEBUG', window.DEBUG)
    .constant('PENDER_SETTINGS', window.PENDER_SETTINGS || {
      'host': 'http://pender:3200',
      'key': 'dev'
    });
}());

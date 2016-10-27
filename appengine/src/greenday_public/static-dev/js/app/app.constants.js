/* global _:false, moment:false */
(function () {
	angular.module('app')
		.constant('_', _)
		.constant('moment', moment)
		.constant('DEBUG', window.DEBUG);
}());

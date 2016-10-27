/**
 * app Module
 *
 * The main application module
 */
(function () {
	angular.module('app', [
		'app.core',
		'app.services',
		'app.templates',
		'app.resources',
		'app.filters',
		'pages',
		'components'
	]);
}());

/**
 * app.core Module
 *
 * The core of our application
 */
(function () {
	angular.module('app.core', [
		'ngRoute',
		'ngAnimate',
		'ngMaterial',
		'angularMoment',
		'angulartics',
		'angulartics.google.analytics',
		'uiGmapgoogle-maps',
		'gdOnboarding',
		'LocalStorageModule',
		'angularStats',
		'cfp.hotkeys'
	]);
}());

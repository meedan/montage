/**
 * components Module
 *
 * The components module.
 * Contains all the shared directives.
 */

(function () {
	angular.module('components', [
		'app.services',
		'components.backdrop',
		'components.buttons',
		'components.dragDrop',
		'components.floatingElement',
		'components.lazyShow',
		'components.popup',
		'components.timedComment',
		'components.videoTimeline',
		'components.datepicker',
		'potato-datepicker',
		'ngSanitize'
	]);
}());

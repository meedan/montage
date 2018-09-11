(function () {
	angular
		.module('components.videoTimeline', ['app.services'])
		.component('foobar', window.AngularSample)
		.constant('TIMELINE_PX_PER_SECOND', 5);
}());

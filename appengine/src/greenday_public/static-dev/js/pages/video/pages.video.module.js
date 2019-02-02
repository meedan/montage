/**
 * Video Theatre module
 *
 * All content pertaining specifically to the video theatre pages belong in
 * this module.
 */
(function () {
	angular
		.module('pages.video', [])
		.component('barfoo', window.AngularVideoTimeline)
		// .component('foobar', window.AngularSample2)
		;
}());

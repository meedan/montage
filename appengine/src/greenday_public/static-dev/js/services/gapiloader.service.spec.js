describe('Unit: Testing services', function () {
	var GapiLoader,
		$window,
		$q,
		$timeout,
		winGapi = {gapi: true};

	beforeEach(module('app.services'));

	beforeEach(inject(function (_GapiLoader_, _$window_, _$q_, _$timeout_) {
		GapiLoader = _GapiLoader_;
		$window = _$window_;
		$q = _$q_;
		$timeout = _$timeout_;
	}));

	describe('GapiLoader service:', function () {

		it('should contain the GapiLoader', function() {
			expect(GapiLoader).not.toBe(null);
		});

		it('should return an object with load function', function() {
			expect(typeof GapiLoader.load).toBe('function');
		});

		it('should attach `onGapiLoaded` function to $window object', function () {
			expect($window.onGapiLoaded).toBeDefined();
		});

		it('should return a promise when calling load function', function() {
			var promise = GapiLoader.load();
			expect(promise).toBeDefined();
		});

		it('should have the `$window.gapi` object after calling `onGapiLoaded`', function() {
			var gapi;
			$window.gapi = winGapi;
			gapi = $window.onGapiLoaded();

			expect(gapi).toBe(winGapi);
		});

		it('should resolve the promise when calling `onGapiLoaded` function', function (done) {
			var mockDeferred = $q.defer();

			spyOn(GapiLoader, 'load').and.callFake(function () {
				return mockDeferred.promise;
			});

			spyOn($window, 'onGapiLoaded').and.callFake(function () {
				mockDeferred.resolve(winGapi);
			});

			GapiLoader.load().then(function () {
				done();
			});


			$timeout(function() {
				$window.onGapiLoaded();
			}, 1000); // This won't actually wait for 1 second.
			// `$timeout.flush()` will force it to execute.
			$timeout.flush(); // Force digest cycle to resolve promises
		});

	});
});

describe('Unit: Testing services', function () {
	var YouTubeDataService,
		$q,
		$timeout,
		$window,
		GapiLoader,
		oAuthParams,
		gapi = {
			client: {
				load: function (apiName, apiVersion) {}
			}
		};

	beforeEach(module('app.services'));

	beforeEach(inject(function (_YouTubeDataService_, _$q_, _$window_, _$timeout_, _GapiLoader_, _oAuthParams_) {
		YouTubeDataService = _YouTubeDataService_;
		$q = _$q_;
		$timeout = _$timeout_;
		$window = _$window_;
		GapiLoader = _GapiLoader_;
		oAuthParams = _oAuthParams_;
	}));


	describe('YouTubeDataService service:', function () {

		it('should contain the YouTubeDataService', function() {
			expect(YouTubeDataService).not.toBe(null);
		});

		it('should return an object with request method', function() {
			expect(typeof YouTubeDataService.request).toBe('function');
		});

	});
});

describe('Unit: Testing services', function () {
	var YouTubePlayerService,
		$q,
		$timeout,
		$window,
		GapiLoader,
		oAuthParams,
		YT = {
			ready: function(callback) {
				callback();
			},
			Player: function (container, params) {
				params.events.onReady();
				return {};
			}
		},
		gapi = {
			client: {
				load: function (apiName, apiVersion) {}
			}
		};

	beforeEach(module('app'));

	beforeEach(inject(function (_YouTubePlayerService_, _$q_, _$window_, _$timeout_, _GapiLoader_, _oAuthParams_) {
		YouTubePlayerService = _YouTubePlayerService_;
		$q = _$q_;
		$timeout = _$timeout_;
		$window = _$window_;
		GapiLoader = _GapiLoader_;
		oAuthParams = _oAuthParams_;
	}));


	describe('YouTubePlayerService service:', function () {

		it('should contain the YouTubePlayerService', function() {
			expect(YouTubePlayerService).not.toBe(null);
		});

		it('should return an object with a createVideo method', function() {
			expect(typeof YouTubePlayerService.createVideo).toBe('function');
			expect($window.onYouTubeIframeAPIReady()).toEqual($window.YT);
		});

		it('should load the api and create a player when calling createVideo', function(done) {
			var mockDeferred = $q.defer(),
				gapiLoaderDeferred = $q.defer();

			spyOn($window, 'onYouTubeIframeAPIReady').and.callThrough();

			YouTubePlayerService.createVideo(null, 'CAXtDPKkOlA').then(function () {
				done();
			});

			$timeout(function () {
				$window.YT = YT;
				$window.onYouTubeIframeAPIReady();
			});

			$timeout.flush();
		});
	});
});

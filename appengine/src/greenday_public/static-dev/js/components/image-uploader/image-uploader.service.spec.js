describe('Unit: Testing services', function () {
	var ImageUploader,
		GapiLoader,
		$q,
		$timeout,
		gapiLoaderDeferred,
		uploadDeferred,
		fileData,
		eventListener,
		gapi = {
			client: {
				request: function () {
					return { execute: function (callback) { callback({}); } };
				}
			},
			auth: {
				getToken: function () {
					return {
						access_token: '123456'
					};
				}
			}
		},
		XMLHttpRequestSpy = {
			open: function () {},
			setRequestHeader: function() {},
			upload: {
				addEventListener: eventListener
			},
			readyState: 4,
			status: 200,
			getResponseHeader: function (thing) {
				return 'https://www.googleapis.com/upload/storage/v1/b/project-images/o?uploadType=resumable&name=4_5ioYWMTIGrNfvKTc3AHQ.jpg&upload_id=AEnB2Uqh8TVkBbG6fTdSuBy3JMS5rb1H1sVedGu3BZkowe27xzPkOf0D6qXCECSIvc9nHC-6wGKVv2DBoY3ZiU_GHASGMGy_5A';
			},
			send: function() {
				var self = this,
					e = {
						target: {
							response: '{"kind":"storage#object","id":"project-images/4_5ioYWMTIGrNfvKTc3AHQ.jpg/1412956891848000","selfLink":"https://www.googleapis.com/storage/v1/b/project-images/o/4_5ioYWMTIGrNfvKTc3AHQ.jpg","name":"4_5ioYWMTIGrNfvKTc3AHQ.jpg","bucket":"project-images","generation":"1412956891848000","metageneration":"1","contentType":"image/jpeg","updated":"2014-10-10T16:01:31.847Z","storageClass":"STANDARD","size":"28327","md5Hash":"tEYFsqUnxz119Fg4A4JrlQ==","mediaLink":"https://www.googleapis.com/download/storage/v1/b/project-images/o/4_5ioYWMTIGrNfvKTc3AHQ.jpg?generation=1412956891848000&alt=media","owner":{"entity":"user-00b4903a97717b4045b8af737e4f7a818c9f2badc6f627ebfbff805fb8e1adb8","entityId":"00b4903a97717b4045b8af737e4f7a818c9f2badc6f627ebfbff805fb8e1adb8"},"crc32c":"YGy95A==","etag":"CMC6/My6osECEAE="}'
						}
					};
				$timeout(function () {
					if (self.onreadystatechange) {
						self.onreadystatechange(e);
					}
					if (self.onload) {
						self.onload(e);
					}
				});
			}
		},
		brokenXMLHttpRequestSpy;

	brokenXMLHttpRequestSpy = angular.copy(XMLHttpRequestSpy);
	brokenXMLHttpRequestSpy.send = function () {
		var self = this;
		$timeout(function () {
			self.status = 500;
			self.onreadystatechange({
				target: {
					response: '{"kind":"storage#object","id":"project-images/4_5ioYWMTIGrNfvKTc3AHQ.jpg/1412956891848000","selfLink":"https://www.googleapis.com/storage/v1/b/project-images/o/4_5ioYWMTIGrNfvKTc3AHQ.jpg","name":"4_5ioYWMTIGrNfvKTc3AHQ.jpg","bucket":"project-images","generation":"1412956891848000","metageneration":"1","contentType":"image/jpeg","updated":"2014-10-10T16:01:31.847Z","storageClass":"STANDARD","size":"28327","md5Hash":"tEYFsqUnxz119Fg4A4JrlQ==","mediaLink":"https://www.googleapis.com/download/storage/v1/b/project-images/o/4_5ioYWMTIGrNfvKTc3AHQ.jpg?generation=1412956891848000&alt=media","owner":{"entity":"user-00b4903a97717b4045b8af737e4f7a818c9f2badc6f627ebfbff805fb8e1adb8","entityId":"00b4903a97717b4045b8af737e4f7a818c9f2badc6f627ebfbff805fb8e1adb8"},"crc32c":"YGy95A==","etag":"CMC6/My6osECEAE="}'
				}
			});
		});
	};


	beforeEach(function () {
		module('components');
		module('app.services');
	});

	beforeEach(inject(function (_ImageUploader_, _$q_, _$timeout_, _GapiLoader_) {
		ImageUploader = _ImageUploader_;
		$q = _$q_;
		$timeout = _$timeout_;
		GapiLoader = _GapiLoader_;

		gapiLoaderDeferred = $q.defer();
		uploadDeferred = $q.defer();

		fileData = {

		};
	}));

	describe('ImageUploader service:', function () {
		it('should contain the ImageUploader', function() {
			expect(ImageUploader).not.toBe(null);
		});

		it('should return an object with functions', function() {
			expect(typeof ImageUploader.upload).toBe('function');
		});

		beforeEach(function () {
			eventListener = jasmine.createSpy();

			spyOn(GapiLoader, 'load').and.returnValue(gapiLoaderDeferred.promise);
			spyOn(ImageUploader, 'upload').and.callThrough();
		});

		it('should upload an image', function (done) {
			spyOn(window, 'XMLHttpRequest').and.returnValue(XMLHttpRequestSpy);
			ImageUploader.upload(fileData).then(function () {
				done();
			});

			gapiLoaderDeferred.resolve(gapi);

			$timeout.flush();
		});

		it('should fail to upload an image', function (done) {
			spyOn(window, 'XMLHttpRequest').and.returnValue(brokenXMLHttpRequestSpy);
			ImageUploader.upload(fileData).then(function () {
				// We shouldn't be here.
			}, function () {
				done();
			});

			gapiLoaderDeferred.resolve(gapi);

			$timeout.flush();
		});
	});
});

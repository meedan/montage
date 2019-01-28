describe('Unit: Testing services', function () {
	var ImageUploader,
		GapiLoader,
		$q,
		$timeout,
		$httpBackend,
		gapiLoaderDeferred,
		uploadDeferred,
		fileData,
		eventListener,
    fakeProject = {
      'is_list': true,
    },
		fakeUser = {
			'accepted_nda': true,
			'email': 'someone@somewhere.com',
			'first_name': '',
			'gaia_id': '1234567890',
			'id': '1',
			'is_active': true,
			'is_googler': false,
			'is_staff': false,
			'is_superuser': false,
			'language': 'en',
			'last_login': '2014-09-17T10:53:42+00:00',
			'last_name': '',
			'username': '1234567890'
		},
		fakeProfile = {
			'kind': 'people#person',
			'etag': '\"KJHSFVCB8273ryfghHJGSLF/KJHSFVCB8273ryfghHJGSLF\"',
			'gender': 'male',
			'emails': [{
				'value': 'someone@somewhere.com',
				'type': 'account'
			}],
			'objectType': 'person',
			'id': '1234567890',
			'displayName': 'Someone Awesome',
			'names': [{
				'familyName': 'Awesome',
				'givenName': 'Someone'
			}],
			'urls': [{
        'value': 'https://plus.google.com/1234567890'
      }],
			'photos': [{
				'url': 'https://lh5.googleusercontent.com/-mV0aK-lwZHoW7ukXRMSdCAtOAWpKPgsHl0rYP7giTs?sz=50',
				'isDefault': false
			}],
			'isPlusUser': true,
			'locales': [{
        'value': 'en_GB'
      }],
			'circledByCount': 0,
			'verified': false,
			'domain': 'somewhere.com'
		},
		fakeUserWithProfile = {
			'accepted_nda': true,
			'email': 'someone@somewhere.com',
			'first_name': 'Someone',
			'gaia_id': '1234567890',
			'id': '1',
			'is_active': true,
			'is_googler': false,
			'is_staff': false,
			'is_superuser': false,
			'language': 'en_GB',
			'last_login': '2014-09-17T10:53:42+00:00',
			'last_name': 'Awesome',
			'username': '1234567890',
			'profile_img_url': 'https://lh5.googleusercontent.com/-mV0aK-lwZHoW7ukXRMSdCAtOAWpKPgsHl0rYP7giTs',
			'google_plus_profile': 'https://plus.google.com/1234567890'
		},
    googleAuth = {
      isSignedIn: {
        get: function () {
          return true;
        }
      },
      currentUser: {
        get: function () {
          return {
            getAuthResponse: function (bool) {
              return { access_token: '123456' };
            },
            reloadAuthResponse: function() {
              return {
                then: function (callback) {
                  callback({});
                  return {
                    catch: function (callback) { callback({}); }
                  };
                }
              };
            }
          };
        }
      }
    },
		gapi = {
			auth2: {
				init: function (params) {
          return {
            then: function (callback) {
              callback(googleAuth);
            }
          };
        }
			},
			client: {
				load: function (apiName, apiVersion, callback) { callback(); },
				setApiKey: function (apiKey) {},
				people: {
					people: {
						get: function (params) {
							return { execute: function (callback) { callback(fakeProfile); } };
						}
					}
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


	beforeEach(module('app'));

	beforeEach(inject(function (_ImageUploader_, _$q_, _$timeout_, _$httpBackend_, _GapiLoader_) {
		ImageUploader = _ImageUploader_;
		$q = _$q_;
		$timeout = _$timeout_;
		$httpBackend = _$httpBackend_;
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

			$httpBackend.expectGET('users/me').respond(fakeUser);
			$httpBackend.expectGET('project').respond(fakeProject);
			$httpBackend.expectPUT('users/me').respond(fakeUserWithProfile);

			gapiLoaderDeferred.resolve(gapi);

			$timeout.flush();
			$httpBackend.flush();
		});

		it('should fail to upload an image', function (done) {
			spyOn(window, 'XMLHttpRequest').and.returnValue(brokenXMLHttpRequestSpy);
			ImageUploader.upload(fileData).then(function () {
				// We shouldn't be here.
			}, function () {
				done();
			});

			$httpBackend.expectGET('users/me').respond(fakeUser);
			$httpBackend.expectGET('project').respond(fakeProject);
			$httpBackend.expectPUT('users/me').respond(fakeUserWithProfile);

			gapiLoaderDeferred.resolve(gapi);

			$timeout.flush();
			$httpBackend.flush();
		});
	});
});

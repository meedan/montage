describe('Unit: Testing services', function () {
	var GapiLoader,
		$window,
		$q,
		$timeout,
		$httpBackend,
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
          return false;
        }
      },
      signIn: function() {
        return {
          then: function (callback) {
            callback({});
            return {
              catch: function (callback) { callback({ access_token: '123456' }); }
            };
          }
        };
      },
      signOut: function() {
        return {
          then: function (callback) { callback(); },
          fail: function (callback) { callback(); }
        };
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
                    catch: function (callback) { callback({ access_token: '123456' }); }
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
		winGapi = gapi;

	beforeEach(module('app'));

	beforeEach(inject(function (_GapiLoader_, _$window_, _$q_, _$timeout_, _$httpBackend_) {
		GapiLoader = _GapiLoader_;
		$window = _$window_;
		$q = _$q_;
		$timeout = _$timeout_;
		$httpBackend = _$httpBackend_;
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
			$httpBackend.expectGET('users/me').respond(fakeUser);
			$httpBackend.expectGET('project').respond(fakeProject);
			$httpBackend.expectPUT('users/me').respond(fakeUserWithProfile);

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
			$httpBackend.flush();
		});

	});
});

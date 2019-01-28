describe('Unit: Testing services', function () {
	var UserService,
		$window,
    UserModel,
		GapiLoader,
		token = 'usertoken123',
		$q,
		$timeout,
		$httpBackend,
    fakeProject = {
      'is_list': true,
    },
		fakeUserStats = {
			'id': 99,
			'videos_watched': 42,
			'tags_added': 12
		},
		fakeUser = {
			'accepted_nda': true,
			'email': 'someone@somewhere.com',
			'first_name': 'Someone',
			'gaia_id': '1234567890',
			'id': '1',
			'is_active': true,
			'is_googler': false,
			'is_staff': false,
			'is_superuser': false,
			'language': 'en',
			'last_login': '2014-09-17T10:53:42+00:00',
			'last_name': '',
			'username': '1234567890',
      'DSSave': function() { },
      'getStats': function() {
        return {
          then: function(callback) {
            callback(fakeUserStats);
          }
        };
      },
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
          then: function (callback) {
            callback({});
            return {
              catch: function (callback) { callback({}); }
            };
          }
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
		gapiLoaderDeferred,
		authDeferred,
		getUserDeferred;

	beforeEach(module('app'));

	beforeEach(inject(function (_UserService_, _$window_, _$q_, _$timeout_, _$httpBackend_, _GapiLoader_, _UserModel_) {
		UserService = _UserService_;
		$window = _$window_;
    $window.googleAuth = googleAuth;
    UserModel = _UserModel_;
		$q = _$q_;
		$timeout = _$timeout_;
		$httpBackend = _$httpBackend_;
		GapiLoader = _GapiLoader_;
	}));

	describe('User service:', function () {

		it('should contain the UserService', function() {
			expect(UserService).not.toBe(null);
		});

		it('should return an object with functions', function() {
			expect(typeof UserService.auth).toBe('function');
			expect(typeof UserService.getUser).toBe('function');
			expect(typeof UserService.signOut).toBe('function');
			expect(typeof UserService.getUserStats).toBe('function');
		});

		describe('auth flow', function () {
			beforeEach(function () {
				gapiLoaderDeferred = $q.defer();
				authDeferred = $q.defer();
				getUserDeferred = $q.defer();

				spyOn(GapiLoader, 'load').and.returnValue(gapiLoaderDeferred.promise);
				spyOn(UserService, 'auth').and.returnValue(authDeferred.promise);
				spyOn(UserService, 'getUser').and.callThrough();
				spyOn(UserService, 'signOut').and.callThrough();
				spyOn(UserService, 'setGoogleAuth').and.callThrough();
        UserService.setGoogleAuth(googleAuth);
			});

			it('should authorize the user', function (done) {
				spyOn(UserModel, 'find').withArgs('me').and.returnValue({
          then: function(callback) {
            callback(fakeUser);
          }
        });
				$httpBackend.expectGET('project').respond(fakeProject);

				UserService.getUser().then(function (user) {
          expect(user.first_name).toBe('Someone');
					done();
				});

				gapiLoaderDeferred.resolve(gapi);

				$timeout.flush();
				$httpBackend.flush();
			});

			it('should authorize the user without a profile_url', function (done) {
				spyOn(UserModel, 'find').withArgs('me').and.returnValue({
          then: function(callback) {
            callback(fakeUser);
          }
        });
				$httpBackend.expectGET('project').respond(fakeProject);

        UserService.getUser().then(function (user) {
          expect(user.first_name).toBe('Someone');
					done();
				});

				var profile = angular.copy(fakeProfile);
				profile.image = {};

				var fakeGapi = angular.copy(gapi);
				fakeGapi.client.people.people.get = function (params) {
					return { execute: function (callback) { callback(profile); } };
				};

				gapiLoaderDeferred.resolve(fakeGapi);

				$timeout.flush();
				$httpBackend.flush();
			});

			it('should reject the promise if the user didn\'t allow the permissions', function (done) {
				spyOn(UserModel, 'find').withArgs('me').and.returnValue({
          then: function(callback, reject) {
            reject({ data: { error: 'I just do not like you' } });
          }
        });

				UserService.getUser(true).then(function () {
					// we shouldn't be here
				}, function (reason) {
					done();
				});

				gapiLoaderDeferred.resolve(gapi);

				$timeout.flush();
			});

			it('should signout', function (done) {
				spyOn(UserModel, 'find').withArgs('me').and.returnValue({
          then: function(callback) {
            callback(fakeUser);
          }
        });
				$httpBackend.expectGET('project').respond(fakeProject);

        UserService.signOut().then(function () {
					done();
				});

				gapiLoaderDeferred.resolve(gapi);

				$timeout.flush();
				$httpBackend.flush();
			});

			it('should get the user stats', function (done) {
				spyOn(UserModel, 'find').withArgs('me').and.returnValue({
          then: function(callback) {
            callback(fakeUser);
          }
        });
				$httpBackend.expectGET('project').respond(fakeProject);

        UserService.getUser().then(function () {
					UserService.getUserStats().then(function () {
						done();
					});
				});

				gapiLoaderDeferred.resolve(gapi);

				$timeout.flush();
				$httpBackend.flush();
			});

			it('should cache the user stats', function (done) {
				spyOn(UserModel, 'find').withArgs('me').and.returnValue({
          then: function(callback) {
            callback(fakeUser);
          }
        });
				$httpBackend.expectGET('project').respond(fakeProject);

        UserService.getUser().then(function () {
					UserService.getUserStats().then(function () {
						UserService.getUserStats().then(function () {
							done();
						});
					});
				});

				gapiLoaderDeferred.resolve(gapi);

				$timeout.flush();
				$httpBackend.flush();
			});

			it('should force the user stats to be retrieved', function (done) {
				spyOn(UserModel, 'find').withArgs('me').and.returnValue({
          then: function(callback) {
            callback(fakeUser);
          }
        });
				$httpBackend.expectGET('project').respond(fakeProject);

        UserService.getUserStats().then(function () {
					UserService.getUserStats(true).then(function () {
						done();
					});
				});

				gapiLoaderDeferred.resolve(gapi);

				$timeout.flush();
				$httpBackend.flush();
			});
		});
	});
});

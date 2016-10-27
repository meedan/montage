describe('Unit: Testing services', function () {
	var UserService,
		GapiLoader,
		token = 'usertoken123',
		$q,
		$timeout,
		$httpBackend,
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
			'kind': 'plus#person',
			'etag': '\"KJHSFVCB8273ryfghHJGSLF/KJHSFVCB8273ryfghHJGSLF\"',
			'gender': 'male',
			'emails': [{
				'value': 'someone@somewhere.com',
				'type': 'account'
			}],
			'objectType': 'person',
			'id': '1234567890',
			'displayName': 'Someone Awesome',
			'name': {
				'familyName': 'Awesome',
				'givenName': 'Someone'
			},
			'url': 'https://plus.google.com/1234567890',
			'image': {
				'url': 'https://lh5.googleusercontent.com/-mV0aK-lwZHoW7ukXRMSdCAtOAWpKPgsHl0rYP7giTs?sz=50',
				'isDefault': false
			},
			'isPlusUser': true,
			'language': 'en_GB',
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
		fakeUserStats = {
			'id': 99,
			'videos_watched': 42,
			'tags_added': 12
		},
		gapi = {
			auth: {
				init: function (callback) { callback(); },
				authorize: function (params, callback) { callback(true); },
				getToken: function () { return {access_token: '123456'}; }
			},
			client: {
				load: function (apiName, apiVersion, callback) { callback(); },
				setApiKey: function (apiKey) {},
				plus: {
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

	beforeEach(module('app.services'));

	beforeEach(inject(function (_UserService_, _$q_, _$timeout_, _$httpBackend_, _GapiLoader_) {
		UserService = _UserService_;
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
			});

			it('should authorize the user', function (done) {
				UserService.getUser().then(function () {
					done();
				});

				$httpBackend
					.expectGET('/users/me')
					.respond(fakeUser);

				$httpBackend
					.expectPUT('/users/me')
					.respond(fakeUserWithProfile);

				gapiLoaderDeferred.resolve(gapi);

				$timeout.flush();
				$httpBackend.flush();
			});

			it('should authorize the user without a profile_url', function (done) {
				UserService.getUser().then(function () {
					done();
				});

				var profile = angular.copy(fakeProfile);
				profile.image = {};

				var fakeGapi = angular.copy(gapi);
				fakeGapi.client.plus.people.get = function (params) {
					return { execute: function (callback) { callback(profile); } };
				};


				$httpBackend
					.expectGET('/users/me')
					.respond(fakeUser);

				$httpBackend
					.expectPUT('/users/me')
					.respond(fakeUserWithProfile);

				gapiLoaderDeferred.resolve(fakeGapi);

				$timeout.flush();
				$httpBackend.flush();
			});

			it('should reject the promise if the user didn\'t allow the permissions', function (done) {
				var rejectGapi = angular.copy(gapi);

				rejectGapi.auth.authorize = function (params, callback) {
					callback({
						error: 'I just do not like you.'
					});
				};

				UserService.getUser(true).then(function () {
					// we shouldn't be here
				}, function (reason) {
					done();
				});

				gapiLoaderDeferred.resolve(rejectGapi);

				$timeout.flush();
			});

			it('should signout', function (done) {
				UserService.signOut().then(function () {
					done();
				});

				$httpBackend
					.expectJSONP('https://accounts.google.com/o/oauth2/revoke?token=123456&callback=JSON_CALLBACK')
					.respond(fakeUser);

				gapiLoaderDeferred.resolve(gapi);

				$timeout.flush();
				$httpBackend.flush();
			});

			it('should fail signing out', function (done) {
				UserService.signOut().then(function () {
					// we shouldn't be here
				}, function () {
					done();
				});

				$httpBackend
					.expectJSONP('https://accounts.google.com/o/oauth2/revoke?token=123456&callback=JSON_CALLBACK')
					.respond(403);

				gapiLoaderDeferred.resolve(gapi);

				$timeout.flush();
				$httpBackend.flush();
			});

			it('should get the user stats', function (done) {
				UserService.getUser().then(function () {
					UserService.getUserStats().then(function () {
						done();
					});
				});

				$httpBackend
					.expectGET('/users/me')
					.respond(fakeUser);

				$httpBackend
					.expectGET('/users/me/stats')
					.respond(fakeUserStats);

				$httpBackend
					.expectPUT('/users/me')
					.respond(fakeUserWithProfile);

				gapiLoaderDeferred.resolve(gapi);

				$timeout.flush();
				$httpBackend.flush();
			});

			it('should cache the user stats', function (done) {
				UserService.getUser().then(function () {
					UserService.getUserStats().then(function () {
						UserService.getUserStats().then(function () {
							done();
						});
					});
				});

				$httpBackend
					.expectGET('/users/me')
					.respond(fakeUser);

				$httpBackend
					.expectGET('/users/me/stats')
					.respond(fakeUserStats);

				$httpBackend
					.expectPUT('/users/me')
					.respond(fakeUserWithProfile);

				gapiLoaderDeferred.resolve(gapi);

				$timeout.flush();
				$httpBackend.flush();
			});

			it('should force the user stats to be retrieved', function (done) {
				UserService.getUserStats().then(function () {
					UserService.getUserStats(true).then(function () {
						done();
					});
				});

				$httpBackend
					.expectGET('/users/me')
					.respond(fakeUser);

				$httpBackend
					.expectGET('/users/me/stats')
					.respond(fakeUserStats);

				$httpBackend
					.expectPUT('/users/me')
					.respond(fakeUserWithProfile);

				$httpBackend
					.expectGET('/users/me/stats')
					.respond(fakeUserStats);

				gapiLoaderDeferred.resolve(gapi);

				$timeout.flush();
				$httpBackend.flush();
			});
		});
	});
});

/**
 * gapiloader service
 *
 */
(function () {
    angular
        .module('app.services')
        .factory('UserService', UserService);

    /** @ngInject */
    function UserService($timeout, $q, $http, $rootScope, $location, moment, GapiLoader, oAuthParams, oAuthRefreshDelay, UserModel, DialogService, PageService, ToastService) {
        var service = {
                auth: auth,
                getUser: getUser,
                signOut: signOut,
                showSettings: showSettings,
                deleteAccount: deleteAccount,
                queryUserContacts: queryUserContacts,
                getUserStats: getUserStats,
                acceptNDA: acceptNDA,
                authorizationToken: authorizationToken,
                setGoogleAuth: setGoogleAuth
            },
            userFetchInProgress = false,
            authDeferred = null,
            authPromise = null,
            userDeferred = null,
            userPromise = null,
            userStatsDeferred = null,
            gapi = null,
            googleAuth = null,
            user,
            userStats,
            authResult;

        return service;

        function setGoogleAuth(ga) {
            googleAuth = ga;
        }

        function authorizationToken() {
            var defer = $q.defer();
            auth().then(function (data) {
                    var accessToken = 'Bearer ' + data.access_token;
                    defer.resolve(accessToken);
                },
                function (error) {
                    //feel free to $log or whateever
                    defer.reject(error);
                });
            return defer.promise;
        }

        function getToken() {
            var user = getCurrentUser();
            return user.getAuthResponse(true).access_token;
        }

        function getCurrentUser() {
            return googleAuth.currentUser.get();
        }

        function auth(immediate) {
            authDeferred = $q.defer();
            authPromise = authDeferred.promise;

            GapiLoader.load().then(function (windowGapi) {
                gapi = windowGapi;
                gapi.client.setApiKey(oAuthParams.api_key);
                gapi.auth2.init(oAuthParams).then(function (result) {
                    googleAuth = result;
                    authorizeUser(immediate);
                });

                userFetchInProgress = false;
            }, function () {
                userFetchInProgress = false;
            });
            return authPromise;
        }

        function queryUserContacts(query) {
            var usersQueryDeferred = $q.defer();
            $http
                .jsonp('https://www.google.com/m8/feeds/contacts/default/thin?v=3&callback=JSON_CALLBACK&alt=json&q=' + query + '&access_token=' + getToken())
                .then(function (response) {
                    if (response.status === 200) {
                        usersQueryDeferred.resolve(response.data.feed.entry);
                    } else {
                        usersQueryDeferred.reject(response);
                    }
                });
            return usersQueryDeferred.promise;
        }

        function authorizeUser(immediate) {
            var params = angular.copy(oAuthParams);
            var nowInSeconds = Math.round(new Date().getTime() / 1000);
            params.prompt = angular.isUndefined(immediate) ? 'none' : (immediate ? 'none' : 'consent');

            var done = function (result) {
                if (!result || result.error) {
                    fail(result);
                    return;
                }
                $http.defaults.headers.common.Authorization = 'Bearer ' + result.access_token;
                authResult = result;
                $timeout(authorizeUser, oAuthRefreshDelay);
                authDeferred.resolve(result);
            };

            var fail = function (result) {
                authDeferred.reject({
                    reason: result.error
                });
            };

            //we want to refresh the token 15mins (900 seconds) before the expiration time
            if (authResult && nowInSeconds < parseInt(authResult.expires_at, 10) - 900) {
                authDeferred.resolve(authResult);
            } else {
                var user = getCurrentUser();

                if (googleAuth.isSignedIn.get()) {
                    user.reloadAuthResponse().then(done).catch(fail);
                } else {
                    googleAuth.signIn().then(done).catch(fail);
                }
            }
        }

        function getUser(immediate) {
            if (!user && userFetchInProgress === false) {
                userFetchInProgress = true;

                userDeferred = $q.defer();
                userPromise = userDeferred.promise;

                auth(immediate).then(function () {
                    var gdUserDfd = $q.defer();
                    var gPlusUserDfd = $q.defer();
                    var allUserData;

                    $rootScope.$broadcast('user:signIn:start', user);
                    $http.defaults.headers.common.Authorization = 'Bearer ' + getToken();

                    // Fetch Montage User
                    UserModel
                        .find('me')
                        .then(function (gdUserData) {
                            gdUserDfd.resolve(gdUserData);

                            if (gdUserData.accepted_nda) {
                                user = gdUserData;
                                user.signOut = signOut;
                                user.showSettings = showSettings;
                                userDeferred.resolve(user);
                                $rootScope.$broadcast('user:signIn:complete', user);
                            } else {
                                userDeferred.reject({
                                    reason: 'not_accepted_nda',
                                    user: gdUserData
                                });
                                $rootScope.$broadcast('user:signIn:failed', {
                                    reason: 'not_accepted_nda',
                                    user: gdUserData
                                });
                            }
                        }, function (response) {
                            gdUserDfd.reject(response);
                        });

                    gdUserDfd.promise.then(function (gdUserData) {
                        var google_plus_profile = gdUserData.google_plus_profile;
                        var lastLogin = moment.utc(gdUserData.last_login);
                        var now = moment.utc();

                        // Fetch the users G+ profile if they last logged in
                        // over 4 hours ago. We also fetch the google plus profile
                        // if the google plus profile is not set on the user object.
                        // This is to cater for when new users are invited to a project.
                        // An account gets created and activated for them, but because
                        // data is not carried out.
                        if (now.diff(lastLogin, 'hours') > 4 || !google_plus_profile) {
                            gapi.client.load('people', 'v1', function () {
                                var request = gapi.client.people.people.get({
                                    'resourceName': 'people/me',
                                    'personFields': 'photos,addresses,emailAddresses,names,locales,urls'
                                });
                                request.execute(function (profile) {
                                    gPlusUserDfd.resolve(profile);
                                });

                            });
                        } else {
                            gPlusUserDfd.reject('No update needed');
                        }
                    }, function (reason) {
                        userFetchInProgress = false;
                        userDeferred.reject(reason);
                        ToastService.showError(reason.data.error.message, 5000);
                        signOut();
                    });

                    // When we have both the Montage and Google Plus user
                    // attach the profile. This only happens if the last_login
                    // time is over the 4 hour threshold, so that we limit the
                    // number of PUTs we do to the Montage API.
                    allUserData = $q.all([gdUserDfd.promise, gPlusUserDfd.promise]);
                    allUserData.then(function (responses) {
                        var gdUserData = responses[0],
                            gPlusUserData = responses[1];

                        attachUserProfile(gdUserData, gPlusUserData);
                        gdUserData.DSSave();
                    });

                    allUserData.finally(function () {
                        userFetchInProgress = false;
                        PageService.stopLoading();
                    });

                }, function (reason) {
                    userFetchInProgress = false;
                    userDeferred.reject(reason);
                    if ($location.path() !== '/welcome') {
                        $location.path('/welcome');
                    }
                });
            }

            return userPromise;
        }

        function getUserStats(force) {
            if (!userStats || force) {
                userStatsDeferred = $q.defer();

                getUser(true)
                    .then(function (user) {
                        user.getStats()
                            .then(function (stats) {
                                userStats = stats;
                                userStatsDeferred.resolve(userStats);
                            });
                    }, function (reason) {
                        userStatsDeferred.reject(reason);
                    });
            }

            return userStatsDeferred.promise;
        }

        function attachUserProfile(user, profile) {
            var profile_img = profile.photos[0].url;//image.url ? profile.image.url.split('?')[0] : '';
            user.first_name = profile.names[0].givenName;
            user.last_name = profile.names[0].familyName;
            user.profile_img_url = profile_img;
            user.language = profile.locales[0].value;
            if (profile.hasOwnProperty('urls')) {
                user.google_plus_profile = profile.urls[0].value;
            } else {
                user.google_plus_profile = null;
            }
            user.last_login = moment.utc().format();
            return user;
        }

        function signOut() {
            var revokeDeferred = $q.defer(),
                revokePromise = revokeDeferred.promise;

            var done = function (response) {
                PageService.clearDataCache();
                revokeDeferred.resolve(response);
                $rootScope.$broadcast('user:signOut:complete', user);
                user = null;
                authResult = null;
            };

            var fail = function (response) {
                revokeDeferred.reject(response);
                $rootScope.$broadcast('user:signOut:fail', user);
            };

            GapiLoader.load().then(function (gapi) {
                $rootScope.$broadcast('user:signOut:start', user);
                googleAuth.signOut().then(done).catch(fail);
            });

            return revokePromise;
        }

        function showSettings($event) {
            DialogService.showUserSettingsDialog($event, user);
        }

        function deleteAccount($event) {
            DialogService.confirm($event, 'Are you sure?').then(function () {
                getUser(true)
                    .then(function (user) {
                        user.DSDestroy()
                            .then(function () {
                                signOut();
                            });
                    });
            });
        }

        function acceptNDA() {
            var acceptNDADeferred = $q.defer();
            UserModel
                .acceptNDA()
                .then(function (response) {
                    UserModel
                        .find('me')
                        .then(function (gdUserData) {
                            gdUserData.accepted_nda = true;
                            acceptNDADeferred.resolve(gdUserData);
                        });
                });
            return acceptNDADeferred.promise;
        }
    }
}());

(function () {

    angular
        .module('app.services')
        .factory('HeapService', HeapService);

    /** @ngInject */
    function HeapService($rootScope, UserService) {
        return {
            engage: engage
        };

        function engage() {
            $rootScope.$on('user:signIn:complete', function () {
                UserService.getUser().then(function (user) {
                    if (window.heap) {
                        heap.identify({
                            handle: user.email
                        });
                    }
                    if (window.FS) {
                        FS.identify(user.id, {
                            displayName: user.first_name + ' ' + user.last_name,
                            email: user.email
                        });
                    }
                });
            });
        }
    }
})();

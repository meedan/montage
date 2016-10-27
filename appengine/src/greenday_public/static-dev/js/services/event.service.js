/**
 * Event subscription service
 *
 */
(function () {
	angular
		.module('app.services')
		.constant('CHANNELS_API_BASE', window.CHANNELS_API_BASE)
		.factory('EventService', EventService);

	/** @ngInject */
	function EventService (_, $timeout, $q, $log, $http, CHANNELS_API_BASE) {
		var service = {
				pull: pull,
				setProject: setProject,
				setVideo: setVideo,
				subscribe: subscribe,
				currentProjectId: null,
				currentVideoId: null,
				getChannels: getChannels
			},
			currentPullRequestDeferred = null,
			pullDeferred = null,
			subscribeDeferred = null,
			unsubscribeDeferred = null,
			abortPullDeferred = null,
			subscribers = {
				all: []
			},
			token = null,
			failedPulls = 0;

		function doPull() {
			if (!pullDeferred) {
				var channels = getChannels();

				if (!token || !channels.length) {
					$log.debug('EventService:No channels');
					return;
				}

				pullDeferred = $q.defer();
				abortPullDeferred = $q.defer();

				$http.get(CHANNELS_API_BASE + '/pull/', {
						params: {
							channels: channels.join(','),
							token: token
						},
						timeout: abortPullDeferred.promise
					})
					.success(function (data, status, headers, config, statusText) {
						if (pullDeferred) {
							pullDeferred.resolve();
							pullDeferred = null;

							if (status === 200) {
								failedPulls = 0;

								if (data !== null) {
									var items = JSON.parse(data.items);
									dispatch(_.pluck(items, 'message'));
								}

								doPull();
							}
							else {
								failedPulls += 1;
								$timeout(doPull, backoff(Math.min(failedPulls, 8)));
							}
						}
					});
			}

			return pullDeferred.promise;
		}

		function doSubscribe() {
			$http.post(CHANNELS_API_BASE + '/subscribe/', {}, {
				params: {
					channels: getChannels().join(',')
				},
				timeout: subscribeDeferred.promise
			})
			.then(function(response) {
				token = response.data.token;
			})
			.then(doPull)
			.then(subscribeDeferred.resolve);
		}

		function pull(callback, objectType) {
			registerListener(callback, objectType);

			if (!subscribeDeferred) {
				subscribe();
			}
		}

		function registerListener(callback, objectType) {
			if (objectType) {
				if (_.isUndefined(subscribers[objectType])){
					subscribers[objectType] = [];
				}

				if (!_.contains(subscribers[objectType], callback)) {
					subscribers[objectType].push(callback);
				}
			} else if (!_.contains(subscribers.all, callback)) {
				subscribers.all.push(callback);
			}
		}

		function setProject(projectId) {
			if (!projectId || service.currentProjectId !== projectId) {
				if (subscribeDeferred) {
					subscribeDeferred.reject();
					unsubscribe();
				}

				service.currentProjectId = projectId;
			}

			if (projectId) {
				subscribe();
			}

			return subscribeDeferred;
		}

		function setVideo(videoId, projectId) {
			if (projectId) {
				setProject(projectId);
			}

			if (!videoId || service.currentVideoId !== videoId) {
				if (subscribeDeferred) {
					subscribeDeferred.reject();
					unsubscribe();
				}

				service.currentVideoId = videoId;
			}

			if (videoId) {
				subscribe();
			}

			return subscribeDeferred;
		}

		function subscribe() {
			if (subscribeDeferred) {
				$log.debug('EventService:subscribe already in progress');
				return;
			}

			subscribeDeferred = $q.defer();

			if (unsubscribeDeferred) {
				unsubscribeDeferred.promise.then(function() {
					doSubscribe();
				});
			}
			else {
				doSubscribe();
			}

			return subscribeDeferred.promise;
		}

		function unsubscribe() {
			if (!token) {
				$log.debug("No token to unsubscribe");
			}

			if (unsubscribeDeferred) {
				$log.debug('EventService:unsubscribe already in progress');
				return;
			}

			unsubscribeDeferred = $q.defer();

			$http.post(CHANNELS_API_BASE + '/unsubscribe/', {
				channels: getChannels().join(','),
				token: token
			})
			.finally(function () {
				unsubscribeDeferred.resolve();
				unsubscribeDeferred = null;
			});

			if (abortPullDeferred) {
				abortPullDeferred.resolve();
			}

			if (pullDeferred) {
				pullDeferred.reject();
			}

			if (subscribeDeferred) {
				subscribeDeferred.reject();
			}

			pullDeferred = null;
			subscribeDeferred = null;

			return unsubscribeDeferred.promise;
		}

		function dispatch(messages) {
			angular.forEach(messages, function(message) {
				angular.forEach(subscribers[message.event.object_type], function(subscriberCallback) {
					subscriberCallback(message);
				});
			});

			angular.forEach(subscribers.all, function(subscriberCallback) {
				angular.forEach(messages, subscriberCallback);
			});
		}

		function getChannels() {
			var channels = [];

			if (service.currentProjectId) {
				channels.push('projectid-' + service.currentProjectId);
			}

			if (service.currentVideoId) {
				channels.push('videoid-' + service.currentVideoId);
			}

			return channels;
		}

		return service;

		function backoff(n) {
			return (Math.pow(2, n)*100) + (Math.round(Math.random() * 100));
		}
	}
})();

var deferredApp = angular.module('deferredApp', ['ngRoute', 'ui.bootstrap']);

var LOG_LEVELS = {
	0: 'debug',
	1: 'info',
	2: 'warning',
	3: 'error',
	4: 'critical'
};

var maxFetch = 10;

deferredApp.constant('appSettings', {
	apiRootUrl: getRoot()
});

deferredApp.config(function($routeProvider) {
	$routeProvider

		.when('/:queueId/:taskId', {
			controller: 'TaskCtrl',
			templateUrl: 'templates/taskdetail.html'
		})
		.when('/', {
			controller: 'HomeCtrl',
			templateUrl: 'templates/home.html'
		})
		.otherwise({
			redirectTo: '/'
		});
});

deferredApp.controller('HomeCtrl', function($scope, $http, $q, appSettings) {
	var ctlr = this;

	$scope.autorefresh = false;
	$scope.refreshInterval = 8;
	$scope.queueNames = [];
	$scope.columns = 3;

	$http.get(appSettings.apiRootUrl)
		.then(function(resp) {
			resp.data.queues.forEach(function(queue) {
				$scope.queueNames.push(queue.name);
			});
			$scope.columns = Math.min(resp.data.queues.length, 3);
		});
});

deferredApp.controller('QueueCtrl', function($scope, $http, appSettings) {
	var etaDeltaIntervalID;
	$scope.queue = {};
	$scope.getTasks = getTasks;
	$scope.loadMoreTasks = loadMoreTasks;

	getTasks($scope.queue);

	$scope.getTaskStatusMsg = function(task) {
		if (task.was_purged) {
			return 'purged';
		}

		if (task.is_permanently_failed) {
			return 'failed';
		}

		if (task.is_complete) {
			return;
		}

		if (task.is_running) {
			if (task.retry_count) {
				return 'running - attempt ' + (task.retry_count + 1);
			}
			return 'running';
		}

		if (!task.is_complete && !task.is_permanently_failed) {
			if (task.retry_count) {
				return 'pending - failed ' + (task.retry_count + 1) + ' times';
			}
			else if (task.first_run) {
				return 'pending - failed once';
			}
			return 'pending';
		}
	};

	$scope.purgeQueue = function() {
		$http.delete(appSettings.apiRootUrl + $scope.queueName).then(getTasks);
	};

	$scope.$watchCollection('[autorefresh, refreshInterval]', function(val) {
		if ($scope.autorefresh) {
			getTasks();
		}
		else if ($scope.queue) {
			clearTimeout($scope.queue.timeoutID);
		}
	});

	function setOldestEtaDelta() {
		if ($scope.queue && $scope.queue.stats && $scope.queue.stats.oldest_eta) {
			var now = new Date();
			if ($scope.queue.stats.oldest_eta > now) {
				$scope.oldestEtaSuffix = 'from now';
				$scope.oldestEtaDelta = new Date($scope.queue.stats.oldest_eta - now);
			}
			else {
				$scope.oldestEtaSuffix = 'ago';
				$scope.oldestEtaDelta = new Date(now - $scope.queue.stats.oldest_eta);
			}
		}
		else {
			$scope.oldestEtaDelta = null;
			$scope.oldestEtaSuffix = null;
		}
	}

	function getTasks() {
		clearTimeout($scope.queue.timeoutID);
		$scope.queue.loading = true;
		var numberToLoad = $scope.queue.tasks ? $scope.queue.tasks.length : maxFetch;
		$http.get(appSettings.apiRootUrl + $scope.queueName + "?limit=" + numberToLoad)
			.success(function(data) {
				$scope.queue = data;
				if ($scope.queue.stats.oldest_eta) {
					$scope.queue.stats.oldest_eta = new Date($scope.queue.stats.oldest_eta)
				}
				$scope.queue.tasks.forEach(processTaskModel);

				$scope.loadMore = data.tasks.length == maxFetch;

				setOldestEtaDelta();
			})
			.then(function() {
				$scope.queue.loading = false;
				if ($scope.autorefresh && $scope.refreshInterval) {
					$scope.queue.timeoutID = setTimeout(getTasks, $scope.refreshInterval*1000);
				}
			})
	}

	function loadMoreTasks() {
		$scope.queue.loading = true;
		$http.get(appSettings.apiRootUrl + $scope.queueName + "?limit=" + maxFetch + "&cursor=" + $scope.queue.cursor)
			.success(function(data) {
				if (data.tasks.length) {
					$scope.queue.cursor = data.cursor;

					data.tasks.forEach(function (task) {
						processTaskModel(task);
						$scope.queue.tasks.push(task);
					});
				}
				else {
					$scope.loadMoreTasks = false;
				}
			})
			.then(function() {
				$scope.queue.loading = false;
			})
	}

	function processTaskModel(task) {
		task.deferred_at = new Date(task.deferred_at);

		task.displayText = task.deferred_function;
		if (task.task_reference) {
			task.displayText += (' (' + task.task_reference + ')');
		}
	}
});

deferredApp.controller('TaskCtrl', function($scope, $routeParams, $http, $q, appSettings) {
	var ctlr = this;

	this.queueId = $routeParams.queueId;
	this.taskId = $routeParams.taskId;

	$scope.logs = [];
	$scope.logLevels = LOG_LEVELS;

	$http.get(appSettings.apiRootUrl + this.queueId + '/' + this.taskId)
		.then(function(resp) {
			$scope.task = resp.data.task;
			$scope.logs = resp.data.logs;
		});
});

deferredApp.controller('LogCtrl', function($scope, $routeParams, $http, $q, appSettings) {
	var ctlr = this;

	$scope.isOpen = $scope.log == $scope.logs[0];

	$scope.log.currentLevel = 1;

	processLogModel($scope.log);
	$scope.log.app_logs.forEach(processAppLogModel);

	$scope.$watch("log.currentLevel", function(level, oldLevel) {
		if (level !== oldLevel) {
			$http.get(appSettings.apiRootUrl + 'logs/' + $scope.log.request_id + '?level=' + level)
			.then(function(resp) {
				$scope.log.app_logs = [];
				$scope.log.app_logs = resp.data.log.app_logs;
				$scope.log.app_logs.forEach(function(appLog) {
					appLog.levelText = LOG_LEVELS[appLog.level];
				});
				$scope.isOpen = true;
				$isLevelDropOpen = false;
			});
		}
	});

	function processLogModel(log) {
		log.start_time = new Date(log.start_time);
	}

	function processAppLogModel(appLog) {
		appLog.levelText = LOG_LEVELS[appLog.level];
		appLog.time = new Date(appLog.time);
	}
});

function extend(dst) {
	angular.forEach(arguments, function(obj) {
		if (obj !== dst) {
			angular.forEach(obj, function(value, key) {
				if (dst[key] && dst[key].constructor && dst[key].constructor === Object) {
					extend(dst[key], value);
				} else {
					dst[key] = value;
				}
			});
		}
	});
	return dst;
};

function getRoot() {
	var urlParts = window.location.pathname.split('/');
		splt = urlParts.indexOf('static');

	return urlParts.slice(0,splt).join('/') + '/api/';
}

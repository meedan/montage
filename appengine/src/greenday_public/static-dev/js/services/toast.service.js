/**
 * Notification service
 *
 */
(function () {
	angular
		.module('app.services')
		.factory('ToastService', ToastService);

	/** @ngInject */
	function ToastService ($mdToast, $timeout) {
		var service = {
				show: show,
				hide: hide,
				cancel: cancel,
				update: update,
				closeAfter: closeAfter,
				showError: showError
			},
			toastApi = {},
			toastClosePromise;

		return service;

		function show(content, showClose, options) {
			toastApi = {
				content: content,
				showClose: !!showClose
			};
			var toastOptions = angular.extend({
					templateUrl: 'components/notifications/simple-toast.html',
					controller: toastController,
					controllerAs: 'ctrl',
					locals: {
						toastApi: toastApi
					}
				}, options || {}),
				toastPromise = $mdToast.show(toastOptions);

			return toastPromise;
		}

		function showError(content, hideDelay) {
			if (!content) {
				content = 'OOPS! Something went wrong.';
			}

			if (angular.isUndefined(hideDelay)) {
				hideDelay = 500;
			}

			show(content, true, { hideDelay: hideDelay});
		}

		/* istanbul ignore next */
		/** @ngInject */
		function toastController($scope, toastApi) {
			$scope.ok = hide;
			$scope.close = cancel;
			$scope.toastApi = toastApi;
		}

		function update(options) {
			$timeout.cancel(toastClosePromise);
			angular.extend(toastApi, options);
		}

		function closeAfter(duration) {
			toastClosePromise = $timeout(hide, duration);
		}

		function hide() {
			$mdToast.hide();
		}

		function cancel(reason) {
			$mdToast.cancel(reason);
		}

	}
}());

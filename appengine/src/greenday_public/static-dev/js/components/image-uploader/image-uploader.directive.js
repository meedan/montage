(function () {
	angular.module('components')
		.directive('imageUploader', imageUploader);

	/** @ngInject */
	function imageUploader(ImageUploader, DEBUG, ToastService) {
		var directive = {
			controller: controller,
			controllerAs: 'ctrl',
			templateUrl: 'components/image-uploader/image-uploader.html',
			restrict: 'E',
			replace: true,
			require: 'ngModel',
			scope: {
				ngModel: '=',
				isBusy: '=',
				type: '@'
			}
		};

		return directive;

		/** @ngInject */
		function controller($scope, $element, $attrs) {
			var ctrl = this,
				$input = $element.find('.image-uploader__input').eq(0),
				dropZone = $element.find('.image-uploader__drop-zone').get(0);

			ctrl.$scope = $scope;
			ctrl.loading = false;
			ctrl.uploadProgress = 0;

			ctrl.showFileDialog = function () {
				$input.trigger('click');
			};

			ctrl.onFileChange = onFileChange;

			$input.on('change', function (event) {
				ctrl.onFileChange(event.target.files[0]);
			});

			dropZone.addEventListener('dragenter', function (event) {
				preventDefault(event);
				$element.addClass('image-uploader--big');
			}, false);

			dropZone.addEventListener('dragover', function (event) {
				preventDefault(event);
			}, false);

			dropZone.addEventListener('dragleave', function (event) {
				preventDefault(event);
				$element.removeClass('image-uploader--big');
			}, false);

			dropZone.addEventListener('drop', function (event) {
				preventDefault(event);
				var dt = event.dataTransfer,
					files = dt.files;

				$element.removeClass('image-uploader--big');
				ctrl.onFileChange(files[0]);
			}, false);
		}

		function preventDefault(event) {
			event.stopPropagation();
			event.preventDefault();
		}

		function onFileChange(fileData) {
			var ctrl = this,
				imageType = /image.*/;

			if (!fileData.type.match(imageType)) {
				return;
			}

			ctrl.loading = true;
			ctrl.$scope.isBusy = true;
			ctrl.$scope.$apply();

			ImageUploader
				.upload(fileData, onProgress.bind(ctrl), ctrl.$scope.type)
				.then(function (response) {
					ToastService.show('Image uploaded', true);
					ctrl.$scope.ngModel = response.url;
					ctrl.uploadProgress = 0;
				}, function (err) {
					ToastService.showError('Error: ' + err, 0);
				})
				.finally(function () {
					ctrl.loading = false;
					ctrl.$scope.isBusy = false;
				});
		}

		function onProgress(progress) {
			var ctrl = this;
			ctrl.uploadProgress = progress;
			ctrl.$scope.$apply();
		}
	}
}());

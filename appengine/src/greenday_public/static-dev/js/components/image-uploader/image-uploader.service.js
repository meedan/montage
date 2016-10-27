/**
 * ImageUploader service
 *
 */
(function () {
	angular
		.module('components')
		.factory('ImageUploader', ImageUploader);

	var maxFileSize = 32*1024*1024;

	/** @ngInject */
	function ImageUploader ($q, $http, GapiLoader, UserService) {
		var service = {
			upload: upload
		};

		return service;

		function upload(fileData, onProgress, type) {
			var uploadDeferred = $q.defer(),
				uploadPromise = uploadDeferred.promise,
				url = '/image-upload/?name=' + fileData.name + '&type=' + type,
				xhr;

			if (fileData.size > maxFileSize) {
				uploadDeferred.reject('Files must not be larger than 32MB');
				return uploadPromise;
			}


			UserService.authorizationToken().then(
				function(token){
					xhr = new XMLHttpRequest();
					xhr.open('POST', url, true);

					xhr.setRequestHeader('Content-Type', fileData.type);
					// xhr.setRequestHeader('Content-Length', fileData.size);
					xhr.setRequestHeader('Authorization', token);

					if (xhr.upload && onProgress) {
						xhr.upload.addEventListener('progress', function (evt) {
							onProgress(parseInt((evt.loaded / evt.total) * 100, 10));
						});
					}

					xhr.onreadystatechange = function (e) {
						if (xhr.readyState === 4) {
							var response = JSON.parse(e.target.response);
							if (xhr.status === 200) {
								uploadDeferred.resolve(response);
							} else {
								uploadDeferred.reject(response.message);
							}
						}
					};

					xhr.send(fileData);
				},
				function(error) {
					window.alert('wrnog!' + error);
				}

			);

			return uploadPromise;
		}
	}
}());

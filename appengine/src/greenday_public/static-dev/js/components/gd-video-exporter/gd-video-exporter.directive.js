(function () {
	angular.module('components')
		.directive('gdVideoExporter', gdVideoExporter);

	/** @ngInject */
	function gdVideoExporter(YouTubeDataService, ToastService, _, $http) {
		var directive = {
			restrict: 'E',
			templateUrl: 'components/gd-video-exporter/gd-video-exporter.html',
			controller: controller,
			link: link,
			controllerAs: 'ctrl',
			require: ['^gdVideoExporter'],
			scope: {
				isVisible: '=',
				resetWhen: '=',
				videos: '=',
				selectedProject: '='
			}
		};

		return directive;

		function link(scope, element, attrs, controllers) {
			var ctrl = controllers[0];

			scope.$watch('resetWhen', function (isReset) {
				if (isReset === true) {
					ctrl.reset();
				}
			});
		}

		function controller($scope, $route, $location) {
			var ctrl = this;

			ctrl.exportToYouTube = exportToYouTube;
			ctrl.downloadLink = null;
			ctrl.ytPlaylistUrl = null;
			ctrl.ytVideoResults = null;
			ctrl.ytExportProg = null;
			ctrl.reset = reset;
			ctrl.exportType = null;
			ctrl.exportName = null;
			ctrl.exportVideoIds = null;
			ctrl.exportTypes = [{
				'key': 'csv',
				'label': 'CSV'
			}, {
				'key': 'kml',
				'label': 'KML'
			}, {
				'key': 'yt',
				'label': 'YouTube Playlist'
			}];
			ctrl.requestExport = function() {
				var request  = {
					format: this.exportType.key,
					name: this.exportName,
					clean_name: this.exportName,
					vids: this.exportVideoIds
				};
				var saveData = (function () {
			    var a = document.createElement("a");
			    document.body.appendChild(a);
			    a.style = "display: none";
			    return function (data, fileName) {
						var blob = new Blob([data.replace(/\uFFFD/g, '')], {type: "text/csv"});
						url = window.URL.createObjectURL(blob);
						a.href = url;
						a.download = fileName;
						a.click();
						setTimeout(function(){
							window.URL.revokeObjectURL(url);
						}, 100);
			    };
				}());

				$http({
				    method: 'POST',
				    url: this.downloadLink,
				    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
				    transformRequest: function() {
				        var str = [];
				        for(var p in request) {
				        	str.push(encodeURIComponent(p) + '=' + encodeURIComponent(request[p]));
								}
				        return str.join('&');
				    }
					}).then(
					function(response){
				  	saveData(response.data, ctrl.exportName + '.' + ctrl.exportType.key);
					},
					function(){

					}
				);
			};

			$scope.$watch('ctrl.exportType', getDownloadLink);
			$scope.$watch('ctrl.exportName', getDownloadLink);
			$scope.$watch('videos', getExportIds);
			$scope.$watch('videos', getDownloadLink);

			function getExportIds() {
				ctrl.exportVideoIds = _.pluck($scope.videos, 'id').join(',');
			}



			function getDownloadLink() {
				var urlBase = '',
					url = [],
					qs = [];

				if (ctrl.exportType && ctrl.exportName && $scope.videos) {
					urlBase = $location.protocol() + '://' + $location.host();

					if ($location.port()) {
						urlBase += ':' + $location.port();
					}

					if (ctrl.exportType.key === 'kml') {
						qs.push('clean_name=' + ctrl.exportName);
					}

					url = [
						urlBase,
						'export',
						'project',
						$route.current.params.projectId,
						'videos'
					];
				}
				ctrl.downloadLink = url.join('/') + '/';
			}

			function exportToYouTube(videos) {
				ctrl.ytExportProg = 0.1;
				ctrl.ytVideoResults = [];

				if (videos.length > 200){
					ToastService.show('You cannot export more than 200 videos to a YouTube Playlist', false, { hideDelay: 3000 });
					ctrl.reset();
				} else {
					ToastService.show('Exporting to YouTube Playlist', false, { hideDelay: 0 });
					YouTubeDataService
						.request('playlists', 'insert', {
							part: 'snippet,status',
							resource: {
								snippet: {
									title: ctrl.exportName,
									description: 'A private playlist created from Montage'
								},
								status: {
									privacyStatus: 'private'
								}
							}
						})
						.then(function (response) {
							var playlist = response.result;
							if (playlist){
								ToastService.update({
									content: 'Adding videos to YouTube playlist...',
								});

								addVideosToPlaylist(playlist.id, videos, 0);
								ctrl.ytPlaylistUrl = 'https://www.youtube.com/playlist?list=' + playlist.id;
							} else {
								ToastService.update({
									content: 'Oops - there was a problem creating your playlist'
								});
							}
						}, function(e) {
							ctrl.ytExportProg = null;
							ToastService.update({ content: e.message});
						});
				}
			}

			function reset() {
				ctrl.exportType = null;
				ctrl.exportName = null;
				ctrl.ytPlaylistUrl = null;
				ctrl.downloadLink = null;
				ctrl.ytExportProg = 0;
				ctrl.ytVideoResults = null;
			}

			function finaliseYouTubeExport(playlistId) {
				ToastService.update({
					content: 'YouTube playlist created!',
					showClose: true
				});
				ctrl.ytExportProg = null;
			}

			function addVideosToPlaylist(playlistId, videos, currentIndex) {
				var currentVideo = videos[currentIndex];

				ToastService.update({
					content: 'Adding video - ' + currentVideo.name
				});

				var promise = YouTubeDataService.request('playlistItems', 'insert', {
					part: 'snippet',
					resource: {
						snippet: {
							playlistId: playlistId,
							resourceId: {
								videoId: currentVideo.youtube_id,
								kind: 'youtube#video'
							}
						}
					}
				}).then(function () {
					ctrl.ytVideoResults.push({
						video: currentVideo,
						status: 1
					});
				}, function (e) {
					ToastService.update({
						content: 'Error adding video ' + currentVideo.name + ': ' + e.message
					});

					ctrl.ytVideoResults.push({
						video: currentVideo,
						status: 2,
						msg: e.message
					});
				}).finally(function () {
					ctrl.ytExportProg = Math.max((currentIndex / videos.length) * 100, ctrl.ytExportProg);

					if (currentIndex + 1 < videos.length){
						addVideosToPlaylist(playlistId, videos, ++currentIndex);
					} else {
						finaliseYouTubeExport(playlistId);
					}
				});

				return promise;
			}
		}
	}
}());

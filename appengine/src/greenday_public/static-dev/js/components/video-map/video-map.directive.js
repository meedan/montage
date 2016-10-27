(function () {
	angular.module('components')
		.directive('videoMap', videoMap);

	/** @ngInject */
	function videoMap($window, $timeout, _) {
		var directive = {
			templateUrl: 'components/video-map/video-map.html',
			restrict: 'E',
			scope: {
				refreshWhen: '=',
				videos: '='
			},
			require: ['^videoMap'],
			link: link,
			controller: controller,
			controllerAs: 'ctrl'
		};

		return directive;

		function link(scope, element, attrs, controllers) {
			var ctrl = controllers[0];

			ctrl.refreshUnwatcher = scope.$watch('refreshWhen', ctrl.onRefreshWhen);
			scope.$watchCollection('videos', ctrl.onVideosUpdate);
			scope.$watch('ctrl.infoBox.options.isVisible', ctrl.onInfoboxVisibleChange);
		}

		function controller($scope, $element, $attrs) {
			var ctrl = this;

			ctrl.showInfoBox = false;
			ctrl.scrollListener = null;

			ctrl.map = {
				controller: {},
				options: {
					zoom: 7,
				}
			};

			ctrl.mapOptions = {
				zoomControlOptions: {
					position: google.maps.ControlPosition.TOP_RIGHT
				},
				streetViewControlOptions: {
					position: google.maps.ControlPosition.TOP_RIGHT
				}
			};

			ctrl.markers = [];
			ctrl.initialised = false;

			ctrl.markerClusterer = {
				controller: {},
				events: {
					mouseover: onClusterMouseover
				},
				options: {
					averageCenter: true,
					clusterClass: 'video-map__cluster',
					imageSizes: [48],
					minimumClusterSize: 1,
					styles: [{
						anchorIcon: [15, 16],
						url: '',
					}],
					calculator: calculator
				}
			};

			ctrl.infoBox = {
				controller: {},
				options: {
					boxClass: 'video-map__infobox',
					closeBoxURL: '',
					coords: {},
					enableEventPropagation: true,
					isVisible: false,
					pixelOffset: {
						height: -9,
						width: -4
					},
					templateUrl: 'components/video-map/video-map-infobox.html',
					templateParams: {
						totalVideos: 0,
						videos: [],
						close: hideInfoBox
					}
				}
			};

			ctrl.onVideosUpdate = function (videos, oldVideos) {
				if (videos && videos.length) {
					var markers = [],
						bounds,
						boundCenter;

					ctrl.infoBox.options.isVisible = false;

					angular.forEach(videos, function (video) {
						if (video.longitude && video.latitude) {
							markers.push({
								id: video.id,
								longitude: video.longitude,
								latitude: video.latitude,
								options: {
									video: {
										id: video.id,
										project_id: video.project_id,
										youtube_id: video.youtube_id,
										name: video.name,
										duration: video.duration,
										channel_name: video.channel_name,
										location_overridden: video.location_overridden,
										precise_location: video.precise_location
									}
								}
							});
						}
					});

					bounds = getBounds(markers);
					boundCenter = bounds.getCenter();

					ctrl.map.options.center = {
						latitude: boundCenter.lat(),
						longitude: boundCenter.lng()
					};

					ctrl.map.options.bounds = {
						northeast: {
							latitude: bounds.getNorthEast().lat(),
							longitude: bounds.getNorthEast().lng()
						},
						southwest: {
							latitude: bounds.getSouthWest().lat(),
							longitude: bounds.getSouthWest().lng()
						}
					};

					ctrl.markers = markers;

					$timeout(function () {
						try {
							var map = ctrl.map.controller.getGMap();

							$window.google.maps.event.addListener(map, 'zoom_changed', hideInfoBox);
							$window.google.maps.event.addListener(map, 'click', hideInfoBox);
						} catch (e) {}
					});
				}

				if (!angular.equals(videos, oldVideos)) {
					ctrl.initialised = true;
				}
			};

			ctrl.onInfoboxVisibleChange = function (isVisible, wasVisible) {
				if (isVisible !== wasVisible) {
					if (isVisible === true) {
						addInfoBoxMouseScrollEvent();
					} else if (isVisible === false) {
						removeInfoBoxMouseScrollEvent();
					}
				}
			};

			ctrl.onRefreshWhen = function (needsRefresh) {
				if (ctrl.markers.length > 0 && needsRefresh === true) {
					$timeout(function () {
						ctrl.map.controller.refresh();
						// no need to watch it again
						ctrl.refreshUnwatcher();
					});
				}
			};

			function getBounds(markers) {
				var bounds = new $window.google.maps.LatLngBounds(),
					latLng;

				angular.forEach(markers, function(marker) {
					latLng = new $window.google.maps.LatLng(marker.latitude, marker.longitude);
					bounds.extend(latLng);
				});

				return bounds;
			}

			function hideInfoBox() {
				$timeout(function () {
					$scope.$apply(function () {
						ctrl.infoBox.options.isVisible = false;
					});
				});
			}

			function onClusterMouseover(cluster) {
				$scope.$apply(function () {
					var markers = cluster.getMarkers().values(),
						center = cluster.getCenter(),
						videos = _.pluck(markers, 'video');

					ctrl.infoBox.options.coords.latitude = center.lat();
					ctrl.infoBox.options.coords.longitude = center.lng();
					ctrl.infoBox.options.templateParams.videos = videos;
					ctrl.infoBox.options.templateParams.nameFilter = '';
					ctrl.infoBox.options.templateParams.totalVideos = videos.length;
					ctrl.infoBox.options.isVisible = true;
				});
			}

			function addInfoBoxMouseScrollEvent() {
				// mega hack to allow mousewheel scrolling in an InfoBox
				// see: https://code.google.com/p/google-maps-utility-library-v3/issues/detail?id=281
				var infoBox = ctrl.infoBox.controller.getGWindows()[0],
					event = $window.google.maps.event;

				ctrl.domreadyListener = event.addListener(infoBox, 'domready', function () {
					$timeout(function () {
						$('.video-map__quick-filter__input').focus();
					}, 100);
					// assign it to a variable so we can remove it when the infobox is hidden
					ctrl.scrollListener = event.addDomListener(infoBox.div_, 'mousewheel', function (e) {
						e.cancelBubble = true;
						if (e.stopPropagation) {
							e.stopPropagation();
						}
					});

					ctrl.clickListener = event.addDomListener(infoBox.div_, 'click', function (e) {
						e.cancelBubble = true;
						if (e.stopPropagation) {
							e.stopPropagation();
						}
					});
				});
			}

			function removeInfoBoxMouseScrollEvent() {
				$window.google.maps.event.removeListener(ctrl.scrollListener);
				$window.google.maps.event.removeListener(ctrl.clickListener);
				$window.google.maps.event.removeListener(ctrl.domreadyListener);
			}
		}


		function calculator(markers) {
			var count = markers.length,
				text = '';

			if (count === 1 && markers.values()[0].video.location_overridden && markers.values()[0].video.precise_location) {
				text = '<icon class="ic-location-on"></icon>';
			} else if (count > 1) {
				text = count;
			}

			return {
				text: text,
				index: 0,
				title: ''
			};
		}
	}
}());

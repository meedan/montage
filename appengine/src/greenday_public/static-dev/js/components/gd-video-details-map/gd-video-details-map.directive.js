/* global google */
(function() {
	angular.module('components')
		.directive('gdVideoDetailsMap', videoDetailsMap);

	var ENABLED_MAP_TYPES = [
		{
			mode: 'hybrid',
			title: 'Hybrid'
		},
		{
			mode: 'roadmap',
			title: 'Roadmap'
		},
		{
			mode: 'satellite',
			title: 'Satellite'
		}
	];

	/** @ngInject */
	function videoDetailsMap($q, $timeout, $analytics, ToastService) {
		var UNDO_TIMEOUT = 10000;

		var directive = {
			templateUrl: 'components/gd-video-details-map/gd-video-details-map.html',
			restrict: 'E',
			scope: {
				expanded: '=',
				video: '=',
				ytVideoData: '='
			},
			controller: controller,
			controllerAs: 'ctrl',
			link: link
		};

		return directive;

		/** @ngInject */
		function controller($scope, $element) {
			var ctrl = this,
				currentMapTypeIndex = 1;

			/////////////////
			// Scope API
			/////////////////


			/////////////////
			// Controller API
			/////////////////
			ctrl.editMode = false;
			ctrl.showImpreciseLocationButton = false;
			ctrl.undoTimeout = null;
			ctrl.currentMapType = ENABLED_MAP_TYPES[currentMapTypeIndex];

			/**
			 * The previous location before any edits were made in this session.
			 * This object will only be populated with coordinates for a short
			 * time after a new location is set, as the undo functionality is
			 * only available for a short time after a new location has been
			 * saved.
			 *
			 * @type {Object}
			 */
			ctrl.beforeEditLocation = {
				latitude: null,
				longitude: null,
				overridden: null
			};

			ctrl.map = {
				center: {
					latitude: null,
					longitude: null
				},
				zoom: null
			};

			// Set initial location and zoom based on video data.
			if (angular.isDefined($scope.video.latitude)) {
				ctrl.map.center.latitude = $scope.video.latitude;
				ctrl.map.center.longitude = $scope.video.longitude;
				ctrl.map.zoom = 7;
			} else {
				ctrl.map.center.latitude = 0;
				ctrl.map.center.longitude = 0;
				ctrl.map.zoom = 2;
			}

			ctrl.mapOptions = {
				disableDefaultUI: true,
				scrollwheel: true
			};

			ctrl.marker = {
				id: $scope.video.id,
				coords: {
					latitude: $scope.video.latitude,
					longitude: $scope.video.longitude
				}
			};

			ctrl.markers = [ctrl.marker];

			ctrl.markerClusterer = {
				options: {
					calculator: calculator,
					clusterClass: 'video-details-map__cluster',
					imageSizes: [48],
					minimumClusterSize: 1,
					styles: [{
						anchorIcon: [8, 9],
						url: ''
					}],
				}
			};

			ctrl.searchbox = {
				events: {
					'places_changed': onPlacesChanged
				},
				template: 'components/gd-video-details-map/gd-video-details-searchbox.html',
				options: {}
			};

			ctrl.toggleMap = function() {
				if ($scope.expanded) {
					ctrl.collapseMap();
				} else {
					ctrl.expandMap();
				}
			};

			ctrl.expandMap = function($event) {
				if (!!$scope.video.archived_at && !$scope.hasLocation()) {
					return;
				}
				$scope.expanded = true;
				ctrl.editMode = true;
				$element.addClass('is-expanded');
				$event.stopPropagation();
			};

			ctrl.collapseMap = function($event) {
				var map = ctrl.map.getGMap();

				if ($scope.video.latitude) {
					map.panTo(new google.maps.LatLng(
						$scope.video.latitude,
						$scope.video.longitude
					));
				}

				ctrl.editMode = false;
				$scope.expanded = false;
				$element.removeClass('is-expanded');
				$event.stopPropagation();
			};

			ctrl.setLocation = function () {
				var map = ctrl.map.getGMap(),
					center = map.getCenter(),
					analyticsLabel,
					currentLatLng = [$scope.video.latitude, $scope.video.longitude].join(',');

				// Store the current position so we can "undo" it later.
				setGdLocation(center.lat(), center.lng(), true);

				// Schedule the undo timer.
				ctrl.undoTimeout = $timeout($scope.clearUndo, UNDO_TIMEOUT);

				// Force the map to update. This is horrible but I couldn't
				// see a better solution :(.
				$timeout(function() {
					$scope.$apply();
				});

				saveVideo()
					.then(function () {
						analyticsLabel = [
							'of', $scope.video.youtube_id,
							'from:', currentLatLng,
							'to:', $scope.video.latitude + ', ' + $scope.video.longitude
						];
						$analytics.eventTrack('change location', {
							category: 'video theatre',
							label: analyticsLabel.join(' ')
						});
					});
			};

			ctrl.setImpreciseLocation = function () {
				var map = ctrl.map.getGMap(),
					center = map.getCenter(),
					analyticsLabel,
					currentLatLng = [$scope.video.latitude, $scope.video.longitude].join(',');

				// Store the current position so we can "undo" it later.
				setGdLocation(center.lat(), center.lng(), false);

				// Schedule the undo timer.
				ctrl.undoTimeout = $timeout($scope.clearUndo, UNDO_TIMEOUT);

				// Force the map to update. This is horrible but I couldn't
				// see a better solution :(.
				$timeout(function() {
					$scope.$apply();
				});

				saveVideo()
					.then(function () {
						analyticsLabel = [
							'of', $scope.video.youtube_id,
							'from:', currentLatLng,
							'to:', $scope.video.latitude + ', ' + $scope.video.longitude
						];
						$analytics.eventTrack('change location', {
							category: 'video theatre',
							label: analyticsLabel.join(' ')
						});
					});
			};

			ctrl.undoLocation = function() {
				var map = ctrl.map.getGMap();

				restorePreviousLocation();

				// Move the map back to the previous location
				if ($scope.video.latitude) {
					map.panTo(new google.maps.LatLng(
						$scope.video.latitude,
						$scope.video.longitude
					));
				}

				// Save the undo to the server.
				// FIXME: Switch to a patch request? Need to figure out if PATCH is
				// possible in js-data (in combination with changesOnly: true
				// option perhaps?) and if the BE supports PATCH here.
				$scope.video.DSSave().then(function () {
					ToastService.hide();
					ToastService.show('Location reverted', false);
				}, function (response) {
					ToastService.showError('Error: ' + response.data.error.message, 0);
				});
			};

			ctrl.revertLocation = function() {
				var map = ctrl.map.getGMap(),
					recordingDetails = $scope.ytVideoData.recordingDetails,
					analyticsLabel,
					currentLatLng = [$scope.video.latitude, $scope.video.longitude].join(',');

				// Remove any Montage location data.
				clearGdLocation();

				// Restore YouTubes location data.
				$scope.video.latitude = recordingDetails.location.latitude;
				$scope.video.longitude = recordingDetails.location.longitude;

				// Move the map back to the original location
				map.panTo(new google.maps.LatLng(
					$scope.video.latitude,
					$scope.video.longitude
				));

				saveVideo()
					.then(function () {
						analyticsLabel = [
							'of', $scope.video.youtube_id,
							'from:', currentLatLng,
							'to:', $scope.video.latitude + ', ' + $scope.video.longitude
						];
						$analytics.eventTrack('revert location', {
							category: 'video theatre',
							label: analyticsLabel.join(' ')
						});
					});
			};

			ctrl.removeLocation = function() {
				// We have to set the lat/lng to undefined and not null because
				// the marker is still rendered at 0,0 if null is used :/
				setGdLocation(undefined, undefined);
				saveVideo()
					.then(function () {
						var analyticsLabel = ['of', $scope.video.youtube_id];
						$analytics.eventTrack('remove location', {
							category: 'video theatre',
							label: analyticsLabel.join(' ')
						});
					});
			};

			ctrl.onMapTypeClicked = function () {
				var nextMapTypeIndex = (currentMapTypeIndex + 1) % ENABLED_MAP_TYPES.length;

				ctrl.setMapType(nextMapTypeIndex);
			};

			ctrl.setMapType = function (index) {
				var map = ctrl.map.getGMap();

				currentMapTypeIndex = index;
				ctrl.currentMapType = ENABLED_MAP_TYPES[index];
				map.setMapTypeId(ENABLED_MAP_TYPES[index].mode);
			};

			ctrl.onZoomInClicked = function() {
				var map = ctrl.map.getGMap(),
					currentZoom = map.getZoom(),
					nextZoom = currentZoom + 1;

				// Figure out if we can zoom in any further
				getMaxZoom(map.getCenter()).then(function (response) {
					var maxZoom;

					if (response.status === google.maps.MaxZoomStatus.OK) {
						maxZoom = response.zoom;
						if (nextZoom <= maxZoom) {
							map.setZoom(nextZoom);
						}
					}
				});
			};

			ctrl.onZoomOutClicked = function(evnt) {
				var MIN_ZOOM = 0,
					map = ctrl.map.getGMap(),
					currentZoom = map.getZoom(),
					nextZoom = currentZoom - 1;

				if (nextZoom >= MIN_ZOOM) {
					map.setZoom(nextZoom);
				}
			};

			/////////////////
			// Private functions
			/////////////////
			function onPlacesChanged(searchBox) {
				var places = searchBox.getPlaces(),
					place,
					map;

				// Center the map on the selected place.
				if (places.length) {
					place = places[0];
					map = ctrl.map.getGMap();
					map.setCenter(place.geometry.location);
				}
			}

			function calculator(markers, numStyles) {
				return {
					text: $scope.video.location_overridden && $scope.video.precise_location ? '<icon class="ic-location-on"></icon>' : '',
					index: 0,
					title: ''
				};
			}

			function clearGdLocation() {
				// Remember the current location before we change it, so we
				// can undo.
				rememberCurrentLocation();

				$scope.video.latitude = undefined;
				$scope.video.longitude = undefined;
				$scope.video.location_overridden = false;
				$scope.video.precise_location = true;
			}

			function rememberCurrentLocation() {
				ctrl.beforeEditLocation.latitude = $scope.video.latitude;
				ctrl.beforeEditLocation.longitude = $scope.video.longitude;
				ctrl.beforeEditLocation.location_overridden = $scope.video.location_overridden;
				ctrl.beforeEditLocation.precise_location = $scope.video.precise_location;
			}

			function restorePreviousLocation() {
				$scope.video.latitude = ctrl.beforeEditLocation.latitude;
				$scope.video.longitude = ctrl.beforeEditLocation.longitude;
				$scope.video.location_overridden = ctrl.beforeEditLocation.location_overridden;
				$scope.video.precise_location = ctrl.beforeEditLocation.precise_location;

				ctrl.beforeEditLocation.latitude = undefined;
				ctrl.beforeEditLocation.longitude = undefined;
				ctrl.beforeEditLocation.location_overridden = undefined;
				ctrl.beforeEditLocation.precise_location = undefined;
			}

			function setGdLocation(lat, lng, precise_location) {
				// Remember the current location before we change it, so we
				// can undo.
				if (typeof(precise_location) === 'undefined' || precise_location !== false) {
					precise_location = true;
				}
				rememberCurrentLocation();

				$scope.video.latitude = lat;
				$scope.video.longitude = lng;
				$scope.video.location_overridden = true;
				$scope.video.precise_location = precise_location;
			}

			function saveVideo() {
				// FIXME: Switch to a patch request? Need to figure out if PATCH is
				// possible in js-data (in combination with changesOnly: true
				// option perhaps?) and if the BE supports PATCH here.
				var save = $scope.video.DSSave();

				ToastService.show('Saving Video Location', false, {
					hideDelay: 0
				});

				save.then(function () {
					ToastService.hide();
					ToastService.show('Location updated', false, {
						hideDelay: 10000,
						templateUrl: 'components/notifications/undo-toast.html',
						controllerAs: 'toastCtrl',
						controller: function ($scope, toastApi) {
							$scope.toastApi = toastApi;
							this.undo = function() {
								ctrl.undoLocation();
							};
						}
					});
				}, function (response) {
					ToastService.showError('Error: ' + response.data.error.message, 0);
				});

				return save;
			}

			function getMaxZoom(latLng) {
				var dfd = $q.defer();
				var maxZoomService = new google.maps.MaxZoomService();

				maxZoomService.getMaxZoomAtLatLng(latLng, function(response) {
					dfd.resolve(response);
				});

				return dfd.promise;
			}
		}

		function link(scope, element, attrs, ctrl) {
			/////////////////
			// Scope API
			/////////////////
			scope.hasLocation = hasLocation;

			scope.clearUndo = function() {
				$timeout.cancel(ctrl.undoTimeout);

				ctrl.beforeEditLocation.latitude = null;
				ctrl.beforeEditLocation.longitude = null;
				ctrl.beforeEditLocation.location_overridden = null;
			};

			/////////////////
			// Scope events
			/////////////////
			scope.$on('$destroy', function () {
				scope.clearUndo();
			});

			/////////////////
			// Scope watchers
			/////////////////
			scope.$watch('video.latitude', function (nv, ov) {
				if (ctrl.marker.coords.latitude !== nv) {
					ctrl.marker.coords.latitude = nv;
				}
			});

			scope.$watch('video.longitude', function (nv, ov) {
				if (ctrl.marker.coords.longitude !== nv) {
					ctrl.marker.coords.longitude = nv;
				}
			});

			scope.$watch('ctrl.marker.coords.latitude', function (nv, ov) {
				if (scope.video.latitude !== nv) {
					scope.video.latitude = nv;
				}
			});

			scope.$watch('ctrl.marker.coords.longitude', function (nv, ov) {
				if (scope.video.longitude !== nv) {
					scope.video.longitude = nv;
				}
			});

			/////////////////
			// Private functions
			/////////////////
			function hasLocation() {
				var gdLocation = false,
					ytLocation = false;

				// Check if there is location data from Montage
				if (angular.isDefined(scope.video) &&
					scope.video.location_overridden) {

					if (scope.video.latitude) {
						// The user has set a location in Montage.
						gdLocation = true;
					} else {
						// Special case... If the user has overridden the
						// YouTube location, but "removed" the location (so they
						// are basically telling us that they don't believe the
						// YouTube location but don't know the actual location),
						// we need to ensure the "Set Location" appears
						return false;
					}
				}

				// Check if there is location data from YouTube
				if (angular.isDefined(scope.ytVideoData.recordingDetails) &&
					angular.isDefined(scope.ytVideoData.recordingDetails.location) &&
					angular.isDefined(scope.ytVideoData.recordingDetails.location.latitude)) {
					ytLocation = true;
				}

				return gdLocation || ytLocation;
			}
		}
	}
}());

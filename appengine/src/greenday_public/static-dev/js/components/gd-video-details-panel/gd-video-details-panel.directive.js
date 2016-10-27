(function () {
	angular.module('components')
		.directive('gdVideoDetailsPanel', videoDetailsPanel);

	/** @ngInject */
	function videoDetailsPanel($mdDialog, $analytics, _, moment, ProjectModel, CollectionModel, ToastService) {

		var directive = {
			templateUrl: 'components/gd-video-details-panel/gd-video-details-panel.html',
			restrict: 'E',
			scope: {
				project: '=',
				gdVideoData: '=',
				ytVideoData: '='
			},
			controller: controller,
			controllerAs: 'videoDetailsPanelCtrl',
			link: link
		};

		return directive;

		/** @ngInject */
		function controller($scope, $element, $attrs) {
			var ctrl = this;

			ProjectModel.bindAll({}, $scope, 'ctrl.projects');

			/////////////////
			// Controller API
			/////////////////
			ctrl.hasProject = !!$scope.project;
			if (!ctrl.hasProject) {
				ProjectModel.findAll();
			} else {
				ctrl.projects = [$scope.project];
			}
			ctrl.collections = {};
			ctrl.mapExpanded = false;

			ctrl.menuData = {
				hasProject: ctrl.hasProject,
				projects: ctrl.projects,
				collections: ctrl.collections,
				isVideoArchived: function () {
					return ctrl.isVideoArchived.apply(ctrl, arguments);
				},
				isVideoInCollection: function (collection) {
					return ctrl.isVideoInCollection.apply(ctrl, arguments);
				},
				remove: function() {
					ctrl.remove.apply(ctrl, arguments);
				},
				manageDuplicates: function() {
					ctrl.manageDuplicates.apply(ctrl,arguments);
				},
				addToCollection: function(destination) {
					ctrl.addToCollection.apply(ctrl, arguments);
				},
				addToProject: function(destination) {
					ctrl.addToProject.apply(ctrl, arguments);
				},
				getCollections: function() {
					ctrl.getCollections.apply(ctrl, arguments);
				},
				createCollection: function() {
					ctrl.createCollection.apply(ctrl, arguments);
				},
				resetCollectionForm: function() {
					ctrl.menuData.addingNewCollection = false;
					ctrl.menuData.newCollectionName = '';
				},
				showNewCollectionForm: function () {
					ctrl.menuData.addingNewCollection = true;
				}
			};

			ctrl.getCollections = function (projectId, bypassCache) {
				CollectionModel
					.findAll({project_id: projectId}, {bypassCache: !!bypassCache})
					.then(function (collections) {
						ctrl.collections[projectId] = collections;
					});
			};

			ctrl.showRecordedDateDatepicker = function ($event) {
				console.log('showRecordedDateDatepicker');
			};

			ctrl.createCollection = function (projectId, collectionName) {
				if (!projectId || !collectionName) {
					return;
				}
				var collection = CollectionModel.createInstance({
					name: collectionName,
					project_id: projectId
				});
				CollectionModel
					.create(collection)
					.then(function (collection) {
						ToastService.show('Collection created');
						ctrl.getCollections(collection.project_id, true);
						ctrl.menuData.resetCollectionForm();
					});

			};

			ctrl.remove = function ($event) {
				var confirm = $mdDialog.show({
					targetEvent: $event,
					templateUrl: 'pages/video/remove-video-dialog/pages.video.remove-video.html',
					controller: 'RemoveVideoDialogCtrl',
					locals: {
						video: $scope.gdVideoData
					}
				});
			};

			ctrl.manageDuplicates = function ($event) {
				$mdDialog.show({
					targetEvent: $event,
					templateUrl: 'pages/video/duplicate-videos-dialog/pages.video.duplicate-videos.html',
					controller: 'DuplicateVideosDialogCtrl',
					controllerAs: 'ctrl',
					onComplete: afterShowAnimation,
					locals: {
						video: $scope.gdVideoData,
						dupeVideos: $scope.gdVideoData.getDuplicates()
					}
				});

				// When the 'enter' animation finishes...
				function afterShowAnimation(scope, element, options) {
					element.find('.duplicates-dialog__input--autofocus').focus();
				}
			};

			ctrl.addToProject = function (project) {
				project
					.addVideos($scope.gdVideoData.youtube_id);
			};

			ctrl.isVideoInCollection = function (collection) {
				var collectionList = $scope.gdVideoData.in_collections;
				if (!collectionList || !collectionList.length) {
					return false;
				}
				return collectionList.indexOf(collection.id) > -1;
			};

			ctrl.addToCollection = function (project, collection) {
				if (typeof $scope.gdVideoData.in_collections === 'undefined') {
                    $scope.gdVideoData.in_collections = [];
                }
				if (ctrl.isVideoInCollection(collection)) {
					collection
						.removeVideos($scope.gdVideoData.youtube_id)
						.then(function () {
							_.remove($scope.gdVideoData.in_collections, function (id) {
								return id === collection.id;
							});
							ToastService.show('Video removed from ' + collection.name);
						});
				} else {
					// If the video belongs to another project, add it to that project first
					if ($scope.gdVideoData.project_id !== collection.project_id) {
						project
							.addVideos($scope.gdVideoData.youtube_id)
							.then(function (result) {
								collection
									.addVideos(result.videos[0].youtube_id)
									.then(function (results) {
										$scope.gdVideoData.in_collections.push(collection.id);
									});
							});
					} else {
						collection
							.addVideos($scope.gdVideoData.youtube_id)
							.then(function (results) {
								$scope.gdVideoData.in_collections.push(collection.id);
							});
					}
				}
			};

			ctrl.isVideoArchived = function () {
				return !!$scope.gdVideoData.archived_at;
			};

			ctrl.revertDate = function () {
				var currentRecordedDate = $scope.gdVideoData.recorded_date,
					prettyDate = moment.utc(currentRecordedDate).format('DD MMM YYYY'),
					analyticsLabel;

				$scope.gdVideoData.recorded_date_overridden = false;
				$scope.gdVideoData.recorded_date = undefined;
				$scope.displayDate = '';

				ToastService.show('Reverting overridden date…', false, {
					hideDelay: 0
				});

				$scope.gdVideoData.save().then(function () {
					analyticsLabel = ['of', $scope.gdVideoData.youtube_id, 'from:', prettyDate];
					ToastService.hide();
					$analytics.eventTrack('revert recorded date', {
						category: 'video theatre',
						label: analyticsLabel.join(' ')
					});
				}, function () {
					ToastService.showError('Unable to save date changes', 3000);
				});
			};
		}

		function link(scope, element, attrs, ctrl) {
			var $map = element.find('.video-theater__map');
			var date;

			if (scope.gdVideoData.recorded_date_overridden) {
				date = scope.gdVideoData.recorded_date;
			} else {
				date = scope.gdVideoData.published_date;
			}

			scope.displayDate = date;

			scope.data = {
				datepickerDate: moment.utc(scope.displayDate).toDate()
			};

			/////////////////
			// Scope watchers
			/////////////////
			scope.$watch('videoDetailsPanelCtrl.mapExpanded', function (expanded, oldExpanded) {
				if (angular.isDefined(expanded)) {
					$map.toggleClass('is-expanded', expanded);
				}
			});

			scope.$watch('data.datepickerDate', function (newDate, oldDate) {
				var newDateIso,
					oldDateIso,
					prettyNewDate,
					prettyOldDate,
					analyticsLabel,
					youtubeId = scope.gdVideoData.youtube_id;

				if (newDate) {
					newDateIso = newDate.toISOString();
					prettyNewDate = moment.utc(newDateIso).format('DD MMM YYYY');
				}

				if (oldDate) {
					oldDateIso = oldDate.toISOString();
					prettyOldDate = moment.utc(oldDateIso).format('DD MMM YYYY');
				}

				if (newDateIso !== oldDateIso) {
					// Override YT date
					if (newDateIso !== scope.gdVideoData.published_date) {
						analyticsLabel = ['of', youtubeId, 'from:', prettyNewDate, 'to:', prettyOldDate];
						scope.gdVideoData.recorded_date_overridden = true;
						scope.gdVideoData.recorded_date = newDateIso;
						scope.displayDate = newDateIso;

						ToastService.show('Saving changes…', false, {
							hideDelay: 0
						});

						scope.gdVideoData.save().then(function () {
							$analytics.eventTrack('change recorded date', {
								category: 'video theatre',
								label: analyticsLabel.join(' ')
							});
							ToastService.hide();
						}, function () {
							ToastService.showError('Unable to save date changes', 3000);
						});
					}
				}
			});
		}
	}
}());

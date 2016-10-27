/**
 * pages.project Module
 *
 * The video list module.
 */
(function () {
	angular
		.module('pages')
		.controller('ProjectPageCtrl', ProjectPageCtrl);

	/** @ngInject */
	function ProjectPageCtrl($scope, $log, $location, $timeout, $analytics, PageService, VideoModel, CollectionModel, ToastService, project, collection, _, FilterUtils, DialogService, EventService, hotkeys) {
		var ctrl = this,
			analyticsCategory = 'project library';

		ctrl.loaders = {
			project: false
		};

		ctrl.defaultViewMode = 'list';
		ctrl.quickFilter = {};

		ctrl.project = project;
		ctrl.collection = collection;

		ctrl.filter = {};
		ctrl.isFiltering = false;

		ctrl.filterSet = {
			filters: {},
			videos: [],
			tags: []
		};

		ctrl.ordering = {};

		ctrl.currentFilter = null;
		ctrl.archived = false;

		ctrl.videoListOptions = {
			bottomSheetActions: getBottomSheetActions(),
			selectedTab: null
		};

		EventService.setProject(project.id);

		PageService.updatePageData({
			title: ctrl.project.name,
			headerTitle: ctrl.project.name,
			section: 'library',
			subSection: 'videos-list-view',
			loading: false,
			projectId: project.id,
			project: project,
			collectionId: collection ? collection.id : null,
			collection: collection ? collection : null,
			onboarding: {
				id: 'library',
				steps: [{
					title: 'Welcome to Montage',
					text: 'Here are some tips to get you started.'
				}, {
					title: 'Add videos to your project',
					text: 'To get started, click the search icon to search YouTube and add videos that may be of interest to your project.',
					attachTo: '.appbar__toolbar',
					positioning: {
						alignTo: 'top left',
						alignEdge: 'top right',
						position: 'outside',
						gaps: {
							x: 0,
							y: 8
						}
					}
				}, {
					title: 'View project updates',
					text: 'To get context on what people are working on and what\'s already been done, check the project updates button.',
					attachTo: '[data-onboarding-target="project-comments-button"]',
					positioning: {
						alignTo: 'top left',
						alignEdge: 'top right',
						position: 'outside',
						gaps: {
							x: 10,
							y: -6
						}
					}
				}]
			}
		});

		ctrl.exportCollection = function () {
			angular.forEach(ctrl.filteredVideos, function (video) {
				video.selected = true;
			});
			$scope.$broadcast('video:selectedChange');
			ctrl.videoListOptions.selectedTab = 'video-exporter';
		};

		ctrl.updateCollection = function () {
			ToastService.show('Updating collection', false, { hideDelay: 0 });

			CollectionModel
				.save(ctrl.collection.id)
				.then(function () {
					ToastService.update({
						content: 'Collection updated',
						showClose: true
					});
					ToastService.closeAfter(3000);
					PageService.stopLoading();
				});
		};

		ctrl.removeCollection = function ($event) {
			DialogService
				.confirm($event, 'Are you sure you want to delete this collection?')
				.then(function () {
					CollectionModel
						.destroy(ctrl.collection.id)
						.then(function () {
							ToastService.show('Collection deleted', false, { hideDelay: 0 });
							ToastService.closeAfter(3000);
							$location.url('/project/' + ctrl.collection.project_id);
						});
				});
		};

		ctrl.switchView = function (viewMode) {
			var qs = $location.search();
			qs.view = viewMode;
			$location.search(qs);
		};

		ctrl.onFilterSetUpdate = function (filterSet) {
			var cleanedFilters = FilterUtils.cleanFilters(ctrl.filterSet.filters),
				filters = FilterUtils.getB64FilterUrl(cleanedFilters),
				qs = $location.search();

			if (!_.isEmpty(cleanedFilters)) {
				qs.filters = filters;
				ctrl.isFiltering = true;
			} else {
				delete qs.filters;
				ctrl.isFiltering = false;
			}

			$location.search(qs);
		};

		ctrl.hotkeyConfig = [{
			combo: ['g l'],
			description: 'Go to library',
			callback: function () {
				ctrl.switchView('list');
			}
		}, {
			combo: ['g m'],
			description: 'Go to map view',
			callback: function () {
				ctrl.switchView('map');
			}
		}, {
			combo: ['g t'],
			description: 'Go to tag view',
			callback: function () {
				ctrl.switchView('tag');
			}
		}];

		// Hotkeys
		angular.forEach(ctrl.hotkeyConfig, function (config) {
			hotkeys.add(config);
		});

		$scope.$on('$destroy', function () {
			$log.warn('pages.project.controller:$destroy');
			angular.forEach(ctrl.hotkeyConfig, function (config) {
				hotkeys.del(config.combo);
			});
		});

		$scope.$on('project:videosUpdated', function (event, projectId, videos) {
			if (projectId === project.id) {
				ctrl.filterSet.fetch();
			}
		});

		$scope.$on('collection:videosOrderChanged', function (event, collectionId, moveVideoFromId, siblingVideo) {
			ctrl.loaders.project = true;
			ctrl.collection
				.moveVideo(moveVideoFromId, siblingVideo)
				.then(function () {
					refreshVideos();
					ctrl.filterSet.fetch();
					ToastService.showError('Your video was moved successfully');
				}, function(response) {
					ToastService.showError('Error: ' + response.data.error.message, 0);
				})
				.finally(function () {
					ctrl.loaders.project = false;
				});
		});

		$scope.$on('collection:videosUpdated', function (event, projectId, collectionId, videos) {
			var isSameProject = (projectId === project.id),
				isSameCollection = collection && (collectionId === collection.id);

			if (isSameProject || isSameCollection) {
				ctrl.filterSet.fetch();
			}
		});

		$scope.$on('filterSet::fetch::start', function (filters) {
			ctrl.loaders.project = true;
		});

		$scope.$on('filterSet::fetch::end', function (evt) {
			ctrl.loaders.project = false;
		});

		$scope.$on('$routeUpdate', onRouteUpdate);

		$timeout(onRouteUpdate);

		function refreshVideos() {
			var filters = FilterUtils.urlToObj($location.search().filters);
			ctrl.filterSet.setFilters(filters);
		}

		function onRouteUpdate() {
			$log.debug('pages.project.controller:onRouteUpdate');
			var qs = $location.search(),
				filters = FilterUtils.urlToObj(qs.filters),
				ordering = qs.orderBy,
				archivedChanged;

			if (!qs.section || qs.section !== ctrl.section) {
				updateSection(qs.section);
			}

			if (qs.view !== ctrl.videoMode) {
				ctrl.viewMode = qs.view || ctrl.defaultViewMode;
			} else {
				ctrl.viewMode = ctrl.defaultViewMode;
			}

			$analytics.eventTrack('view change', {
				category: analyticsCategory,
				label: ctrl.viewMode
			});

			archivedChanged = (qs.section === 'archived' && !ctrl.archived) || (qs.section !== 'archived' && ctrl.archived);
			ctrl.archived = qs.section === 'archived';

			if (archivedChanged) {
				angular.extend(ctrl.videoListOptions.bottomSheetActions, getBottomSheetActions());
			}

			if (qs.filters !== ctrl.currentFilter || archivedChanged) {
				ctrl.currentFilter = qs.filters;
				ctrl.filterSet.setFilters(filters, ctrl.archived);

			}

			if (ctrl.viewMode === 'tag') {
				ctrl.filterSet.fetchTags();
			} else {
				ctrl.filterSet.fetchVideos();
			}

			if (!ordering) {
				ctrl.ordering.currentKey = ctrl.collection ? 'order' : 'created';
				ctrl.ordering.reverse = !ctrl.collection;
			} else {
				if (ordering.indexOf('-') === 0) {
					// we have a reverse ordering
					ctrl.ordering.currentKey = ordering.slice(1);
					ctrl.ordering.reverse = true;
				} else {
					ctrl.ordering.currentKey = ordering;
					ctrl.ordering.reverse = false;
				}
			}
		}

		function updateSection(section) {
			var projectVidFilter = {
				where: {
					project_id: ctrl.project.id
				}
			};
			ctrl.quickFilter = {
				'archived_at': '!!'
			};

			if (ctrl.projectVideosUnwatcher) {
				ctrl.projectVideosUnwatcher();
			}

			if (section) {
				ctrl.section = section;

				if (section === 'favorites') {
					ctrl.quickFilter.favourited = true;
				} else if (section === 'unwatched') {
					ctrl.quickFilter.watch_count = 0;
				} else if (section === 'archived') {
					ctrl.quickFilter = {};
				}

				if (section !== 'library') {
					$analytics.eventTrack('section change', {
						category: analyticsCategory,
						label: section
					});
				}
			} else {
				ctrl.section = 'library';
			}

			if (section && section === 'archived') {
				projectVidFilter.where.archived_at = {
					'!==': undefined
				};
			} else {
				projectVidFilter.where.archived_at = undefined;
			}

			ctrl.projectVideosUnwatcher = VideoModel.bindAll(projectVidFilter, $scope, 'ctrl.projectVideos');

			PageService.updatePageData({
				section: ctrl.section
			}, true);

		}

		function getBottomSheetActions() {
			return {
				addTo: true && !ctrl.archived,
				batchTag: false && !ctrl.archived,
				markAsDuplicate: true && !ctrl.archived,
				archive: true && !ctrl.archived,
				removeFromCollection: !!collection && !ctrl.archived,
				exportTo: true
			};
		}
	}
}());

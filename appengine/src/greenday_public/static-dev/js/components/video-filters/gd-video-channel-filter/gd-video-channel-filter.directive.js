(function () {
	angular.module('components')
		.directive('gdVideoChannelFilter', videoChannelFilter);

	/** @ngInject */
	function videoChannelFilter(ChannelModel, _) {
		var directive = {
			templateUrl: 'components/video-filters/gd-video-channel-filter/gd-video-channel-filter.html',
			restrict: 'E',
			scope: {
				ngModel: '=',
				project: '=?'
			},
			link: link,
			require: ['^gdVideoFilter', '^gdVideoChannelFilter', '^ngModel'],
			controller: controller,
			controllerAs: 'channelFilterCtrl'
		};

		return directive;

		function link(scope, element, attrs, controllers) {
			var filterCtrl = controllers[0],
				channelFilterCtrl = controllers[1],
				ngModelCtrl = controllers[2];

			scope.ngModelCtrl = ngModelCtrl;
			scope.filterCtrl = filterCtrl;
			scope.nameFilter = '';

			scope.$watch('ngModel', channelFilterCtrl.onModelUpdate);
			scope.$watchCollection('channelFilterCtrl.channels', channelFilterCtrl.updateChannelList);
		}

		function controller($scope) {
			var channelFilterCtrl = this,
				channelFilter = {};

			channelFilterCtrl.channels = [];

			if ($scope.project) {
				channelFilter = { project_id: $scope.project.id };
			}

			ChannelModel
				.findAll(channelFilter, { cacheResponse: false })
				.then(function (channels) {
					channelFilterCtrl.channels = channels;
				});

			channelFilterCtrl.deselectAll = function() {
				angular.forEach(channelFilterCtrl.selectedChannels, function (channel) {
					channel.selected = false;
				});
				channelFilterCtrl.selectedChannels = [];
				channelFilterCtrl.update();
			};

			channelFilterCtrl.toggleChannel = function (channel) {
				var selectedChannels;

				channel.selected = !channel.selected;

				selectedChannels = _.filter(channelFilterCtrl.channels, {selected: true});
				channelFilterCtrl.selectedChannels = selectedChannels;
				channelFilterCtrl.update();
			};

			channelFilterCtrl.update = function () {
				var selectedIds = _.pluck(channelFilterCtrl.selectedChannels, 'id');

				$scope.ngModelCtrl.$setViewValue(selectedIds.join(','));

				$scope.filterCtrl.setTitle({
					items: channelFilterCtrl.selectedChannels,
					titleKey: 'name',
					prefix: 'Uploaded by',
					offset: 2,
					conjunctive: 'and',
					separator: ','
				});
			};

			channelFilterCtrl.updateChannelList = function (newChannels, oldChannels) {
				if (newChannels) {
					channelFilterCtrl.onModelUpdate($scope.ngModel);
				}
			};

			channelFilterCtrl.onModelUpdate = function (newVal, oldVal) {
				if (channelFilterCtrl.channels.length && !angular.equals(newVal, oldVal)) {
					var channelIds = newVal.split(','),
						selectedChannels = [];

					angular.forEach(channelIds, function (channelId) {
						var channel = _.find(channelFilterCtrl.channels, {id: channelId});

						if (channel) {
							channel.selected = true;
							selectedChannels.push(channel);
						}

					});

					channelFilterCtrl.selectedChannels = selectedChannels;
					channelFilterCtrl.update();
				}
			};
		}

	}
}());

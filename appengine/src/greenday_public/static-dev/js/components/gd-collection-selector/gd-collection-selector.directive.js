(function () {
	angular.module('components')
		.directive('gdCollectionSelector', gdCollectionSelector);

	/** @ngInject */
	function gdCollectionSelector($timeout, CollectionModel) {
		var directive = {
			restrict: 'E',
			templateUrl: 'components/gd-collection-selector/gd-collection-selector.html',
			link: link,
			controller: controller,
			controllerAs: 'ctrl',
			require: 'ngModel',
			scope: {
				project: '=',
				ngModel: '='
			}
		};

		return directive;

		function link(scope, element, attrs) {
			scope.$input = element.find('input').eq(0);
			scope.$el = element;
		}

		function controller($scope) {
			var ctrl = this;

			$timeout(function () {
				$scope.$el.on('keydown', function (evt) {
					if (evt.keyCode === 27) {
						ctrl.reset();
					}
					if (evt.keyCode === 13) {
						ctrl.addNewCollection();
					}
					$scope.$apply();
				});
			});

			ctrl.setCollection = function (collection) {
				$scope.ngModel = collection;
			};

			ctrl.showAddCollection = function () {
				ctrl.addingCollection = true;
				$timeout(function () {
					$scope.$input.focus();
				});
			};

			ctrl.reset = function () {
				ctrl.addingCollection = false;
				ctrl.newCollection = CollectionModel.createInstance({
					project_id: $scope.project.id,
					name: ''
				});
			};

			ctrl.addNewCollection = function () {
				ctrl.isBusy = true;
				CollectionModel
					.create(ctrl.newCollection)
					.then(function (collection) {
						ctrl.setCollection(collection);
						ctrl.reset();
						ctrl.isBusy = false;
					});
			};

			$scope.$watch('project', function (newProject) {
				if (newProject) {
					var projectFilter = { project_id: $scope.project.id };
					if (ctrl.collectionUnbinder) {
						ctrl.collectionUnbinder();
					}
					ctrl.collectionUnbinder = CollectionModel
						.bindAll(projectFilter, $scope, 'ctrl.collections');
					CollectionModel
						.findAll(projectFilter);
					ctrl.reset();
				}
			});
		}
	}
}());

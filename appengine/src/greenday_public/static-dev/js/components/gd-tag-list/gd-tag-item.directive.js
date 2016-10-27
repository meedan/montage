(function () {
	angular.module('components')
		.directive('gdTagItem', tagItem);

	/** @ngInject */
	function tagItem($compile, $rootScope) {
		var directive = {
			templateUrl: 'components/gd-tag-list/gd-tag-item.html',
			restrict: 'E',
			scope: {
				flat: '@',
				ngModel: '=',
				tagTemplate: '@',
				tagController: '=?'
			},
			link: link,
			controller: controller,
			controllerAs: 'tagItemCtrl'
		};

		return directive;

		function link(scope, element, attrs, controllers) {
			var subTags = scope.ngModel.subTags || [];

			scope.flat = !!scope.flat;

			if (!scope.flat && subTags) {
				var template = '<gd-tag-list tag-controller="tagController" ng-model="ngModel.subTags" tag-template="{{ ::tagTemplate }}"></gd-tag-list>',
					templateEl = angular.element(template),
					templateScope = $rootScope.$new();

				templateScope.ngModel = subTags;

				$compile(templateEl)(scope, function (clonedElement, scope) {
					element.find('.tag-list__tag').eq(0).append(clonedElement);
				});
			}

		}

		function controller($scope) {
			var tagItemCtrl = this;

			if (!$scope.tagController) {
				$scope.tagController = angular.noop;
			}

			tagItemCtrl.onDrop = function (draggableData, droppableData) {
				$scope.$emit('onTagDrop', draggableData, droppableData);
			};

			$scope.tagClicked = function (evt, tag) {
				evt.preventDefault();
				evt.stopPropagation();
				$scope.$emit('onTagClick', tag, evt.currentTarget);
			};
			$scope.addTagClicked = function (evt, tag) {
				evt.preventDefault();
				evt.stopPropagation();
				$scope.$emit('onAddTagClick', tag, evt.currentTarget);
			};
			$scope.removeTagClicked = function (evt, tag) {
				evt.preventDefault();
				evt.stopPropagation();
				$scope.$emit('onRemoveTagClick', tag, evt.currentTarget);
			};
			$scope.approveTagClicked = function (evt, tag) {
				evt.preventDefault();
				evt.stopPropagation();
				$scope.$emit('onApproveTagClick', tag, evt.currentTarget);
			};
			$scope.editTagClicked = function (evt, tag) {
				evt.preventDefault();
				evt.stopPropagation();
				$scope.$emit('onEditTagClick', tag, evt.currentTarget);
			};
		}

	}
}());

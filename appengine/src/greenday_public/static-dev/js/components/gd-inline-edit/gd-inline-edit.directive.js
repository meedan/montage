(function () {
	angular.module('components')
		.directive('gdInlineEdit', gdInlineEdit);

	/** @ngInject */
	function gdInlineEdit($timeout) {
		var directive = {
			restrict: 'E',
			templateUrl: 'components/gd-inline-edit/gd-inline-edit.html',
			link: link,
			controllerAs: 'ctrl',
			// bindToController: true,
			transclude: true,
			scope: {
				ngModel: '=',
				onSave: '&'
			}
		};

		return directive;

		function link (scope, element) {
			var $input = element.find('input').eq(0);

			scope.editMode = false;

			resetModel();

			function resetModel() {
				scope.fakeModel = angular.copy(scope.ngModel);
			}

			$input.on('blur', function (evt) {
				if (scope.fakeModel !== scope.ngModel) {
					scope.save();
					scope.$apply();
				}
			});

			$input.on('keyup', function (evt) {
				// ESC key press
				if (evt.keyCode === 27) {
					resetModel();
					scope.editMode = false;
					$input.blur();
				}
			});

			scope.save = function () {
				scope.ngModel = scope.fakeModel;
				scope.editMode = false;
				$timeout(function () {
					scope.onSave();
				});
			};

			scope.$watch('editMode', function (newVal) {
				if (newVal === true) {
					$timeout(function () {
						$input.focus();
					});
				}
			});
		}
	}
}());

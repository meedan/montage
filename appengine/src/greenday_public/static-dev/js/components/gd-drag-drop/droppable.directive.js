(function () {
	angular.module('components.dragDrop')
		.directive('droppable', droppable);

		/** @ngInject */
		function droppable() {
			var directive = {
				restrict: 'AE',
				link: link,
				controller: controller,
				require: '^droppable',
				scope: {
					onDrop: '&?'
				}
			};

			return directive;

			function link(scope, element, attrs, droppableCtrl) {
				// this gives us the native JS object
				var el = element[0];

				droppableCtrl.el = element;
				droppableCtrl.droppableData = attrs.droppableData;
				droppableCtrl.hasOnDrop = !!attrs.onDrop;

				el.droppable = true;

				el.addEventListener('dragover', droppableCtrl.onDragOver, false);
				el.addEventListener('dragenter', droppableCtrl.onDragEnter, false);
				el.addEventListener('dragleave', droppableCtrl.onDragLeave, false);
				el.addEventListener('drop', droppableCtrl.onDrop, false);
			}

			function controller($scope) {
				var droppableCtrl = this;

				droppableCtrl.onDragOver = function(e) {
					e.stopPropagation();
					e.dataTransfer.dropEffect = 'move';
					// allows us to drop
					if (e.preventDefault) {
						e.preventDefault();
					}
					this.classList.add('over');
					return false;
				};

				droppableCtrl.onDragEnter = function(e) {
					e.stopPropagation();
					this.classList.add('over');
					return false;
				};

				droppableCtrl.onDragLeave = function(e) {
					e.stopPropagation();
					this.classList.remove('over');
					return false;
				};

				droppableCtrl.onDrop = function(e) {
					// Stops some browsers from redirecting.
					if (e.stopPropagation) {
						e.stopPropagation();
					}

					this.classList.remove('over');

					if (droppableCtrl.hasOnDrop) {
						var draggableData = e.dataTransfer.getData('Text'),
							droppableData = droppableCtrl.droppableData;

						$scope.onDrop()(draggableData, droppableData);
					}

					return false;
				};
			}
		}
}());

(function () {
	angular.module('components.dragDrop')
		.directive('draggable', draggable);

		/** @ngInject */
		function draggable() {
			var directive = {
				restrict: 'AE',
				link: link,
				controller: controller,
				require: '^draggable'
			};

			return directive;

			function link(scope, element, attrs, draggableCtrl) {
				// this gives us the native JS object
				var el = element[0];

				draggableCtrl.draggableData = attrs.draggableData;

				el.draggable = true;

				el.addEventListener('dragstart', draggableCtrl.onDragStart, false);
				el.addEventListener('dragend', draggableCtrl.onDragEnd, false);
			}

			function controller() {
				var draggableCtrl = this;

				draggableCtrl.onDragStart = function(e) {
					e.stopPropagation();
					e.dataTransfer.effectAllowed = 'move';
					e.dataTransfer.setData('Text', draggableCtrl.draggableData);
					this.classList.add('drag');
					return false;
				};

				draggableCtrl.onDragEnd = function(e) {
					this.classList.remove('drag');
					return false;
				};
			}
		}
}());

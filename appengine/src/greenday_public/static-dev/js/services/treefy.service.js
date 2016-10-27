/**
 * treefy service
 *
 */
(function () {
angular
	.module('app.services')
	.factory('treefyService', treefyService);

	/** @ngInject */
	function treefyService ($filter) {
		return {
			treefy: treefy
		};

		/**
		 * Creates a sub array of items associated to an object.
		 * The association is solved as in:
		 *
		 * obj.<subItemsAttr> = filter(objArr, {<parentAttr>: obj.<objAttr>}, true);
		 *
		 * e.g.
		 *
		 * obj.subTabs = filter(objArr, {parent_id: obj.id}, true);
		 *
		 * @param  {Array}	objArr       An array of objects
		 * @param  {String}	subItemsAttr The attribute name of the sub items which will be assigned to our object
		 * @param  {String}	parentAttr   The parent attribute name which will be compared against the objAttr
		 * @param  {String}	objAttr      The object attribute name which will be compared against the parentAttr
		 * @return {Array}               The modified array which contains the sub items
		 */
		function treefy(objArr, subItemsAttr, parentAttr, objAttr) {
			var filter = $filter('filter');

			if (!subItemsAttr || !parentAttr || !objAttr) {
				return [];
			}

			angular.forEach(objArr, function (obj) {
				var compareObj = {};
				compareObj[parentAttr] = obj[objAttr];

				obj[subItemsAttr] = filter(objArr, compareObj, true);
			});

			return objArr;
		}
	}
}());

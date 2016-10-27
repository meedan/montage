// lodash patches
(function(_) {
	if (typeof(_) === "undefined") {
		console.error("underscore/lodash not yet imported");
	}

	_.replace = replace;

	/**
	 * Efficiently replaces all of an object's properties with those of
	 * another object
	 * 
	 * Retains the reference to the original object
	 * 
	 * All properties are shallow-copied - use with caution
	 */
	function replace(arrayOrCollection, newArrayOrCollection) {
		if (angular.isDefined(arrayOrCollection.length)) {
			// Using .pop() as it's faster than removing keys and then setting
			// the array length to 0. See http://jsperf.com/empty-javascript-array.
			while (arrayOrCollection.length > 0) {
				arrayOrCollection.pop();
			}

			angular.forEach(newArrayOrCollection, function (val) {
				arrayOrCollection.push(val);
			});
		}
		else {
			emptyObject(arrayOrCollection);
			_.extend(arrayOrCollection, newArrayOrCollection);
		}

		return arrayOrCollection;
	}

	/**
	 * Removes all of an object's properties
	 */
	function emptyObject(object) {
		var props = Object.keys(object),
			index = -1,
			length = props.length;

		while (++index < length) {
			delete object[props[index]];
		}

		return object;
	}
})(_);
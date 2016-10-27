describe('Unit: Testing services', function () {
	var FilterUtils,
		testSearchObj = {
			location: {
				lat: 123.4,
				lng: 567.8,
				zoom: 9
			},
			channel: null,
			tags: [1, 2, 3, 4],
			date: new Date('13 October 1981').toISOString()
		},
		testSearchString = 'JTdCJTIybG9jYXRpb24lMjIlM0ElN0IlMjJsYXQlMjIlM0ExMjMuNCUyQyUyMmxuZyUyMiUzQTU2Ny44JTJDJTIyem9vbSUyMiUzQTklN0QlMkMlMjJjaGFubmVsJTIyJTNBbnVsbCUyQyUyMnRhZ3MlMjIlM0ElNUIxJTJDMiUyQzMlMkM0JTVEJTJDJTIyZGF0ZSUyMiUzQSUyMjE5ODEtMTAtMTJUMjMlM0EwMCUzQTAwLjAwMFolMjIlN0Q=',
		testCacheObj = {
			watch_count: 1,
			favourited: true,
			highlighted: false,
			b: 4,
			a: 5
		},
		testCacheString = 'a=5&b=4&favourited=true&highlighted=false&watch_count=1';

	beforeEach(module('app.services'));

	beforeEach(inject(function (_FilterUtils_) {
		FilterUtils = _FilterUtils_;
	}));

	describe('FilterUtils service:', function () {

		it('should contain the FilterUtils', function() {
			expect(FilterUtils).not.toBe(null);
		});

		it('should convert a nested object to a namespaced querystring', function() {
			expect(FilterUtils.objToUrl(testSearchObj)).toEqual(testSearchString);
		});

		it('should convert a namespaced querystring to a nested object', function() {
			expect(FilterUtils.urlToObj(testSearchString)).toEqual(testSearchObj);
		});

		it('should stringify and order an object and return a string', function() {
			expect(FilterUtils.generateCacheKeyFromFilters(testCacheObj)).toEqual(testCacheString);
		});

	});
});

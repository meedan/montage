(function () {
	angular
		.module('app.resources')
		.factory('UserModel', UserResource);

	/** @ngInject */
	function UserResource(DS, API_BASE_URL, DSHttpAdapter) {
		var UserModel = DS.defineResource({
			name: 'user',
			endpoint: 'users',
			idAttribute: 'c_id',
			relations: {},
			computed: {
				c_id: ['', function () {
					return 'me';
				}]
			},
			actions: {
				acceptNDA: {
					pathname: 'nda',
					method: 'POST'
				}
			},
			methods: {
				getStats: function () {
					var self = this,
						params = [
							API_BASE_URL,
							'users', 'me',
							'stats'
						];

					return DSHttpAdapter
						.GET(params.join('/'))
						.then(function (data) {
							self.stats = data.data;
							return data.data;
						});
				}
			}
		});

		return UserModel;
	}
}());

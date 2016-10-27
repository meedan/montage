describe('Unit: Testing services', function () {
	var DialogService,
		$q,
		$timeout,
		$mdDialog;

	beforeEach(module('app.services'));

	beforeEach(inject(function (_DialogService_, _$q_, _$mdDialog_, _$timeout_) {
		DialogService = _DialogService_;
		$q = _$q_;
		$timeout = _$timeout_;
		$mdDialog = _$mdDialog_;
	}));

	describe('DialogService service:', function () {

		it('should contain the DialogService', function() {
			expect(DialogService).not.toBe(null);
		});

		it('should return an object with confirm function', function() {
			expect(typeof DialogService.confirm).toBe('function');
		});

		it('should return an object with showAddCollaboratorsDialog function', function() {
			expect(typeof DialogService.showAddCollaboratorsDialog).toBe('function');
		});

		it('should return an object with showAddCollectionDialog function', function() {
			expect(typeof DialogService.showAddCollectionDialog).toBe('function');
		});

		it('should return an object with showUserSettingsDialog function', function() {
			expect(typeof DialogService.showUserSettingsDialog).toBe('function');
		});

		it('should resolve the promise when calling $mdDialog.hide()', function(done) {
			var mockDeferred = $q.defer();

			spyOn($mdDialog, 'show').and.returnValue(mockDeferred.promise);
			spyOn($mdDialog, 'hide').and.callFake(function () {
				mockDeferred.resolve();
			});

			DialogService.confirm().then(function () {
				done();
			});

			$timeout(function () {
				DialogService.hide();
			});

			$timeout.flush();
		});

		it('should reject the promise with <reason> when calling $mdDialog.cancel(reason)', function(done) {
			var mockDeferred = $q.defer();

			spyOn($mdDialog, 'show').and.returnValue(mockDeferred.promise);
			spyOn($mdDialog, 'cancel').and.callFake(function () {
				mockDeferred.reject('cancel');
			});

			DialogService.confirm().then(function () {

			}, function (reason) {
				expect(reason).toBe('cancel');
				done();
			});

			$timeout(function () {
				DialogService.cancel('cancel');
			});

			$timeout.flush();
		});
	});
});

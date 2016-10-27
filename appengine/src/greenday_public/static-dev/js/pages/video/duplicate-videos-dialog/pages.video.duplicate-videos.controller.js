/**
 * The video theater module.
 */
(function () {
	angular
		.module('pages.video')
		.controller('DuplicateVideosDialogCtrl', DuplicateVideosDialogCtrl);

	/** @ngInject */
	function DuplicateVideosDialogCtrl(_, $q, $scope, $location, $mdDialog,
		$timeout, ToastService, VideoModel, video, dupeVideos,
		COMPOUND_KEY_SEPARATOR) {

		var ctrl = this;

		// This array will *always* contain the list of duplicates as it
		// currently stands on the server. It will not be mutated until
		// duplicated have been successfully added or removed from it on
		// the server.
		var existingDuplicates = dupeVideos;

		/////////////////
		// Scope API
		/////////////////
		$scope.video = video;

		// State variable used to show the saving spinner at the
		// appropriate time.
		$scope.saving = false;

		// State variable used to show when we are fetching a video's
		// information asynchronously.
		$scope.loading = false;

		// The "working copy" list of duplicates. At first, this will contain
		// only videos which are already marked as duplicates of the current
		// video. As the user adds and removes videos from the list of
		// duplicates this array will be mutated.
		$scope.duplicates = existingDuplicates.slice(0);

		$scope.data = {
			// The current query for the autocomplete.
			query: null,
		};

		/////////////////
		// Controller API
		/////////////////
		ctrl.addDuplicate = addDuplicate;

		// Helper method to remove duplicates from the "working copy"
		// list of duplicates.
		ctrl.removeDuplicate = removeDuplicate;

		// FIXME: We should create a directive specifically for this
		// video/greenday url input type and make this new directive hook into
		// ng-form's validation stuff nicely.
		// The regex pattern to use for ng-pattern to validate the video URL
		// input field.
		ctrl.videoUrlPattern = getVideoUrlPattern();

		// Functions to be called by the save and cancel buttons in the
		// modal ui.
		ctrl.save = save;
		ctrl.cancel = cancel;

		ctrl.onInputKeyDown = onInputKeyDown;

		/////////////////
		// Scope Watchers
		/////////////////

		/////////////////
		// Scope Events
		/////////////////

		$scope.$on('pagedata:changed', function () {
			cancel();
		});

		/////////////////
		// Scope/Controller function implementations
		/////////////////

		/**
		 * Callback for the Cancel button of the dialog. Simply closes
		 * the dialog.
		 */
		function cancel() {
			$mdDialog.hide();
		}

		/**
		 * Callback for the Save button of the dialog.
		 *
		 * Calculates the difference between the list of duplicates as it exists
		 * on the database (stored in existingDuplicates) and the list which has
		 * been edited by the user as displayed in the modal (stored in
		 * $scope.duplicates).
		 */
		function save() {

			var dupePromise,
				undupePromise,
				ytIdsToMarkDupe = [video.youtube_id],
				ytIdsToMarkUndupe = [];

			// Iterate through the saved list of duplicates and check if each
			// video still exists in the duplicates list. If it does, we don't
			// need to do anything. If it no longer exists (has been removed as
			// a duplicate) we add it to the list of video ids to be removed as
			// duplicates.
			angular.forEach(existingDuplicates, function(video) {
				var remove = !_.find($scope.duplicates, { 'youtube_id': video.youtube_id });

				if (remove) {
					ytIdsToMarkUndupe.push(video.youtube_id);
				}
			});

			// Find duplicates which were just added (but not yet saved).
			angular.forEach($scope.duplicates, function(video) {
				var add = !_.find(existingDuplicates, { 'youtube_id': video.youtube_id });

				if (add) {
					ytIdsToMarkDupe.push(video.youtube_id);
				}
			});

			if (ytIdsToMarkDupe.length > 1) {
				dupePromise = VideoModel.batchMarkAsDuplicate({
					params: {
						project_id: $scope.video.project_id
					},
					data: {
						youtube_ids: ytIdsToMarkDupe
					}
				});
			} else {
				dupePromise = $q.when();
			}

			if (ytIdsToMarkUndupe.length) {
				undupePromise = $scope.video.batchUnduplicate(ytIdsToMarkUndupe);
			}  else {
				undupePromise = $q.when();
			}

			$scope.saving = true;

			return $q.all([dupePromise, undupePromise]).then(function (response) {
				// Once saved, update the duplicate_count property of the video
				// to reflect the new number of duplicates. We have to remember
				// to -1 from ytIdsToMarkDupe to account for the fact that the
				// current video id exists in the array, but shouldn't count
				// towards the count of duplicates.
				video.duplicate_count = existingDuplicates.length + (ytIdsToMarkDupe.length - 1) - ytIdsToMarkUndupe.length;

				$mdDialog.hide();
			}, function (response) {
				console.log('Could not save changes', response);
				ToastService.showError('There was a problem saving your changes', 0);
			}).finally(function () {
				$scope.saving = false;
			});
		}

		/**
		 * Adds a video to the list of videos to be marked as duplicates of the
		 * current video on save.
		 *
		 * @param {Object} video
		 *        The video id or URL to add to the list of duplicates.
		 */
		function addDuplicate(video) {
			var ID_REGEX = /^[a-zA-Z0-9_-]{6,11}$/,
				parser,
				pathParts,
				ytVideoId,
				videoPromise;

			if (video.match(ID_REGEX)) {

				// Looks like a video ID, so we can use it directly to try
				// and fetch the video details.
				ytVideoId = video;

			} else {

				// Assume it's a URL and try and parse the video id out.
				parser = document.createElement('a');
				parser.href = video;

				pathParts = parser.pathname.split('/');
				ytVideoId = pathParts[pathParts.length - 1];
			}

			/* jshint -W116 */
			if (ytVideoId == $scope.video.youtube_id) { // deliberate comparison with type coercion
				ToastService.showError('Cannot mark a video as a duplicate of itself', 0);
				return;
			}
			/* jshint +W116 */

			$scope.loading = true;

			videoPromise = VideoModel.find($scope.video.project_id + COMPOUND_KEY_SEPARATOR + ytVideoId);
			videoPromise.then(function(v) {
				console.log('Retrieved video', v);
				if (!_.findWhere($scope.duplicates, {id: v.id})) {
					$scope.duplicates.push(v);

					$scope.data.query = null;
				}
				else {
					ToastService.showError('Video is already marked as a duplicate', 0);
				}
			}, function (response) {
				console.log('Couldn\'t retrieve video', response);
				ToastService.showError('Error: ' + response.data.error.message, 0);
			})
			.finally(function() {
				$scope.loading = false;
			});
		}

		/**
		 * Removes a video from the list of videos to be marked as duplicates
		 * of the current video on save.
		 *
		 * @param {Object} video
		 *        The video model to remove from the list of duplicates.
		 */
		function removeDuplicate(video) {
			var dupeIndex = _.findIndex($scope.duplicates, { 'youtube_id': video.youtube_id });
			$scope.duplicates.splice(dupeIndex, 1);
		}

		/**
		 * Returns the regex required by ng-pattern to validate a valid Montage
		 * video URL.
		 *
		 * @return {R}
		 *         The regular expression pattern to validate against.
		 */
		function getVideoUrlPattern() {
			var ytIdPattern = '\[a-zA-Z0-9_-\]\{6,11\}',
				r,
				url;

			url = $location.protocol() + '://' + $location.host();

			if ($location.port()) {
				url += '(:' + $location.port() + ')?';
			}

			url += '/project/(\\d+)/video/';
			// Escape the URL for use within a RegExp.
			// From http://stackoverflow.com/questions/3561493/is-there-a-regexp-escape-function-in-javascript
			url.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
			r = new RegExp('^(' + url + '(' + ytIdPattern + ')|' + ytIdPattern + ')', 'i');

			return r;
		}

		function onInputKeyDown($event) {
			if ($event.keyCode === 13 /* ENTER */) {
				$event.preventDefault();
				addDuplicate($scope.data.query);
			}
		}
	}
}());

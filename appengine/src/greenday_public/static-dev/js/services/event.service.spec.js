describe('Unit: Event service', function () {
	var EventService;

	beforeEach(module('app.services'));

	beforeEach(inject(function (_EventService_) {
		EventService = _EventService_;
	}));

	describe('EventService:', function () {

		it('should contain the EventService', function() {
			expect(EventService).not.toBe(null);
		});

		describe('EventService:Basics:', function () {
			it('should set the projectId', function() {
				EventService.setProject(1);
				expect(EventService.currentProjectId).toBe(1);
			});

			it('should set the videoId', function() {
				EventService.setVideo(1);
				expect(EventService.currentVideoId).toBe(1);
				expect(EventService.currentProjectId).toBe(null);
			});

			it('should set the videoId with projectId', function() {
				EventService.setVideo(1, 2);
				expect(EventService.currentVideoId).toBe(1);
				expect(EventService.currentProjectId).toBe(2);
			});
		});

		describe('EventService:Channels:', function () {
			it('should get the channels with projectId', function() {
				var projectId = 1,
					expected = ['projectid-' + projectId];

				EventService.setProject(projectId);
				expect(EventService.getChannels()).toEqual(expected);
			});

			it('should get the channels with projectId and videoId', function() {
				var projectId = 1,
					videoId = 2,
					expected = ['projectid-' + projectId, 'videoid-' + videoId];

				EventService.setVideo(videoId, projectId);
				expect(EventService.getChannels()).toEqual(expected);
			});
		});

	});
});

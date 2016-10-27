(function () {
	angular
		.module('app.resources')
		.factory('OneSearchModel', OneSearchModel)
		.factory('OneSearchVideoModel', OneSearchVideoModel)
		.factory('OneSearchService', OneSearchService);

	/** @ngInject */
	function OneSearchModel(DS) {
		var oneSearchModel = DS.defineResource({
			name: 'one-search',
			endpoint: 'onesearch',
			actions: {
				search: {
					pathname: 'advanced/video',
					method: 'GET'
				}
			}
		});

		return oneSearchModel;
	}

	/** @ngInject */
	function OneSearchVideoModel(DS) {
		var oneSearchModel = DS.defineResource({
			name: 'one-search-video',
			endpoint: 'onesearch',
			idAttribute: 'youtube_id'
		});

		return oneSearchModel;
	}

	/** @ngInject */
	function OneSearchService($q, $location, $filter, YouTubeDataService, OneSearchModel, OneSearchVideoModel, PageService, _, moment) {
		var service = {
				doSearch: doSearch,
				ytNextPageToken: null,
				currentResults: []
			};

		return service;

		function buildUrl() {
			var qs = $location.search(),
				params = [];

			angular.forEach(qs, function (value, key) {
				if (key !== 'searchVisible') {
					params.push(key + '=' + value);
				}
			});

			if (params.length) {
				return '?' + params.join('&');
			}

			return '';
		}

		function doSearch(filters, isLoadMore) {
			var oneSearchPromise,
				ytSearchPromise,
				dfd = $q.defer(),
				promises = [],
				hasRecordedDate = filters.date && filters.date.match(/^recorded_date/),
				hasLocation = filters.location && (filters.location === 'true' || filters.location === 'false');

			if (!isLoadMore) {
				ytNextPageToken = null;

				// Clear the videos before doing the new request
				OneSearchVideoModel.ejectAll();

				oneSearchPromise = doOneSearch(filters);
				promises.push(oneSearchPromise);
			}

			if (!filters.tag_ids && !hasRecordedDate && !hasLocation) {
				ytSearchPromise = doYoutubeSearch(filters);
				promises.push(ytSearchPromise);
			}

			$q.all(promises).then(function () {
				dfd.resolve(OneSearchVideoModel.getAll());
			}, function (reason) {
				dfd.reject(reason);
			});

			return dfd.promise;
		}

		function doOneSearch(filters) {
			var oneSearchDeferred = $q.defer(),
				qs = buildUrl(),
				projectId = PageService.getPageData().projectId,
				filterObj = angular.extend({}, filters, {project_id: projectId});

			OneSearchModel
				.search({ params: filterObj})
				.then(function(data) {
					// Montage videos are already in the format we need
					var results = data.data.items,
						video;

					angular.forEach(results, function (result, index) {
						video = OneSearchVideoModel.createInstance(result);
						video.theatre_url = '/project/' + video.project_id + '/video/' + video.youtube_id + qs;
						video.order = index;
						OneSearchVideoModel.inject(video);
					});
					oneSearchDeferred.resolve(results);
				}, function(e) {
					oneSearchDeferred.reject(e);
				});

			return oneSearchDeferred.promise;
		}

		function doYoutubeSearch(filters) {
			// next check for pasted in playlist / channel urls
			var channelName = youtubeChannelName(filters.q),
				channelId = youtubeChannelId(filters.q),
				playlistId = youtubePlaylistId(filters.q),
				searchType = 'video',
				ytSearchPromise;

			if (channelName) {
				filters.q = channelName;
				filters.isUsername = true;
				searchType = 'channel';
			} else if (channelId) {
				filters.q = channelId;
				filters.isUsername = false;
				searchType = 'channel';
			} else if (playlistId) {
				filters.q = playlistId;
				searchType = 'playlist';
			}

			// work out what sort of YouTube search to perform
			if (searchType === 'video') {
				ytSearchPromise = searchYouTubeVideo(filters);
			} else if (searchType === 'channel') {
				ytSearchPromise = searchYouTubeChannel(filters);
			} else if (searchType === 'playlist') {
				ytSearchPromise = searchYouTubePlaylist(filters);
			}

			return ytSearchPromise;
		}

		function youtubeChannelName(url) {
			if (!url) {
				return false;
			}
			var r = /^(https?:\/\/)?(www\.)?youtube\.com\/user\/([\w\-\_]+)/,
				matches = url.match(r);
			return matches ? matches[3] : false;
		}

		function youtubeChannelId(url) {
			if (!url) {
				return false;
			}
			var r = /^(https?:\/\/)?(www\.)?youtube\.com\/channel\/(UC[\w\-\_]+)/,
				matches = url.match(r);
			return matches ? matches[3] : false;
		}

		function youtubePlaylistId(url) {
			if (!url) {
				return false;
			}
			var r = /^(https?:\/\/)?(www\.)?youtube\.com\/playlist\?list=([\w\-\_]+)/,
				matches = url.match(r);
			return matches ? matches[3] : false;
		}

		function parseFilters(filters) {
			var searchObj = {},
				loc,
				date,
				toDate,
				dateObj,
				toDateObj,
				dateParts,
				dateType,
				dateMode;

			// pass any greenday filters applied to the YT search
			if (filters.channel_ids) {
				searchObj.channelId = filters.channel_ids.split(',')[0];
			}

			// same for greenday location filter
			if (filters.location) {
				loc = filters.location.split('__');
				searchObj.location = loc[0];

				if (loc[1]) {
					searchObj.location += ',' + loc[1];
				}

				if (loc[2]) {
					searchObj.locationRadius = loc[2] + 'mi';
				}
			}

			if (filters.date) {
				dateParts = filters.date.split('__');
				date = dateParts[2];
				toDate = dateParts[3];
				dateObj = moment.utc(date, 'YYYY-MM-DD');
				toDateObj = moment.utc(toDate, 'YYYY-MM-DD');
				dateMode = dateParts[1];
				dateType = dateParts[0];

				if (dateType === 'publish_date') {
					switch (dateMode) {
						case 'exact':
							dateObj.subtract(1, 'seconds');
							searchObj.publishedAfter = dateObj.toISOString();
							dateObj.add(1, 'days');
							searchObj.publishedBefore = dateObj.toISOString();
							break;

						case 'before':
							dateObj.startOf('day');
							searchObj.publishedBefore = dateObj.toISOString();
							break;

						case 'after':
							dateObj.endOf('day');
							searchObj.publishedAfter = dateObj.toISOString();
							break;

						case 'between':
							dateObj.startOf('day');
							searchObj.publishedAfter = dateObj.toISOString();
							toDateObj.endOf('day');
							searchObj.publishedBefore = toDateObj.toISOString();
							break;

						case 'notbetween':
							dateObj.startOf('day');
							searchObj.publishedBefore = dateObj.toISOString();
							toDateObj.endOf('day');
							searchObj.publishedAfter = toDateObj.toISOString();
							break;
					}
				}
			}

			return searchObj;
		}

		function searchYoutube(section, operation, searchParams, promiseToResolve, youtubeIdCollectorFn) {
			if (service.ytNextPageToken) {
				searchParams.pageToken = service.ytNextPageToken;
			}

			YouTubeDataService
				.request(section, operation, searchParams)
				.then(function (results) {
					// once we have results back from YouTube, de-dupe and return.
					var youtubeIds = _.map(results.items, youtubeIdCollectorFn),
						detailRequest = YouTubeDataService.request('videos', 'list', {
							id: youtubeIds.join(','),
							part: 'snippet,contentDetails',
							maxResults: 50,
							type: 'video'
						});

					if (results.nextPageToken) {
						service.ytNextPageToken = results.nextPageToken;
					} else {
						service.ytNextPageToken = null;
					}

					detailRequest.then(function (videos) {
						getVideoDetails(results, videos);
						promiseToResolve.resolve(OneSearchVideoModel.getAll());
					});
				});
		}

		function searchYouTubeChannel(filters) {
			var youtubeSearchDeferred = $q.defer(),
				searchObj = {
					channelId: filters.q,
					part: 'snippet',
					maxResults: 50,
					type: 'video'
				},
				youtubeIdCollectorFn = function (item) {
					return item.id.videoId;
				};

			angular.extend(searchObj, parseFilters(filters));

			if (filters.isUsername) {
				// We need to make an API call to channel list
				// and get the channel id first
				YouTubeDataService
					.request('search', 'list', {
						part: 'snippet',
						type: 'channel',
						maxResults: 1,
						q: filters.q
					})
					.then(function (response) {
						searchObj.channelId = response.items[0].id.channelId;
						searchYoutube('search', 'list', searchObj, youtubeSearchDeferred, youtubeIdCollectorFn);
					});
			} else {
				searchYoutube('search', 'list', searchObj, youtubeSearchDeferred, youtubeIdCollectorFn);
			}

			return youtubeSearchDeferred.promise;
		}

		function searchYouTubePlaylist(filters) {
			var youtubeSearchDeferred = $q.defer(),
				searchObj = {
					playlistId: filters.q,
					part: 'snippet',
					maxResults: 50,
					type: 'video'
				},
				youtubeIdCollectorFn = function (item) {
					return item.snippet.resourceId.videoId;
				};

			searchYoutube('playlistItems', 'list', searchObj, youtubeSearchDeferred, youtubeIdCollectorFn);

			return youtubeSearchDeferred.promise;
		}

		function searchYouTubeVideo(filters) {
			var youtubeSearchDeferred = $q.defer(),
				searchObj = {
					q: filters.q,
					part: 'snippet',
					maxResults: 50,
					type: 'video'
				},
				youtubeIdCollectorFn = function (item) {
					return item.id.videoId;
				};

			angular.extend(searchObj, parseFilters(filters));

			searchYoutube('search', 'list', searchObj, youtubeSearchDeferred, youtubeIdCollectorFn);

			return youtubeSearchDeferred.promise;
		}

		function getVideoDetails(results, videos) {
			var qs = buildUrl();

			angular.forEach(results.items, function (result, index) {
				if (videos.items[index]) {
					var videoDetails = videos.items[index].contentDetails,
						channelTitle = null,
						videoDuration = moment.duration(videoDetails.duration).asSeconds(),
						backupChannelTitle = videos.items[index].snippet.channelTitle,
						durationFilter = $filter('duration'),
						youtube_id = result.id.videoId || result.snippet.resourceId.videoId,
						notes = videos.items[index].snippet.description.replace(/\n/g, '<br>'),
						video;

					// if the result posesses a channel title use that
					if(result.snippet.channelTitle){
						channelTitle = result.snippet.channelTitle;
					} else {
						channelTitle = backupChannelTitle;
					}

					// Montage videos has the priority, so if it exists, don't override
					video = OneSearchVideoModel.get(youtube_id);

					if (!video) {
						// Convert Youtube video -> Montage video
						video = OneSearchVideoModel.createInstance({
							theatre_url: '/video/' + result.id.videoId + qs,
							youtube_id: youtube_id,
							name: result.snippet.title,
							channel_name: channelTitle,
							channel_id: result.snippet.channelId,
							publish_date: result.snippet.publishedAt,
							notes: notes,
							duration: videoDuration,
							tag_count: ' ',
							pretty_duration: durationFilter(videoDuration),
							pretty_publish_date: moment(result.snippet.publishedAt).format('MMM DD, YYYY'),
							order: 1000 + index
						});

						OneSearchVideoModel.inject(video);
					}
				}
			});

			return OneSearchVideoModel.getAll();
		}
	}
}());

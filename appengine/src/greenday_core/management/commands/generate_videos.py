"""
    Management command to generate videos to add to a Project
"""
# import python deps
from optparse import make_option
import isodate
from random import randint, shuffle

# import lib deps
from apiclient import discovery

# import django deps
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

# import greenday deps
from greenday_core.models import (
    Project, Video, GlobalTag, ProjectTag,
    VideoTag, YouTubeVideo, User
)


# class to generate a load of videos for dev purposes
class Command(BaseCommand):
    """
        Managment command that allows us to generate a load of
        videos for a passed project. This is for development
        use only and is designed to allow us to insert large
        amounts of data quickly for profiling, optimisation
        and testing purposes.
    """
    help = (
        u"Generate x videos for passed projects using passed "
        "YouTube channel or Playlist ID and number required")

    # define parameters that can be passed to the command.
    option_list = BaseCommand.option_list + (
        make_option(
            '--project_id', action='store', dest='project_id',
            help='Montage project ID', type="int"),
        make_option(
            '--tag_ids', action='store', dest='tag_ids',
            help='Montage Global Tag IDs', type="string"),
        make_option(
            '--user_id', action='store', dest='user_id',
            help='Montage project user ID', type="int"),
        make_option(
            '--channel_id', action='store', dest='channel_id',
            default=None, help='YouTube Channel ID', type="string"),
        make_option(
            '--playlist_id', action='store', dest='playlist_id',
            default=None, help='YouTube Playlist ID', type="string"),
        make_option(
            '--number', action='store', dest='number', type="int",
            default=10, help='The number of videos to add (Max 50)'),
        )

    # setup default variables / you tube api client etc.
    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.api_key = 'AIzaSyA0fkTv1gU2mlMCdSXwfz_zN0_D1WZqVy8'
        self.channel_id = None
        self.playlist_id = None
        self.user = None
        self.tags = None
        self.youtube = self.youtubev3_client()

    def handle(self, *args, **options):
        """
            Handles all the heavy lifting of the command.
        """
        if not settings.DEBUG:
            raise CommandError(
                'This command can only be run from dev or staging envs')

        # validate project
        if not options.get('project_id'):
            raise CommandError('You must provide a project id.')
        self.project = self.validate_project(options['project_id'])

        # validate user if one passed
        if options.get('user_id'):
            self.user = self.validate_user(options['user_id'])

        # validate number
        self.number = self.validate_number(options['number'])

        # validate tags if passed
        if options.get('tag_ids'):
            self.tags = self.validate_tags(options['tag_ids'])

        # check we have either a channel or playlist id
        if not options['channel_id'] and not options['playlist_id']:
            raise CommandError(
                'You must provide a YouTube playlist or channel id')

        # check we have dont have both a channel and playlist id
        if options['channel_id'] and options['playlist_id']:
            raise CommandError(
                'You can only provide either a channel id or playlist id')

        # assign data source
        if options['channel_id']:
            self.channel_id = options['channel_id']
        elif options['playlist_id']:
            self.playlist_id = options['playlist_id']

        # generate the videos
        self.generate_videos()

    def validate_project(self, project_id):
        """
            Method to validate the passed project id
        """
        try:
            return Project.objects.get(pk=project_id)
        except Project.DoesNotExist:
            raise CommandError(
                'Project with id %s does not exist' % project_id)

    def validate_tags(self, tag_ids):
        """
            Method to validate the csv seperated list of global tag
            ids.
        """
        tag_ids = tag_ids.split(',')
        tags = []
        for tag_id in tag_ids:
            try:
                tag_id = int(tag_id)
            except ValueError:
                pass
            else:
                try:
                    gtag = GlobalTag.objects.get(pk=int(tag_id))
                except GlobalTag.objects.DoesNotExist:
                    pass
                else:
                    try:
                        project_tag = ProjectTag.objects.get(
                            project=self.project, global_tag=gtag)
                    except ProjectTag.DoesNotExist:
                        project_tag = ProjectTag.add_root(
                            project=self.project, global_tag=gtag)
                    tags.append(project_tag)
        return tags

    def validate_user(self, user_id):
        """
            Method to validate the passed user id
        """
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            raise CommandError('Invalid user_id')

        if not self.project.is_assigned(user):
            raise CommandError('User must be assigned to the project')

    def validate_number(self, number):
        """
            Validate the number of vidoes to add is a number and that
            its not greater than 200.
        """
        if number > 50:
            raise CommandError(
                'You can only add a max of 200 videos at a time')
        return number

    def youtubev3_client(self):
        """
            Helper function to get a youtube v3 api client.
        """
        return discovery.build('youtube', 'v3', developerKey=self.api_key)

    def get_playlist_videos(self):
        """
            Method to return videos from a YouTube Playlist.
        """
        results = self.youtube.playlistItems().list(
            playlistId=self.playlist_id,
            part='snippet,contentDetails',
            fields='items(snippet(publishedAt,title,description,channelId,'
            'playlistId),contentDetails(videoId))',
            maxResults=self.number,
        ).execute()
        results = self.fetch_extra_video_data(results)
        results = self.fetch_extra_playlist_data(results)
        return results

    def get_channel_videos(self):
        """
            Method to return videos from a YouTube channel.
        """
        channels = self.youtube.channels().list(
            forUsername=self.channel_id, part='snippet,contentDetails',
        ).execute()

        # check we have a result returned and that its only one result
        if len(channels.get('items', [])) == 0:
            channels = self.youtube.channels().list(
                id=self.channel_id, part='snippet,contentDetails',
            ).execute()
            if len(channels.get('items', [])) == 0:
                raise CommandError(
                    'Channel with ID of %s not found' % self.channel_id)
        assert len(channels.get('items', [])) == 1

        # Get the Uploads playlist ID from the channel info
        uploads_list_id = \
            channels['items'][0]['contentDetails']['relatedPlaylists'][
                'uploads']
        uploads = self.youtube.playlistItems().list(
            playlistId=uploads_list_id,
            part='snippet,contentDetails',
            fields='items(snippet(publishedAt,title,description,channelId,'
            'channelTitle,playlistId),contentDetails(videoId))',
            maxResults=self.number,
        ).execute()
        results = self.fetch_extra_video_data(uploads)
        return results

    def fetch_extra_playlist_data(self, results):
        """
            Method to fetch extra playlist data.

            Makes an extra call to the YouTube API to get extra
            data about a playlist. This is because the
            PlaylistItems YouTube API endpoint doesn't return
            all Playlist related data.
        """
        playlists = self.youtube.playlists().list(
            part='snippet,contentDetails',
            id=self.playlist_id,
            fields='items(snippet(title,channelTitle))'
        ).execute()
        assert len(playlists.get('items', [])) == 1
        item = playlists.get('items')[0]
        for result in results:
            result['snippet']['channelTitle'] = item['snippet']['channelTitle']
            result['snippet']['playlistName'] = item['snippet']['title']
        return results

    def fetch_extra_video_data(self, results):
        """
            Method to fetch extra video data.

            Makes an extra call to the YouTube API to get extra
            data about each video in a result set. This is because the
            Playlist and Channel YouTube API endpoints don't return
            all video related data - duration and geo-location for example.
        """
        updated_results = []
        for result in results.get('items', []):
            extra = {}
            extra_data = self.youtube.videos().list(
                part='snippet,contentDetails,recordingDetails',
                id=result['contentDetails']['videoId'],
                fields='items(snippet(channelTitle),contentDetails(duration),'
                'recordingDetails)'
                ).execute()

            # check we only have one result and then assign that result
            # to a local variable.
            assert len(extra_data.get('items', [])) == 1
            item = extra_data.get('items')[0]

            # parse the duration
            timedelta = isodate.parse_duration(
                item['contentDetails']['duration'])
            extra['duration'] = int(timedelta.total_seconds())

            # parse the geo-location data
            extra['geo'] = extra['recorded_date'] = None
            if 'recordingDetails' in item:
                if 'recordingDate' in item['recordingDetails']:
                    rec_time = item['recordingDetails']['recordingDate']
                    extra['recorded_date'] = isodate.parse_datetime(rec_time)
                if 'location' in item['recordingDetails']:
                    loc = item['recordingDetails']['location']
                    extra['geo'] = '%f %f' % (
                        loc['latitude'], loc['longitude'])
            result['extra'] = extra
            updated_results.append(result)
        return updated_results

    def generate_videos(self):
        """
            Method to pull down video meta data from YouTube and store
            them against the relevant project.
        """

        # grab so videos based on the command args that were passed
        if self.playlist_id:
            videos = self.get_playlist_videos()
        else:
            videos = self.get_channel_videos()

        # grab all users assigned to the project and a create a count
        # 0 index.
        users = self.project.assigned_users
        user_count = int(users.count() - 1)

        # loop through videos. Check if they already exist for the project.
        # if not add them to the project.
        for video in videos:
            video_id = video['contentDetails']['videoId']
            playlist_name = None
            lat = None
            lon = None
            if video['snippet'].get('playlistName'):
                playlist_name = video['snippet']['playlistName']
            if video['extra']['geo']:
                lat, lon = video['extra']['geo'].split(' ')
                try:
                    lat = float(lat)
                    lon = float(lon)
                except TypeError:
                    raise CommandError(
                        "Can't case lat/lon to float- lat: %s lon: %s" % (
                            lat, lon))

            # if we have not been passed a valid user, then assign one
            # at random.
            if not self.user:
                self.user = users[
                    randint(0, user_count - 1)] if user_count >= 0 else None

            # if we have tags that decide on a random number of them to
            # apply to the video and shuffle the list of tags so that
            # the slice we take is also randomised.
            if self.tags:
                num_tags_to_apply = randint(0, len(self.tags) - 1)
                apply_tags = None
                if num_tags_to_apply > 0:
                    shuffle(self.tags)
                    apply_tags = self.tags[:num_tags_to_apply]

            yt_video, _ = YouTubeVideo.objects.update_or_create(
                youtube_id=video_id,
                defaults=dict(
                    youtube_id=video_id,
                    name=video['snippet']['title'],
                    latitude=lat,
                    longitude=lon,
                    notes=video['snippet']['description'],
                    publish_date=isodate.parse_datetime(
                        video['snippet']['publishedAt']),
                    recorded_date=video['extra']['recorded_date'],
                    channel_id=video['snippet']['channelId'],
                    channel_name=video['snippet']['channelTitle'],
                    playlist_id=video['snippet']['playlistId'],
                    playlist_name=playlist_name,
                    duration=video['extra']['duration'],
                )
            )

            # build the video object
            video, created = Video.objects.get_or_create(
                project=self.project,
                youtube_video=yt_video,
                youtube_id=yt_video.youtube_id,
                defaults=dict(
                    user=self.user,
                ))

            if created:
                print (
                    'YouTube video with ID %s has been added '
                    'to the project' % video_id)
            else:
                print (
                    'YouTube video with ID %s already exists for '
                    'this project. Skipping' % video_id)

            # build tags and tag instances
            if self.tags and apply_tags:
                for tag in apply_tags:
                    video_tag, _ = VideoTag.objects.get_or_create(
                        project_tag=tag,
                        video=video,
                        defaults={
                            "project": self.project
                        })
                    start_time = randint(0, yt_video.duration / 2)
                    end_time = randint(start_time + 1, yt_video.duration)
                    try:
                        video_tag.tag_video(start_time, end_time)
                    except:
                        pass

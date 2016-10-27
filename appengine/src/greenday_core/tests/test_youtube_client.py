"""
    Tests for :mod:`greenday_core.youtube_client <greenday_core.youtube_client>`
"""
import datetime
import mock
from milkman.dairy import milkman

from .base import AppengineTestBed

import isodate
from ..youtube_client import YouTubeClient

from ..models import YouTubeVideo

YT_RAW_DATA = {
    "YxgsxaFWWHQ": {
        u'contentDetails': {
            u'caption': u'true',
            u'definition': u'hd',
            u'dimension': u'2d',
            u'duration': u'PT4M46S',
            u'licensedContent': True
        },
        u'etag': u'"k1sYjErg4tK7WaQQxvJkW5fVrfg/V16HAT30JCSZHgYpoKbyBPpC-WU"',
        u'id': u'YxgsxaFWWHQ',
        u'kind': u'youtube#video',
        u'recordingDetails': {
            u'location': {
                u'altitude': 0.0,
                u'latitude': 51.5073318481,
                u'longitude': -0.127680003643}},
        u'snippet': {
            u'categoryId': u'27',
            u'channelId': u'UC2C_jShtL725hvbm1arSV9w',
            u'channelTitle': u'CGP Grey',
            u'description': u'Before you see the final Hobbit Movie, learn about the mythology of The Lord of The Rings universe\nWallpapers from the video available at Patreon: http://www.patreon.com/creation?hid=1385484 and Subbable: https://subbable.com/cgpgrey\n\nOfficial discussion at: http://www.reddit.com/r/CGPGrey/comments/2pky88/the_lord_of_the_rings_mythology_explained/\n\nHello Internet Podcast on The Hobbit: https://www.youtube.com/watch?v=8gsWj8YTOyk#t=2455\n\nSpecial Thanks:\n\nProfessor Verlyn Flieger http://mythus.com/\n\nhttp://askmiddlearth.tumblr.com/\n\nSoliloquy: http://goo.gl/LQEakz\n\n@icel, @VivaLaDiva405, Rory Howington, Vijayalakshmi, Jason Arkin, Malthe Agger, rictic, Ian, Saki Comandao, Edward DeLany, Chris Kitching, PervertedThomas, Brian Peterson, Ron Bowes, T\xf3mas \xc1rni J\xf3nasson, Michael Morden, Mikko, Derek Bonner, Derek Jackson, Iain Flockton, Jim, Sokhom Chhim, Shawn Bazin, Finn Kelly, Dan, Christine D\xf6nszelmann, Orbit_Junkie, Eren Polat, Mark Elders, Lars-G\xf6ran, Veronica Peshterianu, Daniel Heeb, Juan Villagrana, Ernesto Jimenez, Paul Tomblin, Travis Wichert, Andrew Bailey, Israel Armando, Teddy, Ricardo, Yousef Hasan, Ruud Hermans, Keng, Alex Morales, Ryan E Manning, Linh, Erik Parasiuk, Rhys Parry, Arian Flores, Jennifer Richardson, Maarten van der Blij, Bj\xf6rn Mor\xe9n, Jim, Eric Stangeland, Rustam Anvarov, Sam Kokin, Kevin Anderson, Gustavo Jimenez, Thomas Petersen, Kyle Bloom, Osric Lord-Williams, Myke Hurley, David, Ryan Nielsen, Esteban Santana Santana, Terry Steiner, Dag Viggo Lok\xf8en, Tristan Watts-Willis, Ian N Riopel, John Rogers, Edward Adams, Ryan, Kevin, Nicolae Berbece, Alex Prescott, Leon, Alexander Kosenkov, Daniel Slater, Sunny Yin, Sigur\xf0ur Sn\xe6r Eir\xedksson, Maxime Zielony, Anders, ken mcfarlane, AUFFRAY Clement, Aaron Miller, Bill Wolf, Himesh Sheth, Thomas Weir, Caswal Parker, Brandon Callender, Joseph, Stephen Litt Belch, Sean Church, Pierre Perrott, Ilan, Mr.Z, Heemi Kutia, Timothy Moran, Peter Lomax, Quin Thames, darkmage0707077, \xd8rjan Sollie, Emil, Kelsey Wainwright, Richard Harrison, Robby Gottesman, Ali Moeeny, Lachlan Holmes, Jonas Maal\xf8e, John Bevan, Dan Hiel, Callas, Elizabeth Keathley, John Lee, Tijmen van Dien, ShiroiYami, thomas van til, Drew Stephens, Owen Degen, Tobias Gies, Alex Schuldberg, Ryan Constantin, Jerry Lin, Rasmus Svensson, Bear, Lars, Jacob Ostling, Cody Fitzgerald, Guillaume PERRIN, John Waltmans, Solon Carter, Joel Wunderle, Rescla, GhostDivision, Andrew Proue, David Lombardo, Tor Henrik Lehne, David Palomares, Cas Eli\xebns, paul everitt, Karl Johan Stensland Dy, Freddi H\xf8rlyck\n\nArtwork:\n\nhttp://kittyninjafish.deviantart.com/\n\n\nMusic:\n\nhttp://incompetech.com/',
            u'liveBroadcastContent': u'none',
            u'localized': {
                u'description': u'Before you see the final Hobbit Movie, learn about the mythology of The Lord of The Rings universe\nWallpapers from the video available at Patreon: http://www.patreon.com/creation?hid=1385484 and Subbable: https://subbable.com/cgpgrey\n\nOfficial discussion at: http://www.reddit.com/r/CGPGrey/comments/2pky88/the_lord_of_the_rings_mythology_explained/\n\nHello Internet Podcast on The Hobbit: https://www.youtube.com/watch?v=8gsWj8YTOyk#t=2455\n\nSpecial Thanks:\n\nProfessor Verlyn Flieger http://mythus.com/\n\nhttp://askmiddlearth.tumblr.com/\n\nSoliloquy: http://goo.gl/LQEakz\n\n@icel, @VivaLaDiva405, Rory Howington, Vijayalakshmi, Jason Arkin, Malthe Agger, rictic, Ian, Saki Comandao, Edward DeLany, Chris Kitching, PervertedThomas, Brian Peterson, Ron Bowes, T\xf3mas \xc1rni J\xf3nasson, Michael Morden, Mikko, Derek Bonner, Derek Jackson, Iain Flockton, Jim, Sokhom Chhim, Shawn Bazin, Finn Kelly, Dan, Christine D\xf6nszelmann, Orbit_Junkie, Eren Polat, Mark Elders, Lars-G\xf6ran, Veronica Peshterianu, Daniel Heeb, Juan Villagrana, Ernesto Jimenez, Paul Tomblin, Travis Wichert, Andrew Bailey, Israel Armando, Teddy, Ricardo, Yousef Hasan, Ruud Hermans, Keng, Alex Morales, Ryan E Manning, Linh, Erik Parasiuk, Rhys Parry, Arian Flores, Jennifer Richardson, Maarten van der Blij, Bj\xf6rn Mor\xe9n, Jim, Eric Stangeland, Rustam Anvarov, Sam Kokin, Kevin Anderson, Gustavo Jimenez, Thomas Petersen, Kyle Bloom, Osric Lord-Williams, Myke Hurley, David, Ryan Nielsen, Esteban Santana Santana, Terry Steiner, Dag Viggo Lok\xf8en, Tristan Watts-Willis, Ian N Riopel, John Rogers, Edward Adams, Ryan, Kevin, Nicolae Berbece, Alex Prescott, Leon, Alexander Kosenkov, Daniel Slater, Sunny Yin, Sigur\xf0ur Sn\xe6r Eir\xedksson, Maxime Zielony, Anders, ken mcfarlane, AUFFRAY Clement, Aaron Miller, Bill Wolf, Himesh Sheth, Thomas Weir, Caswal Parker, Brandon Callender, Joseph, Stephen Litt Belch, Sean Church, Pierre Perrott, Ilan, Mr.Z, Heemi Kutia, Timothy Moran, Peter Lomax, Quin Thames, darkmage0707077, \xd8rjan Sollie, Emil, Kelsey Wainwright, Richard Harrison, Robby Gottesman, Ali Moeeny, Lachlan Holmes, Jonas Maal\xf8e, John Bevan, Dan Hiel, Callas, Elizabeth Keathley, John Lee, Tijmen van Dien, ShiroiYami, thomas van til, Drew Stephens, Owen Degen, Tobias Gies, Alex Schuldberg, Ryan Constantin, Jerry Lin, Rasmus Svensson, Bear, Lars, Jacob Ostling, Cody Fitzgerald, Guillaume PERRIN, John Waltmans, Solon Carter, Joel Wunderle, Rescla, GhostDivision, Andrew Proue, David Lombardo, Tor Henrik Lehne, David Palomares, Cas Eli\xebns, paul everitt, Karl Johan Stensland Dy, Freddi H\xf8rlyck\n\nArtwork:\n\nhttp://kittyninjafish.deviantart.com/\n\n\nMusic:\n\nhttp://incompetech.com/',
                u'title': u'The Lord of the Rings Mythology Explained (Part 1)'
            },
            u'publishedAt': u'2014-12-17T15:12:19.000Z',
            u'thumbnails': {
                u'default': {
                    u'height': 90,
                    u'url': u'https://i.ytimg.com/vi/YxgsxaFWWHQ/default.jpg',
                    u'width': 120
                },
                u'high': {
                    u'height': 360,
                    u'url': u'https://i.ytimg.com/vi/YxgsxaFWWHQ/hqdefault.jpg',
                    u'width': 480
                },
                u'medium': {
                    u'height': 180,
                    u'url': u'https://i.ytimg.com/vi/YxgsxaFWWHQ/mqdefault.jpg',
                    u'width': 320
                },
                u'standard': {
                    u'height': 480,
                    u'url': u'https://i.ytimg.com/vi/YxgsxaFWWHQ/sddefault.jpg',
                    u'width': 640
                }
            },
            u'title': u'The Lord of the Rings Mythology Explained (Part 1)'
        }
    },
    "O37yJBFRrfg": {
        u'contentDetails': {
            u'caption': u'true',
            u'definition': u'hd',
            u'dimension': u'2d',
            u'duration': u'PT5M51S',
            u'licensedContent': True
        },
        u'etag': u'"k1sYjErg4tK7WaQQxvJkW5fVrfg/D4nam3SrMXGzw4cTb2tJiX1EtI8"',
        u'id': u'O37yJBFRrfg',
        u'kind': u'youtube#video',
        u'recordingDetails': {
            u'location': {
                u'altitude': 0.0,
                u'latitude': 51.5073318481,
                u'longitude': -0.127680003643
            }
        },
        u'snippet': {
            u'categoryId': u'27',
            u'channelId': u'UC2C_jShtL725hvbm1arSV9w',
            u'channelTitle': u'CGP Grey',
            u'description': u'CGPGrey T-Shirts: http://dftba.com/product/10m/CGP-Grey-Logo-Shirt\nHelp support videos like this: http://www.cgpgrey.com/subbable\nTwitter: https://twitter.com/cgpgrey\nTumblr: http://cgpgrey.tumblr.com/\n\nG+: https://plus.google.com/115415241633901418932/posts',
            u'liveBroadcastContent': u'none',
            u'localized': {
                u'description': u'CGPGrey T-Shirts: http://dftba.com/product/10m/CGP-Grey-Logo-Shirt\nHelp support videos like this: http://www.cgpgrey.com/subbable\nTwitter: https://twitter.com/cgpgrey\nTumblr: http://cgpgrey.tumblr.com/\n\nG+: https://plus.google.com/115415241633901418932/posts',
                u'title': u'The European Union Explained*'
            },
            u'publishedAt': u'2013-07-02T12:00:32.000Z',
            u'thumbnails': {
                u'default': {
                    u'height': 90,
                    u'url': u'https://i.ytimg.com/vi/O37yJBFRrfg/default.jpg',
                    u'width': 120
                },
                u'high': {
                    u'height': 360,
                    u'url': u'https://i.ytimg.com/vi/O37yJBFRrfg/hqdefault.jpg',
                    u'width': 480
                },
                u'maxres': {
                    u'height': 720,
                    u'url': u'https://i.ytimg.com/vi/O37yJBFRrfg/maxresdefault.jpg',
                    u'width': 1280
                },
                u'medium': {
                    u'height': 180,
                    u'url': u'https://i.ytimg.com/vi/O37yJBFRrfg/mqdefault.jpg',
                    u'width': 320
                },
                u'standard': {
                    u'height': 480,
                    u'url': u'https://i.ytimg.com/vi/O37yJBFRrfg/sddefault.jpg',
                    u'width': 640
                }
            },
            u'title': u'The European Union Explained*'
        }
    }
}

class YouTubeClientTestCase(AppengineTestBed):
    """
        Tests for :class:`greenday_core.youtube_client.YouTubeClient <greenday_core.youtube_client.YouTubeClient>`
    """
    def test_get_video_data(self):
        """
            Test :func:`greenday_core.youtube_client.YouTubeClient.get_video_data <greenday_core.youtube_client.YouTubeClient.get_video_data>`
            returns processed video data
        """
        client = YouTubeClient()

        yt_id = "YxgsxaFWWHQ"
        expected_data = YT_RAW_DATA[yt_id]

        data = client.get_video_data([yt_id])

        video_data = data[yt_id]
        self.assertEqual(expected_data['snippet']['title'], video_data['name'])
        self.assertEqual(
            float(expected_data['recordingDetails']['location']['latitude']),
            video_data['latitude'])
        self.assertEqual(
            float(expected_data['recordingDetails']['location']['longitude']),
            video_data['longitude'])
        self.assertEqual(
            expected_data['snippet']['description'], video_data['notes'])
        self.assertEqual(
            isodate.parse_datetime(expected_data['snippet']['publishedAt']),
            video_data['publish_date'])
        self.assertEqual(
            expected_data['snippet']['channelId'], video_data['channel_id'])
        self.assertEqual(
            expected_data['snippet']['channelTitle'],
            video_data['channel_name'])
        self.assertEqual(
            isodate.parse_duration(
                expected_data['contentDetails']['duration']).total_seconds(),
            video_data['duration'])

    def test_update_videos(self):
        """
            Test :func:`greenday_core.youtube_client.YouTubeClient.update_videos <greenday_core.youtube_client.YouTubeClient.update_videos>`
            updates YouTubeVideo objects with updated data
        """
        video_1 = milkman.deliver(YouTubeVideo, youtube_id='YxgsxaFWWHQ')
        video_2 = milkman.deliver(YouTubeVideo, youtube_id='O37yJBFRrfg')

        client = YouTubeClient()
        client.update_videos((video_1, video_2,))

        for vid in (video_1, video_2,):
            expected_data = YT_RAW_DATA[vid.youtube_id]
            self.assertEqual(expected_data['snippet']['title'], vid.name)
            self.assertEqual(
                float(expected_data['recordingDetails']['location']['latitude']),
                vid.latitude)
            self.assertEqual(
                float(expected_data['recordingDetails']['location']['longitude']),
                vid.longitude)
            self.assertEqual(
                expected_data['snippet']['description'], vid.notes)
            self.assertEqual(
                isodate.parse_datetime(expected_data['snippet']['publishedAt']),
                vid.publish_date)
            self.assertEqual(
                expected_data['snippet']['channelId'], vid.channel_id)
            self.assertEqual(
                expected_data['snippet']['channelTitle'],
                vid.channel_name)
            self.assertEqual(
                isodate.parse_duration(
                    expected_data['contentDetails']['duration']).total_seconds(),
                vid.duration)

    def test_update_or_create_videos(self):
        """
            Test :func:`greenday_core.youtube_client.YouTubeClient.update_or_create_videos <greenday_core.youtube_client.YouTubeClient.update_or_create_videos>`
            updates YouTubeVideo objects with updated data or creates them if they don't already exist
        """
        video_1 = milkman.deliver(YouTubeVideo, youtube_id='YxgsxaFWWHQ')

        new_id = 'O37yJBFRrfg'

        client = YouTubeClient()
        client.update_or_create_videos((video_1.youtube_id, new_id,))

        for vid in YouTubeVideo.objects.all():
            expected_data = YT_RAW_DATA[vid.youtube_id]
            self.assertEqual(expected_data['snippet']['title'], vid.name)
            self.assertEqual(
                float(expected_data['recordingDetails']['location']['latitude']),
                vid.latitude)
            self.assertEqual(
                float(expected_data['recordingDetails']['location']['longitude']),
                vid.longitude)
            self.assertEqual(
                expected_data['snippet']['description'], vid.notes)
            self.assertEqual(
                isodate.parse_datetime(expected_data['snippet']['publishedAt']),
                vid.publish_date)
            self.assertEqual(
                expected_data['snippet']['channelId'], vid.channel_id)
            self.assertEqual(
                expected_data['snippet']['channelTitle'],
                vid.channel_name)
            self.assertEqual(
                isodate.parse_duration(
                    expected_data['contentDetails']['duration']).total_seconds(),
                vid.duration)


    @mock.patch.object(YouTubeVideo, "delete_cached_thumbs")
    def test_update_video_missing_from_yt(self, m_delete_cached_thumbs):
        """
            Test :func:`greenday_core.youtube_client.YouTubeClient.update_videos <greenday_core.youtube_client.YouTubeClient.update_videos>`
            where a video has been removed from youtube
        """
        video_1 = milkman.deliver(
            YouTubeVideo,
            youtube_id='MISSING',
            name="foo",
            channel_id='foo',
            channel_name='foo',
            playlist_id='foo',
            playlist_name='foo',
            duration=42,
            latitude=42,
            longitude=42,
            notes='foo',
            publish_date=datetime.datetime.now(),
            recorded_date=datetime.datetime.now()
        )

        client = YouTubeClient()
        client.update_videos((video_1,))

        for k in (
                'channel_id',
                'channel_name',
                'playlist_id',
                'playlist_name',
                'duration',
                'latitude',
                'longitude',
                'notes',
                'publish_date',
                'recorded_date',):
            self.assertFalse(getattr(video_1, k), "{0} not cleared".format(k))

        self.assertTrue(video_1.missing_from_youtube)
        self.assertEqual('<Video removed>', video_1.name)
        self.assertEqual('MISSING', video_1.youtube_id)

        m_delete_cached_thumbs.assert_called_with()


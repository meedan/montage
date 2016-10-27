"""
    Defines objects which encapsulate custom search behaviour
"""
import datetime
from google.appengine.api import search as search_api
from search.ql import Q, GeoQueryArguments
from search.indexes import Index
from search.query import SearchQuery

from greenday_core.api_exceptions import (
    BadSearchDateFormatException, BadSearchGeoFormatException
)

MILES_TO_METERS_FACTOR = 1.609344 * 1000


def process_comma_seperate_filters(filter_str):
    """
        This method takes a string of comma seperated
        values and returns two lists. One of standard
        values and one of values to be negated

        Returns:
            values, negated_values

        Example Usage:
            process_comma_seperate_filters('23,36,21,-99,150')
            process_comma_seperate_filters('foo,-bar,-car,wookie,han')

        Would return:
            ['23', '36', '21', '150'], ['99']
            ['foo', 'wookie', 'han'], ['bar', 'car']
    """
    if not isinstance(filter_str, basestring):
        raise Exception('filter not a string')
    seperated_values = filter_str.split(',')
    negated_values = [
        val.strip('-') for val in seperated_values if val[0] == '-']
    values = [val for val in seperated_values if val[0] != '-']
    return values, negated_values


# video search bot helper
class VideoSearch(SearchQuery):
    """
        Helper class to allow us to re-use generic
        video searching and filtering functionality.
    """
    @classmethod
    def create(cls, index, document_class=None, ids_only=True):
        """
            Create a search query
        """
        if isinstance(index, basestring):
            index = search_api.Index(name=index)
        elif isinstance(index, Index):
            index = index._index

        return cls(index, document_class=document_class, ids_only=ids_only)

    def filter_projects(self, project_ids):
        """
            Method to filter videos down by project id(s)
        """
        if isinstance(project_ids, basestring) and project_ids.find(',') > -1:
            project_ids = project_ids.split(',')
        return self.filter(project_id=project_ids)

    def filter_collections(self, collection_ids):
        """
            Method to filter videos down by collection id(s)
        """
        if isinstance(collection_ids, basestring) and collection_ids.find(
                ',') > -1:
            collection_ids = collection_ids.split(',')

        return self.filter(collection_ids=collection_ids)

    def geo_search(self, location):
        """
            Method to filter videos based on their geo-information
        """
        if location == 'true':
            return self.filter(has_location="1")

        if location == 'false':
            return self.filter(has_location="0")

        parts = location.split("__")
        if not len(parts) >= 3:
            raise BadSearchGeoFormatException(
                "Location must be of format {lat}__{lon}__{radius}")
        lat, lon, radius = map(float, parts[:3])

        radius *= MILES_TO_METERS_FACTOR

        return self.filter(
            has_location="1",
            location__geo=GeoQueryArguments(lat, lon, radius))

    def filter_channels(self, channel_ids):
        """
            Method to filter videos based on their channel id(s)
        """
        if isinstance(channel_ids, basestring) and channel_ids.find(',') > -1:
            channel_ids = channel_ids.split(',')
        return self.filter(channel_id=channel_ids)

    def filter_tags(self, tag_ids):
        """
            Method to filter or negate videos by tag(s)
        """
        filters = []
        tags, negated_tags = process_comma_seperate_filters(tag_ids)
        if negated_tags:
            filters.append(~Q(tag_ids=negated_tags))
        if tags:
            filters.append(Q(tag_ids=tags))
        return self.filter(*filters)

    def filter_date(self, date_string):
        """
            Method to filter videos by a date string

            date_string is a string formatted in any of the following ways:

            - `{field_name}__{operation}` - where operation is `true` or `false`
            - `{field_name}__{operation}__{date}` - where operation is `after`, `exact` or `before`
            - `{field_name}__{operation}__{from_date}__{to_date}` - where operation is `between` or `notbetween`

            Where:

            - `field_name`: either `published` or `recorded`
            - `operation`: one of:
                - `true`: all videos with this date defined.
                - `false`: all videos without this date defined
                - `after`: all videos where this date is greater than `date`
                - `before`: all videos where this date is less than `date`
                - `exact`: all videos where this date is equal to `date`
                - `between`: all videos where this date is greater than `from_date` and less than `to_date`
                - `notbetween`: all videos where this date is less than `from_date` and greater than `to_date`
        """
        parts = date_string.split('__')
        field_name = parts[0]

        if parts[1] == 'true':
            return self.filter(~Q(**{field_name: datetime.date.max}))

        if parts[1] == 'false':
            return self.filter(**{field_name: datetime.date.max})

        if not len(parts) > 2:
            raise BadSearchDateFormatException(
                "Value must be formatted {op}__{date} or "
                "between__{from_date}__{to_date}")

        op = parts[1]
        date = datetime.datetime.strptime(parts[2], '%Y-%m-%d')

        if op == "after":
            return self.filter(**{"{0}__gte".format(field_name): date})

        elif op == "exact":
            return self.filter(**{field_name: date})

        elif op == "before":
            return self.filter(**{"{0}__lte".format(field_name): date})

        elif op in ("between", "notbetween",):
            if not len(parts) == 4:
                raise BadSearchDateFormatException(
                    "Between dates operation requires two "
                    "double-underscore delimited dates")
            to_date = datetime.datetime.strptime(parts[3], '%Y-%m-%d')

            if op == "notbetween":
                return self.filter(
                    Q(**{"{0}__lte".format(field_name): date}) |
                    Q(**{"{0}__gte".format(field_name): to_date})
                )
            else:
                return self.filter(**{
                    "{0}__gte".format(field_name): date,
                    "{0}__lte".format(field_name): to_date
                })
        else:
            raise BadSearchDateFormatException(
                "{0} is not a supported operation".format(op))

    def filter_private_to_project_ids(
            self, project_ids=None, allow_public=True):
        """
            Filters private videos by the project they are private to.

            Also returns public videos by default
        """
        q = Q()
        if allow_public:
            q = Q(
                private_to_project_ids='___NONE___')

        if project_ids:  # thor falls over if an empty list is passed
            q = q | Q(private_to_project_ids=project_ids)

        return self.filter(q)

    def filter_youtube_id(self, youtube_id):
        """
            Filter by youtube ID
        """
        return self.filter(youtube_id=youtube_id)

    def multi_filter(self, filters):
        """
            Takes an object of filter arguments and applies the
            individual filters
        """

        # all filters should clone the query object
        video_search = self

        # filter on project
        if filters.project_id:
            video_search = video_search.filter_projects(filters.project_id)

        # filter on keywords
        if filters.q:
            video_search = video_search.keywords(filters.q)

        # geosearch
        if filters.location:
            video_search = video_search.geo_search(filters.location)

        # apply channel filter
        if filters.channel_ids:
            video_search = video_search.filter_channels(filters.channel_ids)

        # apply collection filter
        if getattr(filters, 'collection_id', None):
            video_search = video_search.filter_collections(
                filters.collection_id)

        # apply tags - negated and regular
        if filters.tag_ids:
            video_search = video_search.filter_tags(filters.tag_ids)

        # apply date filtering
        if filters.date:
            video_search = video_search.filter_date(filters.date)

        if getattr(filters, 'youtube_id', None):
            video_search = video_search.filter_youtube_id(filters.youtube_id)

        if getattr(filters, 'exclude_ids', None):
            ids = filters.exclude_ids.split(',')
            if ids:
                video_search = video_search.filter(~Q(id=ids))

        return video_search

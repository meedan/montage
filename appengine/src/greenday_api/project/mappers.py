"""
    Defines mappers to map response messages for the project API
"""
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum

# GREENDAY
from greenday_core.models import VideoCollection, ProjectUser

from ..mapper import GeneralMapper
from ..video.messages import CollectionResponseMessageSkinny

from .messages import (
    UserResponseMessage,
    ProjectUserResponseMessage,
    GenericProjectUpdateMessage,
    ProjectTagResponseMessageSlim,
)


class ProjectMapper(GeneralMapper):
    """
        Mapper class to map
        :class:`Project <greenday_core.models.project.Project>` entities
    """
    def __init__(self, *args, **kwargs):
        """
            Creates mapper
        """
        self.projectuser_mapper = GeneralMapper(
            ProjectUser, ProjectUserResponseMessage)
        self.projecttag_mapper = TagMapper(ProjectTagResponseMessageSlim)
        self.user_mapper = GeneralMapper(get_user_model(), UserResponseMessage)
        self.collection_mapper = GeneralMapper(
            VideoCollection, CollectionResponseMessageSkinny)
        super(ProjectMapper, self).__init__(*args, **kwargs)

    def get_message_field_value(
            self,
            obj,
            message_field_name,
            current_user=None):
        """
            Custom mapping behaviour
        """
        if message_field_name == "owner":
            return self.user_mapper.map(
                next(
                    (ru.user for ru in obj.projectusers.all() if ru.is_owner),
                    None))
        elif message_field_name == "admin_ids":
            return map(
                int, (ru.user_id for ru in obj.projectusers.all()
                      if ru.is_admin and ru.user_id)
            )
        elif message_field_name == "assigned_user_ids":
            return map(
                int, (ru.user_id for ru in obj.projectusers.all()
                      if ru.is_assigned and ru.user_id)
            )
        elif message_field_name == "collections":
            return map(self.collection_mapper.map, obj.collections.all())
        elif message_field_name == 'projecttags':
            return map(
                self.projecttag_mapper.map,
                obj.projecttags.all()
            )
        elif message_field_name == 'taginstance_count':
            # only return this if the tags have been prefetched
            if (hasattr(obj, "_prefetched_objects_cache") and
                    obj._prefetched_objects_cache.get('projecttags')):
                return sum(
                    getattr(pt, "taginstance_sum", 0)
                    for pt in obj.projecttags.all()
                )
        elif current_user and message_field_name == "current_user_info":
            if (hasattr(obj, "_prefetched_objects_cache") and
                    obj._prefetched_objects_cache.get('projectusers')):
                # if we prefetched the projectusers then get from the
                # prefetched queryset
                projectuser = next(
                    (o for o in obj.projectusers.all()
                        if o.user_id == current_user.id),
                    None
                )
            else:
                projectuser = obj.get_user_relation(current_user)

            if projectuser:
                return self.projectuser_mapper.map(projectuser)
        else:
            return super(ProjectMapper, self).get_message_field_value(
                obj, message_field_name)


class GenericProjectUpdateMapper(object):
    """
        Basic mapper to map an
        :class:`Event <greenday_core.models.event.Event>`
        object to a
        :class:`GenericProjectUpdateMessage <greenday_api.project.messages.GenericProjectUpdateMessage>`
    """
    def map(self, obj, event_obj):
        """
            Maps obj to event_obj
        """
        return GenericProjectUpdateMessage(
            id=obj.id,
            name=obj.name,
            timestamp=event_obj.timestamp
        )


# mapper for project collaborators
class ProjectCollaboratorMapper(GeneralMapper):
    """
        Project collaborators need a little more information
        and so this mapper allows us to traverse either the user
        or pending_user relationships to return extra data
    """
    def __init__(self, model, message_type):
        """
            Creates mapper
        """
        super(ProjectCollaboratorMapper, self).__init__(
            model, message_type)

    def get_message_field_value(self, obj, message_field_name):
        """
            Custom mapping behaviour
        """
        if message_field_name in (
                "first_name", "last_name", "email", "profile_img_url"):
            if obj.user:
                return getattr(obj.user, message_field_name, None)
            return getattr(obj.pending_user, message_field_name, None)
        return super(ProjectCollaboratorMapper, self).get_message_field_value(
            obj, message_field_name)


class TagMapper(GeneralMapper):
    """
        Maps a
        :class:`ProjectTag <greenday_core.models.tag.ProjectTag>`
        which is associated with a project
    """
    def __init__(self, message_type):
        """
            Creates the mapper
        """
        super(TagMapper, self).__init__(None, message_type)

    def get_message_field_value(
            self,
            obj,
            message_field_name):
        """
            Custom mapping behaviour
        """
        if message_field_name in ("id", "name",):
            return getattr(obj.global_tag, message_field_name)

        if message_field_name == "taginstance_count":
            if hasattr(obj, "taginstance_sum"):
                return long(obj.taginstance_sum)
            else:
                return (
                    obj.videotags
                    .annotate(taginstance_count=Count("tag_instances"))
                    .aggregate(Sum('taginstance_count'))
                )['taginstance_count__sum']

        return super(TagMapper, self).get_message_field_value(
            obj, message_field_name)

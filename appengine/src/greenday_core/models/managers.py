"""
    Defines Django ORM managers
"""
from operator import attrgetter
from itertools import groupby

from django.db.models import Q, Count, QuerySet, Prefetch, Manager, Sum

from treebeard.ns_tree import NS_NodeQuerySet

from ..utils import compose_new_type


class TrashableQuerySet(QuerySet):
    """
        Explicitly call delete() on each model
    """
    def delete(self, trash=True):
        if trash:
            for m in self:
                m.delete()
        else:
            super(TrashableQuerySet, self).delete()


class BaseNonTrashedManager(Manager):
    """
        Returns only objects which have not been trashed
    """
    def get_queryset(self):
        return super(BaseNonTrashedManager, self).get_queryset().filter(
            trashed_at__isnull=True)

NonTrashedManager = BaseNonTrashedManager.from_queryset(TrashableQuerySet)


class TrashedManager(Manager):
    """
        Returns only objects which have been trashed.
    """
    def get_queryset(self):
        return super(TrashedManager, self).get_queryset().filter(
            trashed_at__isnull=False)


class BaseNS_NodeManager(Manager):
    """
        Alternative implementation of NS_NodeManager so we can chain querysets
    """

    def get_queryset(self):
        qs = super(BaseNS_NodeManager, self).get_queryset()
        return qs.order_by('tree_id', 'lft')


NS_NodeManager = BaseNS_NodeManager.from_queryset(NS_NodeQuerySet)


class UnarchivedManager(Manager):
    """
        Manager to return unarchived objects
    """
    def get_queryset(self):
        return (
            super(UnarchivedManager, self)
            .get_queryset()
            .filter(archived_at__isnull=True)
        )


class ArchivedManager(Manager):
    """
        Manager to return unarchived objects
    """
    def get_queryset(self):
        try:
            return (
                super(ArchivedManager, self)
                .get_query_set()
                .filter(archived_at__isnull=False)
            )
        except AttributeError:
            return (
                super(ArchivedManager, self)
                .get_queryset()
                .filter(archived_at__isnull=False)
            )


# create a manager to chain NonTrashedManager and UnarchivedManager
NonTrashedUnarchivedManager = compose_new_type(
    "NonTrashedUnarchivedManager", UnarchivedManager, NonTrashedManager)

# create a manager to chain NonTrashedManager and ArchivedManager
NonTrashedArchivedManager = compose_new_type(
    "NonTrashedArchivedManager", ArchivedManager, NonTrashedManager)


class NSTreePrefillParentCacheMixin(object):
    def prefill_parent_cache(self):
        """
            Sets the cached parent on each node in the queryset *if* the
            parent is also in the queryset

            This method iterates the queryset
        """
        # this relies on the fact that NS tree orders querysets by tree_id
        for _, nodes in groupby(self, attrgetter('tree_id')):

            # reverse the nodes in this tree as we're looking for the closest
            # ancestors
            reversed_nodes = sorted(nodes, reverse=True, key=attrgetter('lft'))
            for node in reversed_nodes:
                if node.is_root():
                    continue

                # get the first ancestor of the node
                parent = next((
                    n for n in reversed_nodes
                    if n.lft < node.lft and n.rgt > node.rgt
                ), None)

                if parent:
                    # patch the parent node onto the node object
                    node._cached_parent_obj = parent

        return self


class ProjectQuerySet(QuerySet):
    """
        Queryset to add querying methods for `Project` entities
    """
    def with_videos(self):
        """ Add a count of the project's videos to each project result """
        return self.extra(select={
            'video_count': """
                SELECT COUNT(*) FROM greenday_core_video
                WHERE greenday_core_video.project_id =
                greenday_core_project.id AND
                greenday_core_video.trashed_at is null AND
                greenday_core_video.archived_at is null
            """
        })

    def get_projects_for(self, user):
        """ Gets all projects that the given user has a role on """
        return self.filter(
            Q(projectusers__user=user) &  # set up join
            (
                # filter on join
                Q(projectusers__is_owner=True) |
                Q(projectusers__is_admin=True) |
                Q(projectusers__is_assigned=True)
            )
        )

    def prefetch_projecttags(self):
        """
            Prefetch all projecttags along with their taginstance counts
        """
        from .tag import ProjectTag

        return self.prefetch_related(
            Prefetch(
                "projecttags",
                queryset=(
                    ProjectTag.objects
                    .select_related("global_tag")
                    .with_taginstance_sum()
                )
            )
        )

    def with_total_video_duration(self):
        """
            Adds `total_video_duration` to results
        """
        return self.annotate(total_video_duration=Sum("videos__youtube_video__duration"))

ProjectManager = NonTrashedManager.from_queryset(ProjectQuerySet)


class VideoQuerySet(QuerySet):
    """
        Queryset to add querying methods for `Video` entities
    """
    def with_tag_count_real(self):
        """ Add a count of video tags to each video result """
        return self.extra(select={
            'video_tag_count_real': """
                SELECT COUNT(*) FROM greenday_core_videotag
                WHERE greenday_core_videotag.video_id =
                greenday_core_video.id
            """
        })

    def with_tag_instance_count_real(self):
        """ Add a count of video tags to each video result """
        return self.annotate(
            video_tag_instance_count_real=Count("videotags__tag_instances"))

    def with_watch_count_real(self):
        """
            Add a count of watches to each video return
            Property is named 'watch_count_real' so it doesn't clash with
            'watch_count' which is the denormalised version of this count
        """
        return self.extra(select={
            'watch_count_real': """
                SELECT COUNT(*) FROM greenday_core_uservideodetail
                WHERE greenday_core_uservideodetail.video_id =
                greenday_core_video.id AND
                greenday_core_uservideodetail.watched=true
            """
        })

    def with_duplicate_count_real(self):
        """ Add a count of duplicates """
        return self.extra(select={
            'duplicate_count_real': """
                SELECT COUNT(*) FROM greenday_core_duplicatevideomarker
                WHERE greenday_core_duplicatevideomarker.video_1_id =
                greenday_core_video.id OR
               greenday_core_duplicatevideomarker.video_2_id =
               greenday_core_video.id
            """
        })

VideoManager = NonTrashedUnarchivedManager.from_queryset(VideoQuerySet)
ArchivedVideoManager = NonTrashedArchivedManager.from_queryset(VideoQuerySet)
VideoNonTrashedManager = NonTrashedManager.from_queryset(VideoQuerySet)


class ProjectTagQuerySet(NSTreePrefillParentCacheMixin, NS_NodeQuerySet):
    """
        Queryset to add querying methods for `ProjectTag` entities
    """
    def with_taginstance_sum(self):
        """
            Adds `taginstance_sum` to result objects
        """
        return self.extra(select={
            "taginstance_sum": """
                SELECT COUNT(*) FROM greenday_core_videotaginstance i
                INNER JOIN greenday_core_videotag v ON i.video_tag_id = v.id
                WHERE v.project_tag_id = greenday_core_projecttag.id
            """
        })

ProjectTagManager = BaseNS_NodeManager.from_queryset(ProjectTagQuerySet)

ProjectCommentManager = BaseNS_NodeManager.from_queryset(compose_new_type(
    "ProjectCommentQuerySet", NS_NodeQuerySet, NSTreePrefillParentCacheMixin))
TimedVideoCommentManager = BaseNS_NodeManager.from_queryset(compose_new_type(
    "TimedVideoCommentQuerySet", NS_NodeQuerySet, NSTreePrefillParentCacheMixin))

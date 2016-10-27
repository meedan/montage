"""
    Defines models related to commenting functionality
"""
from collections import defaultdict
from operator import attrgetter

from django.db import models

from treebeard.ns_tree import NS_Node

from .managers import ProjectCommentManager, TimedVideoCommentManager
from .project import Project
from .tag import TagInstance
from .video import Video


class Comment(models.Model):
    """
        Abstract base class for a comment
    """
    class Meta:
        abstract = True

    text = models.TextField()

    @classmethod
    def get_root_comments_for(
            cls,
            object_id,
            prefetch_replies=False,
            reverse_order=False,
            qs_fn=lambda qs: qs):
        """ Gets all root comments for a given object """
        if isinstance(object_id, cls.tagged_object_type):
            object_id = object_id.pk

        order_key = '{0}created'.format('-' if reverse_order else '')

        if prefetch_replies:
            root_comments = {}
            root_comment_replies = defaultdict(list)

            for comment in qs_fn(
                    cls.get_tree()
                    .filter(tagged_object_id=object_id)
                    .select_related('user')):
                if comment.is_root():
                    root_comments[comment.tree_id] = comment
                else:
                    root_comment_replies[comment.tree_id].append(comment)

            for tree_id, comment in root_comments.items():
                comment._reply_cache = sorted(
                    root_comment_replies.get(tree_id, ()),
                    key=attrgetter('created'))

            return sorted(
                root_comments.values(),
                key=attrgetter('created'),
                reverse=reverse_order)
        else:
            return qs_fn(
                cls.get_root_nodes()
                .filter(tagged_object_id=object_id)
                .select_related('user')
                .order_by(order_key)
            )

    def get_replies(self, reverse_order=False, qs_fn=lambda qs: qs):
        """ Gets all replies to the given root comment """
        assert self.is_root(), "May only get replies to root comments"

        if hasattr(self, '_reply_cache'):
            return sorted(
                self._reply_cache,
                key=attrgetter('created'),
                reverse=reverse_order)

        order_key = '{0}created'.format('-' if reverse_order else '')

        self._reply_cache = list(qs_fn(
            self.get_children()
            .select_related('user')
            .order_by(order_key)
        ))

        return self._reply_cache

    def add_reply(self, text, user, **kwargs):
        """ Adds a reply to the given root comment """
        assert self.is_root(), "Must only add replies to the root comment"

        reply = self.add_child(
            text=text,
            user=user,
            tagged_object_id=self.tagged_object_id,
            **kwargs)

        if hasattr(self, '_reply_cache'):
            del self._reply_cache

        return reply


class TimedVideoComment(NS_Node, TagInstance, Comment):
    """
        Represents a comment on a video
    """
    tagged_object_type = Video

    start_seconds = models.FloatField()
    project = models.ForeignKey(Project)

    objects = TimedVideoCommentManager()

    def __unicode__(self):
        return u"{0} \"{1}\" on video ID {2}".format(
            "Comment" if self.is_root() else "Reply",
            self.text, self.video_id)

    def add_reply(self, text, user):
        """ Adds a reply to the given root comment """
        return super(TimedVideoComment, self).add_reply(
            text, user, start_seconds=self.start_seconds, project=self.project)

    @classmethod
    def get_root_comments_for(
            cls,
            object_id,
            prefetch_replies=False,
            reverse_order=False,
            qs_fn=None):
        """
            Override to prefetch and prefill queryset data
        """
        return super(TimedVideoComment, cls).get_root_comments_for(
            object_id,
            prefetch_replies=prefetch_replies,
            reverse_order=reverse_order,
            qs_fn=qs_fn or (lambda qs:
                qs.prefetch_related("tagged_content_object").prefill_parent_cache()
            )
        )

    def get_replies(self, reverse_order=False, qs_fn=lambda qs: qs):
        """
            Override to patch the parent comment (this comment)
            onto each reply
        """
        def _comment_qs_fn(qs):
            """ Patches the parent node onto each reply """
            for obj in qs_fn(qs.prefetch_related('tagged_content_object')):
                obj._cached_parent_obj = self
                yield obj

        return super(TimedVideoComment, self).get_replies(
            reverse_order=reverse_order,
            qs_fn=_comment_qs_fn)

    def save(self, *args, **kwargs):
        """
            Override save() to denormalise project_id
        """
        if not self.project_id:
            self.project_id = self.video.project_id
        super(TimedVideoComment, self).save(*args, **kwargs)


class ProjectComment(NS_Node, TagInstance, Comment):
    """
        Represents a comment on a project
    """
    tagged_object_type = Project

    objects = ProjectCommentManager()

    def __unicode__(self):
        return u"{0} \"{1}\" on project ID {2}".format(
            "Comment" if self.is_root() else "Reply",
            self.text, self.project_id)

    @classmethod
    def get_root_comments_for(
            cls,
            object_id,
            prefetch_replies=False,
            reverse_order=False,
            qs_fn=None):
        """
            Override to prefill queryset data
        """
        return super(ProjectComment, cls).get_root_comments_for(
            object_id,
            prefetch_replies=prefetch_replies,
            reverse_order=reverse_order,
            qs_fn=qs_fn or (lambda qs: qs.prefill_parent_cache())
        )

    def get_replies(self, reverse_order=False, qs_fn=lambda qs: qs):
        """
            Override to patch the parent comment (this comment)
            onto each reply
        """
        def _comment_qs_fn(qs):
            """ Patches the parent node onto each reply """
            for obj in qs_fn(qs):
                obj._cached_parent_obj = self
                yield obj

        return super(ProjectComment, self).get_replies(
            reverse_order=reverse_order,
            qs_fn=_comment_qs_fn)

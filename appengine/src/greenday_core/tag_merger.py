"""
    Defines TagMerger
"""
import itertools
import logging

from django.db import transaction
from django.db.models import Prefetch

from .models import GlobalTag, ProjectTag, VideoTag


class TagMerger(object):
    """
        Handles the merging of tags

        Object designed to be disposed of once the merge is complete
    """
    def __init__(self, merging_from_tag, master_tag):
        """
            Creates merger object
        """
        assert (
            isinstance(merging_from_tag, GlobalTag) and
            isinstance(master_tag, GlobalTag))

        self.merging_from_tag = merging_from_tag
        self.master_tag = master_tag

        self._merge_run = False

    @transaction.atomic
    def do_merge(self):
        """
            Merges the tags
        """
        assert not self._merge_run, "Cannot merge again"

        try:
            for project_id, project_tags in itertools.groupby(
                    list(
                        ProjectTag.objects
                        .filter(
                            global_tag_id__in=(
                                self.merging_from_tag.pk, self.master_tag.pk,))
                        .prefetch_related(
                            Prefetch(
                                'videotags',
                                queryset=VideoTag.objects
                                .select_related('video')
                            ))
                        .order_by('project_id')),
                    key=lambda o: o.project_id):

                project_tags_mapped = {
                    pt.global_tag_id: pt for pt in project_tags}

                self.merge_tags_for_project(
                    project_tags_mapped.get(self.merging_from_tag.pk),
                    project_tags_mapped.get(self.master_tag.pk))

            self.merging_from_tag.delete()

        finally:
            self._merge_run = True

    def merge_tags_for_project(
            self, merge_from_project_tag, master_project_tag):
        """
            Merges the given tags in the context of a
            single project
        """

        if not merge_from_project_tag:
            # this project doesn't have the merging tag - nothing to do here
            return

        if not master_project_tag:
            # this project doesn't have the master tag - repurpose the old tag
            merge_from_project_tag.global_tag = self.master_tag
            merge_from_project_tag.save()
            return

        video_ids_with_master_tag = {
            vt.video_id: vt for vt in master_project_tag.videotags.all()
        }

        for video_tag in (
            merge_from_project_tag.videotags.all()
                ):

            if video_tag.video_id in video_ids_with_master_tag:
                master_video_tag = video_ids_with_master_tag[
                    video_tag.video_id]
                self.merge_tag_instances(video_tag, master_video_tag)

                video_tag.delete()

                logging.info(
                    u"Video {0} has had its {1} tag removed".format(
                        video_tag.video.youtube_video.name,
                        self.merging_from_tag.name))
            else:
                video_tag.project_tag = master_project_tag
                video_tag.save()

                logging.info(
                    u"Video {0} has had its {1} tags changed to {2}"
                    .format(
                        video_tag.video.youtube_video.name,
                        self.merging_from_tag.name,
                        self.master_tag.name)
                )

        merge_from_project_tag.delete()

    def merge_tag_instances(self, video_tag, master_video_tag):
        """
            Merges tag instances from a video_tag to another video_tag
        """
        assert video_tag.video_id == master_video_tag.video_id, "Both video tags must have an FK to the same video"

        for tag_instance in video_tag.tag_instances.all():
            if not tag_instance.has_times:
                continue

            master_tag_instances = list(master_video_tag.tag_instances.all())
            merge_into = self.tag_instance_intersects_with(
                tag_instance, master_tag_instances)

            if merge_into:
                merge_from = tag_instance
                while merge_from:
                    merge_into = self.merge_tag_instance(
                        merge_from, merge_into)

                    logging.info(
                        u"Merged tag instance {0} into {1}"
                        .format(merge_from, merge_into))

                    merge_into.save()
                    merge_from.delete()

                    # the merge_into tag will cover a greater duration and may
                    # intersect with other tags
                    merge_from = self.tag_instance_intersects_with(
                        merge_into, master_tag_instances)

                    if merge_from:
                        master_tag_instances.remove(merge_from)

            else:
                tag_instance.video_tag = master_video_tag
                tag_instance.save()

            logging.info(
                u"Moved tag instance {0} from video tag {1} to {2}"
                .format(
                    tag_instance,
                    tag_instance.video_tag_id,
                    master_video_tag.pk))

    def tag_instance_intersects_with(self, tag_instance, list_of_instances):
        """
            Checks if the instances intersects with another tag and returns the
            intersecting tag if so
        """
        return next(
            (
                mi for mi in list_of_instances if
                tag_instance.pk != mi.pk and
                mi.end_seconds > tag_instance.start_seconds and
                mi.start_seconds < tag_instance.end_seconds
            ), None
        )

    def merge_tag_instance(self, from_tag_instance, to_tag_instance):
        """
            Extends to_tag_instance with the start/end of from_tag_instance
        """
        to_tag_instance.start_seconds = min(
            to_tag_instance.start_seconds, from_tag_instance.start_seconds)
        to_tag_instance.end_seconds = max(
            to_tag_instance.end_seconds, from_tag_instance.end_seconds)

        return to_tag_instance

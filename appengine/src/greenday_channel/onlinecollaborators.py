"""
    Defines the online collaborators manager
"""
import datetime

from google.appengine.api import memcache

from greenday_core.constants import EventKind
from greenday_core.eventbus import publish_appevent

from .utils import retry_until_truthy


class OnlineCollaboratorsManager(object):
    """
        Tracks the online/offline state of collaborators working on
        projects (could be any object though)

        Fires off system events to the eventbus to indicate online/offline users
    """
    def __init__(
            self,
            object_id,
            prefix="project",
            namespace="collab",
            collaborator_expiry=90,
            online_event_kind=EventKind.PROJECTCOLLABORATORONLINE,
            offline_event_kind=EventKind.PROJECTCOLLABORATOROFFLINE
            ):
        """
            Creates an online collaborators manager

            object_id: the object on which users are collaborating
        """
        self.object_id = object_id
        self.prefix = prefix
        self.namespace = namespace
        self.client = memcache.Client()
        self.collaborator_expiry = datetime.timedelta(
            seconds=collaborator_expiry)
        self.online_event_kind = online_event_kind
        self.offline_event_kind = offline_event_kind

    @property
    def key(self):
        return "{0}-{1}".format(self.prefix, self.object_id)

    @classmethod
    def user_to_dict(cls, user):
        return {
            'id': user.pk,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'profile_img_url': user.profile_img_url,
            'google_plus_profile': user.google_plus_profile,
            'timestamp': datetime.datetime.utcnow()
        }

    def filter_expired_collaborators(self, collaborators):
        now = datetime.datetime.utcnow()
        for k, v in collaborators.items():
            if (now - v['timestamp']) > self.collaborator_expiry:
                publish_appevent(
                    self.offline_event_kind,
                    object_id=collaborators[k]['id'],
                    project_id=self.object_id,
                    meta=collaborators[k]['id'],
                    user_id=collaborators[k]['id'])

                del collaborators[k]

        return collaborators

    def add_collaborator(self, user, token):
        """
            Adds a user to the list of collaborators online for the given object

            Users linked to the passed token so that they can be later removed
            using just the token
        """
        user_dict = self.user_to_dict(user)

        def _add_collaborator():
            collaborators = self.get_collaborators()

            # prevent duplicate collaborator entries if a user has multiple windows open
            for k, v in collaborators.items():
                if v['id'] == user.pk:
                    del collaborators[k]

            collaborators[token] = user_dict

            ret = self.client.cas(
                self.key,
                collaborators,
                namespace=self.namespace
            )

            if ret:
                publish_appevent(
                    self.online_event_kind,
                    object_id=user.pk,
                    project_id=self.object_id,
                    meta=user.pk,
                    user=user)
            return ret

        return retry_until_truthy(_add_collaborator)

    def remove_collaborator(self, token):
        """
            Removes a user from the list of collaborators online for the given
            object
        """
        def _remove_collaborator():
            collaborators = self.get_collaborators()

            if token in collaborators:
                user_id = collaborators[token]['id']
                del collaborators[token]

                ret = self.client.cas(
                    self.key,
                    collaborators,
                    namespace=self.namespace
                )

                if ret:
                    publish_appevent(
                        self.offline_event_kind,
                        object_id=user_id,
                        project_id=self.object_id,
                        meta=user_id,
                        user_id=user_id)

                return ret

        return retry_until_truthy(_remove_collaborator)

    def get_collaborators(self, filter_expired=True):
        """
            Gets a list of users online
        """
        collaborators = self.client.gets(
            self.key, namespace=self.namespace)

        if collaborators is None:
            self.client.set(self.key, {}, namespace=self.namespace)
            collaborators = {}

        if filter_expired:
            filtered_collaborators = self.filter_expired_collaborators(collaborators)

            if len(filtered_collaborators) != len(collaborators):
                self.client.set(self.key, filtered_collaborators, namespace=self.namespace)

            collaborators = filtered_collaborators

        return collaborators

    def refresh_collaborator(self, token):
        """
            Refreshes a user on a given project so that the cache doesn't expire

            If the collaborator doesn't exist then nothing happens
        """
        def _refresh_collaborator():
            collaborators = self.get_collaborators(filter_expired=False)

            if token in collaborators:
                collaborators[token]['timestamp'] = datetime.datetime.utcnow()

                return self.client.cas(
                    self.key,
                    collaborators,
                    namespace=self.namespace
                )
            else:
                return True

        return retry_until_truthy(_refresh_collaborator)

    def purge_expired_collaborators(self):
        collaborators = self.get_collaborators(filter_expired=True)
        self.client.cas(
            self.key,
            collaborators,
            namespace=self.namespace
        )


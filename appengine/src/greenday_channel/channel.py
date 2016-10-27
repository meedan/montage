"""
    Defines the channel manager
"""
import time
import uuid

from google.appengine.api import memcache

from .utils import retry_until_truthy


class GreendayChannelManager(object):
    """
        A manager to encapsulate a memcache-based messaging queue
    """
    def __init__(
            self,
            client_namespace="channel-clients",
            message_namespace="channel-buckets",
            channels=None,
            max_message_backlog=200,
            pull_retries=37,
            pull_sleep=1.5,
            default_cas_ttl=60*30):
        """
            Creates a channel manager
        """
        assert channels
        self.client_namespace = client_namespace
        self.message_namespace = message_namespace
        self.client = memcache.Client()
        self.default_cas_ttl = default_cas_ttl
        self.max_message_backlog = max_message_backlog
        self.channels = channels
        self.pull_retries = pull_retries
        self.pull_sleep = pull_sleep

    def publish_message(self, message):
        """
            Publishes a message to all subscribed clients in the client group
        """
        def _publish_message(token):
            messages = self.client.gets(token, namespace=self.message_namespace)

            if messages is None:
                self.client.set(token, [], namespace=self.message_namespace)
                return False
            else:
                messages.append(
                    {'message': message,
                    'time': time.time()
                    })

            if self.client.cas(
                    token,
                    messages,
                    time=self.default_cas_ttl,
                    namespace=self.message_namespace):
                if len(messages) > self.max_message_backlog:
                    self.remove_client(token)
                return True

        # fan out
        for channel in self.channels:
            for token in self.get_client_tokens(channel):
                retry_until_truthy(_publish_message, args=(token,))

    def pop_messages(self, token):
        """
            Pops all messages for a given client
        """
        def _pop_messages():
            messages = self.client.gets(token, namespace=self.message_namespace)
            if messages is None:
                self.client.set(token, [], namespace=self.message_namespace)
                return False
            if self.client.cas(token, [], namespace=self.message_namespace):
                return messages

        return retry_until_truthy(
            _pop_messages,
            max_retries=self.pull_retries,
            sleep=self.pull_sleep)

    def add_client(self, token):
        """
            Adds a client to be subscribed

            token: uuid to identify the app client
        """
        def _add_client(channel):

            tokens = self.get_client_tokens(channel)

            if token not in tokens:
                tokens.append(token)

                return self.client.cas(
                        channel,
                        tokens,
                        time=self.default_cas_ttl,
                        namespace=self.client_namespace)
            else:
                return True

        done = 0
        for channel in self.channels:
            if retry_until_truthy(_add_client, args=(channel,)):
                done += 1

        return done == len(self.channels)


    def get_client_tokens(self, channel):
        """
            Gets all clients currently subscribed
        """
        tokens = self.client.gets(channel, namespace=self.client_namespace)

        if tokens is None:
            self.client.set(channel, [], namespace=self.client_namespace)
            tokens = []

        return tokens

    def remove_client(self, token):
        """
            Removes a given subscribed client
        """
        def _remove_client(channel):
            tokens = self.get_client_tokens(channel)

            if token in tokens:
                tokens.remove(token)
                return self.client.cas(
                    channel,
                    tokens,
                    time=self.default_cas_ttl,
                    namespace=self.client_namespace)
            else:
                return True

        for channel in self.channels:
            return retry_until_truthy(_remove_client, args=(channel,))

    @classmethod
    def create_client_token(cls):
        """
            Returns a new uuid
        """
        return unicode(uuid.uuid4())

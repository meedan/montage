"""
    Context managers to affect the dispatch of Django's signals
"""
import weakref

from django.db.models.signals import (
    pre_save,
    pre_init,
    pre_delete,
    post_save,
    post_delete,
    post_init,
    post_syncdb)
from django.dispatch.dispatcher import _make_id


ALL_SIGNALS = [
    # Django
    pre_save,
    pre_init,
    pre_delete,
    post_save,
    post_delete,
    post_init,
    post_syncdb,
]


class InhibitSignals(object):
    """
        Context manager to stop signals being fired
    """
    def __init__(self, senders, signal_list=None, ignore_receivers=None):
        """
        Inhibits Django's signals from being fired for the given senders.

        with inhibit_signals(
                [None, obj.__class__],
                ignore_receivers=[receiver_to_keep_connected]):
            obj.save() # only receiver_to_keep_connected() should be called
        """
        try:
            iter(senders)
        except TypeError:
            senders = [senders]

        self.senders = {_make_id(sender): sender for sender in senders}

        self.ignore_receivers_keys = map(_make_id, ignore_receivers or [])

        signals = signal_list if signal_list is not None else ALL_SIGNALS
        self.signal_map = {
            signal: self.get_signal_receivers(signal)
            for signal in signals
        }

    def __enter__(self):
        self.disconnect_signals()

    def __exit__(self, *args):
        self.reconnect_signals()

    def get_signal_receivers(self, signal):
        """ Gets every receiver listening to the signal """
        receivers = []
        for receiver in signal.receivers:
            if not receiver[0][0] in self.ignore_receivers_keys:
                for sender_id in self.senders:
                    if receiver[0][1] == sender_id:
                        receivers.append((sender_id, receiver))
        return receivers

    def disconnect_signals(self):
        """
            Disconnect signals to prevent them from firing
        """
        for signal, receivers in self.signal_map.items():
            for sender_id, receiver in receivers:
                signal.disconnect(
                    sender=self.senders[sender_id],
                    dispatch_uid=receiver[0][0])

    def reconnect_signals(self):
        """
            Reconnect the signals
        """
        for signal, receivers in self.signal_map.items():
            for sender_id, receiver in receivers:
                lookup_key, receiver_method = receiver
                if isinstance(receiver_method, weakref.ReferenceType):
                    receiver_method = receiver_method()

                signal.connect(
                    receiver_method,
                    sender=self.senders[sender_id],
                    dispatch_uid=lookup_key[0])

inhibit_signals = InhibitSignals


class WithSignal(object):
    """
        Context manager to connect a Django signal
    """
    def __init__(
            self, signal, receiver, sender=None, weak=True, dispatch_uid=None):
        """
        Wires up a Django signal for the context

        with with_signal(
                signal,
                handler,
                sender=MyModel,
                weak=True,
                dispatch_uid="save"):
            # receiver will be connected here

        # receiver disconnected here
        """
        self.signal = signal
        self.receiver = receiver
        self.sender = sender
        self.weak = weak
        self.dispatch_uid = dispatch_uid

    def __enter__(self):
        self.signal.connect(
            self.receiver,
            sender=self.sender,
            weak=self.weak,
            dispatch_uid=self.dispatch_uid
        )

    def __exit__(self, *args):
        self.signal.disconnect(
            receiver=self.receiver,
            sender=self.sender,
            weak=self.weak,
            dispatch_uid=self.dispatch_uid)

with_signal = WithSignal

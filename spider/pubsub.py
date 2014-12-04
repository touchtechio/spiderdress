"""pubsub

Use this module for simple publish-subscribe functionality.

Example:
    import pubsub as pub

    def listener(arg1, arg2):
        print arg1, arg2

    pub.subscribe(listener, "topic")

    pub.send_message("topic", arg1=1, arg2="arg2")

"""

from multiprocessing import Process, Queue

_topics = dict()

def subscribe(listener, topic):
    """Subscribes to a topic, allowing the listener to receive any published
    messages.

    Args:
        listener(func): The function to handle messages.
        topic(str): The topic to subscribe to.

    """
    if topic not in _topics:
        _topics[topic] = Topic()

    _topics[topic].add_subscriber(listener)

def unsubscribe(listener, topic):
    """Unsubscribes a listener from a topic.

    Args:
        listener(func): The function to unsubscribe.
        topic(str): The topic to unsubscribe the function from.

    """
    if topic not in _topics:
        print "Topic does not exist."
        return

    _topics[topic].remove_subscriber(listener)

def send_message(topic, **kwargs):
    """Sends a message to all listeners of the topic.

    Args:
        topic(str): The topic to send the message to.
        **kwargs: Message in the form of arbitrary keyword arguments.

    """
    if topic not in _topics:
        print "Topic does not exist."
        return

    _topics[topic].add_message(kwargs)

class Topic(object):
    """Holds a list of subscribers and message queue for a topic.

    """

    def __init__(self):
        self._listeners = []
        self._message_queue = Queue()

    def add_subscriber(self, listener):
        """Add a new subscriber to the topic.

        Args:
            listener(func): The function to subscribe.

        """
        self._listeners.append(listener)

    def remove_subscriber(self, listener):
        """Remove a subscriber from the topic.

        Args:
            listener(func): The function to remove.

        """
        self._listeners.remove(listener)

    def add_message(self, kwargs):
        """Add message to all subscribers of topic.

        Args:
            **kwargs: Message as argument list.

        """
        self._message_queue.put(kwargs)
        Process(target=self._send_messages).start()

    def _send_messages(self):
        """Main loop to send messages in queue."""
        kwargs = self._message_queue.get()

        for listener in self._listeners:
            listener(**kwargs)

if __name__ == '__main__':
    print "Using pubsub."

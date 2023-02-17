#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""twitter.py - A listener for handling streaming Twitter data.

See README.md or https://github.com/nicholasadamou/stockmine
for more information.

Copyright (C) Nicholas Adamou 2019
stockmine is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""

from json import loads
from queue import Empty
from queue import Queue
from threading import Event
from threading import Thread

from tweepy import StreamListener

from logs import *

# The number of worker threads processing tweets.
NUM_THREADS = 1

# The maximum time in seconds that workers wait for a new task on the queue.
QUEUE_TIMEOUT_S = 5 * 60

# The number of retries to attempt when an error occurs.
API_RETRY_COUNT = 60

# The number of seconds to wait between retries.
API_RETRY_DELAY_S = 1

# The HTTP status codes for which to retry.
API_RETRY_ERRORS = [400, 401, 500, 502, 503, 504]


class TwitterListener(StreamListener):
    """A listener class for handling streaming Twitter data."""

    def __init__(self, callback):
        super().__init__()

        self.callback = callback
        self.error_status = None
        self.start_queue()

    def start_queue(self):
        """Creates a queue and starts the worker threads."""

        self.queue = Queue()
        self.stop_event = Event()
        print(f"{OK} Starting {NUM_THREADS} worker threads.")
        self.workers = []
        for worker_id in range(NUM_THREADS):
            worker = Thread(target=self.process_queue, args=[worker_id])
            worker.daemon = True
            worker.start()
            self.workers.append(worker)

    def stop_queue(self):
        """Shuts down the queue and worker threads."""

        # First stop the queue.
        if self.queue:
            print(f"{WARNING} Stopping queue.")
            self.queue.join()
        else:
            print(f"{WARNING} No queue to stop.")

        # Then stop the worker threads.
        if self.workers:
            print("%s Stopping %d worker threads." % (WARNING, len(self.workers)))
            self.stop_event.set()
            for worker in self.workers:
                # Block until the thread terminates.
                worker.join()
        else:
            print(f"{WARNING} No worker threads to stop.")

    def process_queue(self, worker_id):
        """Continuously processes tasks on the queue."""

        print(f"{OK} Started worker thread: {worker_id}")
        while not self.stop_event.is_set():
            try:
                data = self.queue.get(block=True, timeout=QUEUE_TIMEOUT_S)
                self.handle_data(data)
                self.queue.task_done()
            except Empty:
                print(f"{WARNING} Worker {worker_id} timed out on an empty queue.")
                continue

        print(f"{WARNING} Stopped worker thread: {worker_id}")

    def on_error(self, status):
        """Handles any API errors."""

        print(f"{ERROR} Twitter error: {status}")
        self.error_status = status
        self.stop_queue()
        return False

    def get_error_status(self):
        """Returns the API error status, if there was one."""

        return self.error_status

    def on_data(self, data):
        """Puts a task to process the new data on the queue."""

        # Stop streaming if requested.
        if self.stop_event.is_set():
            return False

        # Put the task on the queue and keep streaming.
        self.queue.put(data)
        return True

    def handle_data(self, data):
        """Sanity-checks and extracts the data before sending it to the
        callback.
        """

        try:
            tweet = loads(data)
        except ValueError:
            print(f"{ERROR} Failed to decode JSON data: {data}")
            return

        print(f"{OK} Examining tweet: {tweet}")

        # Call the callback.
        self.callback(tweet)

import threading
from abc import ABC, abstractmethod

from swarmai.utils.task_queue.Task import Task

def synchronized_queue(method):
    timeout_sec = 30
    def wrapper(self, *args, **kwargs):
        with self.lock:
            self.lock.acquire(timeout = timeout_sec)
            try:
                return method(self, *args, **kwargs)
            except Exception as e:
                print(f"Failed to execute {method.__name__}: {e}")
            finally:
                self.lock.release()
    return wrapper


class TaskQueueBase(ABC):
    """Abstract class for the Task Queue object.
    We can have different implementation of the task queues: from simple queue, to the custom priority queue.
    Not every implementatino is inherently thread safe, so we also put the locks here.

    Made a pull queue, just for the ease of implementation.
    """
    def __init__(self):
        self.lock = threading.Lock()

        # make sure that all the methods are subject to the decorator
        for name in dir(self):
            attr = getattr(self, name)
            if callable(attr):
                setattr(self, name, synchronized_queue(attr))

    @abstractmethod
    def add_task(self, taks: Task) -> bool:
        """Adds a task to the queue.
        """
        raise NotImplementedError

    @abstractmethod
    def get_task(self) -> Task:
        """Gets the next task from the queue.
        """
        raise NotImplementedError


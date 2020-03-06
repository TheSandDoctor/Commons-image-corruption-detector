import argparse

from worker_base import WorkerBase
from EDirections import EDirections
from redis import Redis
from datetime import datetime
from config import REDIS_KEY
import multiprocessing as mp

redis = None
MAX_WORKERS = 50

class RCWorker(WorkerBase):
    def __init__(self, direction):
        super().__init__(direction)


def calc_range():
    # Goal here is to have different levels for the # of processes
    global redis
    if redis.llen(REDIS_KEY) > 150000:
        return 50
    elif redis.llen(REDIS_KEY) > 50000:
        return 40
    elif redis.llen(REDIS_KEY) > 5000:
        return 25
    elif redis.llen(REDIS_KEY) > 500:
        return 15
    else:
        return 10


if __name__ == '__main__':
    processes = []
    try:
        redis = Redis(host="localhost")
        parser = argparse.ArgumentParser()
        parser.add_argument('--r', "--right", help="Check from the right", action="store_true")
        args = parser.parse_args()
        if args.r:
            scan = RCWorker(EDirections.RIGHT)
        else:
            scan = RCWorker(EDirections.LEFT)

        for i in range(0, 10):
            p = mp.Process(target=scan.run(), args=(i,))
            processes.append(p)
            p.start()
            # scan.run()  # Do the work
    except KeyboardInterrupt:
        for i in processes:
            i.terminate()

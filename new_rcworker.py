import argparse

from worker_base import WorkerBase
from EDirections import EDirections


class RCWorker(WorkerBase):
    def __init__(self, direction):
        super().__init__(direction)


if __name__ == '__main__':
    try:
        skip = True
        parser = argparse.ArgumentParser()
        parser.add_argument('--r', "--right", help="Check from the right", action="store_true")
        args = parser.parse_args()
        try:
            if args.right:
                skip = False
        except AttributeError:
            pass
        if args.right:
            scan = RCWorker(EDirections.RIGHT)
        else:
            scan = RCWorker(EDirections.LEFT)
        scan.run()  # Do the work
    except KeyboardInterrupt:
        pass

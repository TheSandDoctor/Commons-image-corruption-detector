from __future__ import absolute_import

from base_scan import BaseCorruptScan
import argparse


class FullScanReversed(BaseCorruptScan):
    pass


if __name__ == '__main__':
    try:
        skip = True
        parser = argparse.ArgumentParser()
        parser.add_argument('--fs', "--full_scan", help="whether to skip rechecks", action="store_true")
        args = parser.parse_args()
        try:
            if args.full_scan:
                skip = False
        except AttributeError:
            pass
        scan = FullScanReversed('corruptBackwards', True, skip)
        scan.process_file() # Do the work
    except KeyboardInterrupt:
        pass

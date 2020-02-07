# -*- coding: UTF-8 -*-
import pywikibot

class ImageObj:

    def __init__(self, change):
        """

        :param change: json object
        """
        self.title = str(change['title'])
        self.log_timestamp = change['log_params']['img_timestamp']
        self.gen_timestamp = change['timestamp']
        self.hash = str(change['log_params']['img_sha1'])
        self.isCorrupt = False

    def getRevision(self, file_page):
        """

        :param file_page: pywikibot file page object
        :return: returns pywikibot revision
        """
        try:
            revision = file_page.get_file_history()[pywikibot.Timestamp.fromtimestampformat(self.log_timestamp)]
        except KeyError:
            try:
                # From rcbacklog
                revision = file_page.get_file_history()[pywikibot.Timestamp.fromISOformat(self.log_timestamp)]
            except KeyError:
                try:
                    revision = file_page.get_file_history()[pywikibot.Timestamp.fromtimestamp(self.gen_timestamp)]
                except KeyError:
                    revision = file_page.latest_file_info
                    pywikibot.warning(
                        'Cannot fetch specified revision, falling back to '
                        'latest revision.')
        return revision

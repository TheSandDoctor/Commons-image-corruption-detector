# -*- coding: UTF-8 -*-
import requests


def getImageInfo(title, url='https://commons.wikimedia.org/w/api.php'):
    """
    Get image info from a given title using a given API URL.
    Adapted/adopted from: https://www.mediawiki.org/w/index.php?title=API:Imageinfo&oldid=3433526#Sample_code
    :param title: title of page to get imageinfo from
    :param url: API url (defaultL https://commons.wikimedia.org/w/api.php )
    :return: json object containing raw api response of image info
    """
    session = requests.Session()
    if title[:5] != "File:":
        title = "File:" + title
    params = {
        "action": 'query',
        "format": 'json',
        "prop": 'imageinfo',
        "titles": title
    }

    response = session.get(url=url, params=params)
    del session
    del params
    del title
    for _, v in response.json()['query']['pages'].items():
        return v


def getPageID(title):
    """
    Fetches page ID from a given title
    :param title: title of page to get page ID for. This can be in the form of "File:<name>" or just "<name>"
    :return: Page ID (int
    """
    return int(getImageInfo(title)['pageid'])


#if __name__ == '__main__':
#    print(getPageID('File:Do Step Inn - Central 1.jpg'))
#    print(getPageID('Do Step Inn - Central 1.jpg'))
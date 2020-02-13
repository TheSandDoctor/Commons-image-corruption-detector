# -*- coding: UTF-8 -*-
import pywikibot
from pywikibot.data.api import APIError

site_pwb = pywikibot.Site("commons", "commons")


def allimages(start=None, prefix="", reverse=False, step=None, total=None, content=False):
    pages = site_pwb.allimages(
        start=start,
        prefix=prefix,
        reverse=reverse,
        step=step,
        total=total,
        content=content
    )
    return pages


def tag_page(filepage, template, summary, minor=True):
    # Modified version of
    # https://github.com/toolforge/embeddeddata/blob/5ecd31417a4c3c5d1be9c2a58f55a1665d9c767f/worker.py#L361
    filepage.clear_cache()

    if not filepage.exists():
        pywikibot.warning("Page doesn't exist, skipping save.")
        return

    # Make sure no edit conflicts happen here
    try:
        retry_apierror(
            lambda:
            filepage.save(prependtext=template + '\n',
                          summary=summary, minor=minor, botflag=True, force=True)
        )
    except pywikibot.exceptions.LockedPage as e:
        print(filepage.title())
        print(e.message)


def retry_apierror(f):
    # https://github.com/toolforge/embeddeddata/blob/5ecd31417a4c3c5d1be9c2a58f55a1665d9c767f/worker.py#L238
    for i in range(8):
        try:
            f()
        except APIError:
            pywikibot.warning(
                'Failed API request on attempt %d' % i)
        else:
            break
    else:
        raise

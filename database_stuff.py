# -*- coding: UTF-8 -*-
from __future__ import print_function
from datetime import date, datetime, timedelta, timezone
import mysql.connector as mariadb
from image_corruption_utils import get_remote_hash, allow_bots
import config
import manapi
import logging
from logging.config import fileConfig

fileConfig('logging_config.ini')
logger = logging.getLogger(__name__)

insert_image = ("INSERT INTO images_viewed "
                "(title, isCorrupt, date_scanned, to_delete_nom, hash, page_id, not_image) "
                "VALUES (%(title)s, %(isCorrupt)s, %(date_scanned)s, %(to_delete_nom)s, %(hash)s, %(page_id)s, %(not_image)s)")

expired_images = {"SELECT title, isCorrupt, date_scanned, to_delete_nom FROM images_viewed"
                  "WHERE to_delete_nom = %s"}

corrupt_images = "SELECT title, isCorrupt, date_scanned, to_delete_nom,  FROM images_viewed WHERE isCorrupt = 1"

update_entry = {"UPDATE images_viewed SET title = %s, isCorrupt = %s, to_delete_nom = %s, hash = %s, was_fixed = %s WHERE page_id = %s"}


def get_next_month(day_count):
    """
    Generate date timestamp from now until the provided day_count.
    :param day_count: how many days from now to calculate the date of (int)
    :return: Date string in format m/d/yyyy
    """
    return (datetime.now(timezone.utc).date() + timedelta(days=day_count)).strftime('%m/%d/%Y')


def gen_nom_date(days = 30):
    """
    Generate file nomination date.
    :param days: days from now that it will take effect
    :return: return list with nom date split on each '/'
    """
    return str(get_next_month(days)).split('/')


def calculate_difference(date_tagged):
    """
    Calculate the difference between the current date and a provided date string
    :param date_tagged: Date string
    :return: the difference in days (int) between current date and provided date_tagged
    """
    date_tagged = datetime.strptime(date_tagged, '%m/%d/%Y').date()
    return (datetime.now(timezone.utc).date() - date_tagged).days


def store_image(title, isCorrupt, img_hash, day_count=30, page_id=None, not_image=False):
    """
    Stores current image information (provided in header) into the database for this application.
    :param title: filename
    :param isCorrupt: (bool)
    :param img_hash: sha1 hash of image
    :param page_id: page id (optional)
    :param day_count: how long a grace period pre-nomination if unresolved by then (default: 30 days, not stored
    if image isn't corrupt in the first place (database defaults to NULL if no value provided)
    :param not_image: False if file is an image, true otherwise
    :return: None
    """
    global logger
    if page_id is None and not not_image:
        try:
            page_id = manapi.getPageID(title)
        except KeyError:
            page_id = -1
            logger.error("KeyError - cannot get page ID from API")
    if page_id is None:
        page_id = -1
    cnx = mariadb.connect(**config.config)
    cursor = cnx.cursor()
    if not_image:
        image_data = {
            'title': title,
            'isCorrupt': False,
            'date_scanned': datetime.now(timezone.utc).date().strftime('%m/%d/%Y'),
            'to_delete_nom': None,
            'hash': str(img_hash),
            'page_id': int(page_id),
            'not_image': not_image
        }
    elif isCorrupt:
        image_data = {
            'title': title,
            'isCorrupt': isCorrupt,
            'date_scanned': datetime.now(timezone.utc).date().strftime('%m/%d/%Y'),
            'to_delete_nom': get_next_month(day_count),
            'hash': str(img_hash),
            'page_id': int(page_id),
            'not_image': not_image
        }
    else:
        image_data = {
            'title': title,
            'isCorrupt': isCorrupt,
            'date_scanned': datetime.now(timezone.utc).date().strftime('%m/%d/%Y'),
            'to_delete_nom': None,
            'hash': str(img_hash),
            'page_id': int(page_id),
            'not_image': not_image
        }
    try:
        cursor.execute(insert_image, image_data)
        cnx.commit()
        logger.debug(cursor.rowcount, "record inserted.")
    except mariadb.Error as error:
        logger.error("Error: {}".format(error))
    finally:
        cnx.close()


def get_expired_images():
    """
    Get images whose expiry date is today (UTC)
    Return data structure is as follows:
           0th element: title
           1st element: isCorrupt
           2nd element: date_scanned
           3rd element: to_delete_nom
    :return: images whose expiry date is today (UTC) as tuples.
    """
    global logger
    cnx = mariadb.connect(**config.config)
    cursor = cnx.cursor()
    try:
        cursor.execute(expired_images, datetime.now(timezone.utc).date().strftime('%m/%d/%Y'))
        raw = cursor.fetchall()  # returns tuples
    except mariadb.Error as error:
        logger.error("Error: {}".format(error))
    finally:
        cnx.close()
    return raw
    # data = []
    # for i in raw:
    #    data.append(i[0])
    # return data


def get_all_corrupt():
    global logger
    cnx = mariadb.connect(**config.config)
    cursor = cnx.cursor()
    try:
        cursor.execute(corrupt_images)
        raw = cursor.fetchall()  # returns tuples
    except mariadb.Error as error:
        logger.error("Error: {}".format(error))
    finally:
        cnx.close()
    return raw


def have_seen_image(site, title, page_id=None):
    """
    Checks if we have previously viewed this image with its current hash value. This is done through connecting to the
    database for this application.
    :param site: site object
    :param title: filename to check
    :param page_id: page id to check (optional)
    :return: True if seen, False if not
    """
    if page_id is None:
        page_id = manapi.getPageID(title)
    res = False
    global logger
    cnx = mariadb.connect(**config.config)
    cursor = cnx.cursor()
    img_hash = get_remote_hash(site, title)
    sql = "SELECT title FROM images_viewed WHERE page_id=%s AND hash=%s"
    try:
        cursor.execute(sql, (page_id, img_hash))
        msg = cursor.fetchone()
        if msg is None:
            res = False
        else:
            res = True
    except mariadb.Error as error:
        logger.error("Error: {}".format(error))
    finally:
        cnx.close()
    return res


def update_entry(title, isCorrupt, to_delete_nom, img_hash, page_id=None, was_fixed=None):
    """
    Updates existing entry in database. This is currently called in image_followup when an image has been changed.
    :param title: filename
    :param isCorrupt: (bool)
    :param to_delete_nom: date string for when to nominate for deletion (NULL if not corrupt)
    :param img_hash: hash of the image to compare with the stored database value
    :param page_id: page id (optional)
    :param was_fixed: whether image was fixed
    :return: None
    """
    if page_id is None:
        page_id = manapi.getPageID(title)
    global logger
    cnx = mariadb.connect(**config.config)
    cursor = cnx.cursor()
    try:
        cursor.execute(update_entry, (title, isCorrupt, to_delete_nom, img_hash, was_fixed, page_id))
        cnx.commit()
    except mariadb.Error as error:
        logger.error("Error: {}".format(error))
    finally:
        cnx.close()
    logger.info("Record updated")
    logger.debug("Record updated -- " + str(page_id))

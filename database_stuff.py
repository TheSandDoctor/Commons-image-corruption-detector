from __future__ import print_function
from datetime import date, datetime, timedelta, timezone
import mysql.connector
from image_corruption_utils import getRemoteHash

insert_image = ("INSERT INTO images_viewed "
                "(title, isCorrupt, date_scanned, to_delete_nom, hash) "
                "VALUES (%(title)s, %(isCorrupt)s, %(date_scanned)s, %(to_delete_nom)s, %(hash)s)")

expired_images = {"SELECT title, isCorrupt, date_scanned, to_delete_nom FROM images_viewed"
                  "WHERE to_delete_nom = %s"}

update_entry = {"UPDATE images_viewed SET isCorrupt = %s, to_delete_nom = %s, hash = %s WHERE title = %s"}


def get_next_month(day_count):
    """
    Generate date timestamp from now until the provided day_count.
    :param day_count: how many days from now to calculate the date of (int)
    :return: Date string in format m/d/yyyy
    """
    return (datetime.now(timezone.utc).date() + timedelta(days=day_count)).strftime('%B/%d/%Y')


def calculate_difference(date_tagged):
    """
    Calculate the difference between the current date and a provided date string
    :param date_tagged: Date string
    :return: the difference in days (int) between current date and provided date_tagged
    """
    date_tagged = datetime.strptime(date_tagged, '%B/%d/%Y').date()
    return (datetime.now(timezone.utc).date() - date_tagged).days


def store_image(title, isCorrupt, img_hash, day_count=30):
    """
    Stores current image information (provided in header) into the database for this application.
    :param title: filename
    :param isCorrupt: (bool)
    :param img_hash: sha1 hash of image
    :param day_count: how long a grace period pre-nomination if unresolved by then (default: 30 days, not stored
    if image isn't corrupt in the first place (database defaults to NULL if no value provided)
    :return: None
    """
    cnx = mysql.connector.connect(**config)
    cursor = cnx.cursor()
    if isCorrupt:
        image_data = {
            'title': title,
            'isCorrupt': isCorrupt,
            'date_scanned': datetime.now(timezone.utc).date().strftime('%B/%d/%Y'),
            'to_delete_nom': get_next_month(day_count),
            'hash': str(img_hash)
        }
    else:
        image_data = {
            'title': title,
            'isCorrupt': isCorrupt,
            'date_scanned': datetime.now(timezone.utc).date().strftime('%B/%d/%Y'),
            'hash': str(img_hash)
        }
    cursor.execute(insert_image, image_data)
    cnx.commit()
    print(cursor.rowcount, "record inserted.")
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
    cnx = mysql.connector.connect(**config)
    cursor = cnx.cursor()
    cursor.execute(expired_images, datetime.now(timezone.utc).date().strftime('%B/%d/%Y'))
    raw = cursor.fetchall()  # returns tuples
    cnx.close()
    return raw
    # data = []
    # for i in raw:
    #    data.append(i[0])
    # return data


def have_seen_image(site, title):
    """
    Checks if we have previously viewed this image with its current hash value. This is done through connecting to the
    database for this application.
    :param site: site object
    :param title: filename to check
    :return: True if seen, False if not
    """
    cnx = mysql.connector.connect(**config)
    cursor = cnx.cursor()
    img_hash = getRemoteHash(site, title)
    sql = "SELECT title FROM images_viewed WHERE title = %s AND hash=%s"
    cursor.execute(sql, (title, img_hash))
    msg = cursor.fetchone()
    cnx.close()
    return msg


def update_entry(title, isCorrupt, to_delete_nom, img_hash):
    """
    Updates existing entry in database. This is currently called in image_followup when an image has been corrected.
    :param title: filename
    :param isCorrupt: (bool)
    :param to_delete_nom: date string for when to nominate for deletion (NULL if not corrupt)
    :param img_hash: hash of the image to compare with the stored database value
    :return: None
    """
    cnx = mysql.connector.connect(**config)
    cursor = cnx.cursor()
    cursor.execute(update_entry, (isCorrupt, to_delete_nom, img_hash, title))
    cnx.commit()
    cnx.close()
    print("Record updated")

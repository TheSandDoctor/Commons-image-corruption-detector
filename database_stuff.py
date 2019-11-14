from __future__ import print_function
from datetime import date, datetime, timedelta, timezone
import mysql.connector
from image_corruption_utils import getRemoteHash

config = {
  'user': 'scott',
  'password': 'password',
  'host': '127.0.0.1',
  'database': 'images',
  'raise_on_warnings': True
}
insert_image = ("INSERT INTO images_viewed "
                "(title, isCorrupt, date_scanned, to_delete_nom, hash) "
                "VALUES (%(title)s, %(isCorrupt)s, %(date_scanned)s, %(to_delete_nom)s, %(hash)s)")

expired_images = {"SELECT title, isCorrupt, date_scanned, to_delete_nom FROM images_viewed"
                "WHERE to_delete_nom = %s"}

update_entry = {"UPDATE images_viewed SET isCorrupt = %s, to_delete_nom = %s, hash = %s WHERE title = %s"}

def getNextMonth(day_count):
    return (datetime.now(timezone.utc).date() + timedelta(days=day_count)).strftime('%m/%d/%Y')


def calculateDifference(date_tagged):
    """ Returns the difference in days (int) between current date and provided date_tagged
        date_tagged: Date string """
    date_tagged = datetime.strptime(date_tagged, '%m/%d/%Y').date()
    return (datetime.now(timezone.utc).date() - date_tagged).days


def store_image(title, isCorrupt, day_count = 30, hash):
    cnx = mysql.connector.connect(**config)
    cursor = cnx.cursor()
    if isCorrupt:
        image_info = {
            'title': title,
            'isCorrupt': isCorrupt,
            'date_scanned': datetime.now(timezone.utc).date().strftime('%m/%d/%Y'),
            'to_delete_nom': getNextMonth(day_count),
            'hash': str(hash)
        }
    else:
        image_data = {
            'title': title,
            'isCorrupt': isCorrupt,
            'date_scanned': datetime.now(timezone.utc).date().strftime('%m/%d/%Y'),
            'hash': str(hash)
        }
    cursor.execute(insert_image, image_data)
    cnx.commit()
    print(mycursor.rowcount, "record inserted.")
    cnx.close()


def get_expired_images():
    """ Returns images whose expiry date is today (UTC) as tuples.
        Return data structure is as follows:
            0th element: title
            1st element: isCorrupt
            2nd element: date_scanned
            3rd element: to_delete_nom
    """
    cnx = mysql.connector.connect(**config)
    cursor = cnx.cursor()
    cursor.execute(expired_images, datetime.now(timezone.utc).date().strftime('%m/%d/%Y'))
    raw = cursor.fetchall() # returns tuples
    cnx.close()
    return raw
    #data = []
    #for i in raw:
    #    data.append(i[0])
    #return data


def have_seen_image(site, title):
    cnx = mysql.connector.connect(**config)
    cursor = cnx.cursor()
    getRemoteHash(site, title)
    sql = "SELECT title FROM images_viewed WHERE title = %s AND hash=%s"
    cursor.execute(sql, (title, hash))
    msg = cursor.fetchone()
    cnx.close()
    if not msg:
        return False
    return True

def update_entry(title, isCorrupt, to_delete_nom, hash):
    cnx = mysql.connector.connect(**config)
    cursor = cnx.cursor()
    cursor.execute(update_entry, (isCorrupt, to_delete_nom, hash, title))
    cnx.commit()
    print("Record updated")

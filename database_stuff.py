from __future__ import print_function
from datetime import date, datetime, timedelta
import mysql.connector

config = {
  'user': 'scott',
  'password': 'password',
  'host': '127.0.0.1',
  'database': 'images',
  'raise_on_warnings': True
}
insert_image = ("INSERT INTO images_viewed "
                "(title, isCorrupt, date_scanned, to_delete_nom) "
                "VALUES (%(title)s, %(isCorrupt)s, %(date_scanned)s, %(to_delete_nom)s)")

expired_images = {"SELECT title, isCorrupt, to_delete_nom FROM images_viewed"
                "WHERE to_delete_nom = %s"}

def getNextMonth(day_count):
    return datetime.now(timezone.utc).date() + timedelta(days=day_count)


def store_image(title, isCorrupt, day_count = 30):
    cnx = mysql.connector.connect(**config)
    cursor = cnx.cursor()
    if isCorrupt:
        image_info = {
            'title': title,
            'isCorrupt': isCorrupt,
            'date_scanned': datetime.now(timezone.utc).date(),
            'to_delete_nom': getNextMonth(day_count),
        }
    else:
        image_data = {
            'title': title,
            'isCorrupt': isCorrupt,
            'date_scanned': datetime.now(timezone.utc).date(),
        }
    cursor.execute(insert_image, image_data)
    cnx.commit()
    print(mycursor.rowcount, "record inserted.")
    cnx.close()


def get_expired_images():
    """ Returns images whose expiry date is today (UTC) as a list. """
    cnx = mysql.connector.connect(**config)
    cursor = cnx.cursor()
    cursor.execute(expired_images, datetime.now(timezone.utc).date())
    raw = cursor.fetchall() # returns tuples
    cnx.close()
    data = []
    for i in raw:
        data.append(i[0])
    return data


def have_seen_image(title):
    cnx = mysql.connector.connect(**config)
    cursor = cnx.cursor()
    sql = "SELECT title FROM images_viewed WHERE title = %s"
    cursor.execute(sql, title)
    msg = cursor.fetchone()
    cnx.close()
    if not msg:
        return False
    return True

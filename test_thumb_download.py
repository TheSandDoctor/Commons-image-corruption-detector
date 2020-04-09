import requests
import pywikibot


def download_thumbnail(fp, path):
    revision = fp.latest_file_info
    r = requests.get(fp.get_file_url(url_width=800), stream=True)
    if r.status_code == 200:
        try:
            with open(path, 'wb') as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
        except IOError as e:
            raise e
        return True
    else:
        #self.logger.error("Could not download:: " + str(fp.title()))
        print("Could not download")
        return False

if __name__ == '__main__':
    site = pywikibot.Site(user="TheSandBot")
    file_page = pywikibot.FilePage(site, "File:Bo Thann winn.jpg")
    if file_page.latest_file_info['width'] > 600:
        print("Image > 600 wide")
        print(download_thumbnail(file_page, "./Test.jpg"))
    else:
        print("NO")
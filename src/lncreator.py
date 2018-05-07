from lncreator.lightnovel import LightNovel
from lncreator.release import Release
from lncreator.logger import logger
from lncreator.database import Database
import sys, requests, lncreator.utils

def print_help():
  logger.info("Usage: %s page_start page_end" % sys.argv[0])
  sys.exit(1)

def get_list_from_range_ranking(url_ranking="https://www.novelupdates.com/series-ranking/?rank=popular", page_start=1, page_end=1, database=None):
  if page_start < 1:
    logger.critical("Page start must be higher or equal than 1 (%d)" % page_start)
    return False
  elif page_end < 1 or page_end < page_start:
    logger.critical("Page end must be higher or equal than 1 and page start (%d) " % page_end)
    return False
  for page_id in range(page_start, page_end + 1):
    url = "%s&pg=%d" % (url_ranking, page_id)
    logger.debug("Trying to get lightnovels from url [%s] (page: [%d])..." % (url, page_id))
    response = lncreator.utils.get_page_response(url)
    if not response:
      return False
    soup = lncreator.utils.get_bs_format(response)
    if not soup:
      return False
    tr_tags = soup.find_all("tr", class_="bdrank")
    if not tr_tags:
      logger.critical("Unable to find <tr> tag with class bdrank")
      return False
    for tr_tag in tr_tags:
      td_tags = tr_tag.find_all("td")
      if not td_tags:
        logger.critical("Unable to find <td> tags!")
        return False
      a_tag = td_tags[-1].find("a")
      if not a_tag:
        logger.critical("Unable to find <a> tag!")
        return False
      try:
        lightnovel = LightNovel(a_tag.get('href'))
        if not lightnovel.get_releases():
          logger.error("Unable to get releases...")
          continue
        if not lightnovel.add_in_database(database):
          logger.error("An error occured while adding your LN into our database...")
          continue
      except Exception as e:
        logger.error(e)
        continue

def main():
  database = Database("sqlite.db")
  if len(sys.argv) == 3:
    page_start = int(sys.argv[1])
    page_end = int(sys.argv[2])
    get_list_from_range_ranking("https://www.novelupdates.com/series-ranking/?rank=popular", page_start, page_end, database)
  elif len(sys.argv) == 2:
    url = sys.argv[1]
    lightnovel = LightNovel(url)
    if not lightnovel.get_releases():
      logger.error("Unable to get releases...")
      return 1
    if not lightnovel.add_in_database(database):
      logger.error("An error occured while adding your LN into our database...")
      return 1


if __name__ == "__main__":
  main()
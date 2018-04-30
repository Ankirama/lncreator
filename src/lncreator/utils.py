from lncreator.logger import logger
import requests
from bs4 import BeautifulSoup
from requests.exceptions import MissingSchema

def format_link(link):
    if link[:2] == "//":
        return "https:%s" % link
    else:
        return link

def get_page_response(url):
    '''
    Use requests to get the response of the release's page
    Return False or Response
    '''
    logger.info("Getting response from requests...")
    if not url:
      logger.warning("Unable to get novelupdates_url...")
      return False
    try:
      response = requests.get(url)
    except MissingSchema:
      logger.warning("Bad URL format for [%s]" % url)
      return False
    logger.debug("Status code for url [%s]: %d" % (url, response.status_code))
#    logger.debug("[%s] content: %s" % (url, response.text))
    if response.status_code != 200:
      logger.warning("Unable to process [%s] : Bad status code [%d]" % (url, response.status_code))
      return False
    logger.info("URL [%s]: OK" % url)
    return response

def get_bs_format(response):
    '''
    Use beautifulsoup with the response's content to parse the page
    Return False or BeautifulSoup
    '''
    logger.info("Converting in Beautiful format...")
    if not response:
      logger.warning("Unable to find a _response...")
      return False
    soup = BeautifulSoup(response.content, "lxml")
    if not soup:
      logger.warning("Unable to process bs4 for url [%s]" % response.url)
      return False
    logger.debug("BS4 format OK")
    return soup
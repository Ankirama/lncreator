import requests
from lncreator.release import Release
from lncreator.logger import logger
from bs4 import BeautifulSoup
from lncreator import exceptions
from requests.exceptions import MissingSchema
import lncreator.utils

class LightNovel(object):
  _releases = []
  _url = None

  def __init__(self, url):
    if not isinstance(url, str):
      raise TypeError("url must be a string")
    logger.info("Creating a new LN for url [%s]..." % url)
    self._url = url

  def number_pages_releases(self):
    '''
    Return number of pages for a specific LN
    If there is a 'next' button then the number of page is just before
    Else this is the last element

    The class used to find it in novelupdates is `digg_pagination`
    '''
    logger.debug("Getting number of pages from novelupdates [%s]..." % self._url)
    if self._soup:
      logger.warning("Unable to get soup...")
      return False
    div = self._soup.find('div', class_='digg_pagination')
    if not div:
      raise exceptions.NovelUpdatesSoupError("Unable to find class digg_pagination in novel updates [%s]!!" % self._url)
    pages = div.find_all('a')
    if not pages:
      raise exceptions.NovelUpdatesSoupError("Unable to get number of pages from novel updates!")
    pages_number = -1
    if pages[-1].get('rel') == ['next']:
      pages_number = int(pages[-2].text)
    else:
      pages_number = int(pages[-1].text)
    logger.debug("Number of pages: [%d]" % pages_number)
    return pages_number

  def get_release_data_from_tr(self, page_url, tr_tag):
      td_tags = tr_tag.find_all("td")
      if not td_tags:
        raise exceptions.NovelUpdatesSoupError("Unable to find any tag <td> in novel updates [%s]..." % page_url)
      if len(td_tags) < 3:
        raise exceptions.NovelUpdatesSoupError("Not enough <td> tags ([%d]) in novel updates [%s]" % (len(td_tags), page_url))
      release_data = td_tags[2].find("a")
      if not release_data:
        raise exceptions.NovelUpdatesSoupError("Unable to find <a> tag in td_tags[2] (release data)... in novel updates [%s]" % page_url)
      basic_data = {}
      basic_data['title'] = release_data.text
      basic_data['href'] = lncreator.utils.format_link(release_data.get('href'))
      group_data = td_tags[1].find("a")
      if not group_data:
        raise exceptions.NovelUpdatesSoupError("Unable to find <a> tag in td_tags[1] (group data)... in novel updates [%s]" % page_url)
      basic_data['group'] = group_data.text
      basic_data['group_href'] = lncreator.utils.format_link(group_data('href'))
      logger.debug("Trying to create release url [%s]..." % basic_data['href'])
      try:
        release = Release(basic_data)
      except TypeError as e:
        logger.warning(e)
        return False
      if not release.get_data_content():
        return False
      return release

  def get_releases_from_page(self, page_url):
    logger.debug("Getting releases from page [%s]..." % page_url)
    response = lncreator.utils.get_page_response(page_url)
    if not response:
      return False
    soup = lncreator.utils.get_bs_format(response)
    if not soup:
      return False
    table_tag = soup.find("table", id="myTable")
    if not table_tag:
      raise exceptions.NovelUpdatesSoupError("Unable to find tag <table> with id [myTable] in novel updates [%s]" % page_url)
    tbody_tag = table_tag.find("tbody")
    if not tbody_tag:
      raise exceptions.NovelUpdatesSoupError("Unable to find tag <tbody> in <table> in novel updates [%s]" % page_url)
    tr_tags = tbody_tag.find_all("tr")
    if not tr_tags:
      raise exceptions.NovelUpdatesSoupError("Unable to find tag <tr> in <tbody> in novel updates [%s]" % page_url)
    logger.debug("Number of releases in this page (normaly): [%d]" % len(tr_tags))
    for tr_tag in tr_tags:
      try:
        release = self.get_release_data_from_tr(page_url, tr_tag)
      except exceptions.NovelUpdatesSoupError as e:
        raise exceptions.NovelUpdatesSoupError(e)
      if not release:
        logger.warning("Unable to find data for releases [%s]" % page_url)
        return False
      try:
        self._releases.insert(0, release)
      except Exception as e:
        logger.warning("Unable to push release...")
        logger.warning(e)

  def get_releases(self):
    logger.debug("Getting releases for [%s]..." % self._url)
    self._response = lncreator.utils.get_page_response(self._url)
    if not self._response:
      return False
    self._soup = lncreator.utils.get_bs_format(self._response)
    if not self._soup:
      return False
    number_pages = self.number_pages_releases()
    if not number_pages:
      return False
    self._releases = []
    for page_id in range(1, number_pages):
      page_url = "%s?pg=%d" % (self._url, page_id)
      self.get_releases_from_page(page_url)

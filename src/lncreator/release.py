import requests
from lncreator.logger import logger
from bs4 import BeautifulSoup, NavigableString
from requests.exceptions import MissingSchema
import lncreator.utils

class Release(object):
  _novelupdates_url = None
  _url = None
  _soup = None
  _title = None
  _group = None
  _tags = None
  _pseudo_content = None
  _children_content = None
  _parent = None

  BASIC_STRUCT = ["group", "group_href", "title", "href"]

  def __init__(self, basic_data):
    if not isinstance(basic_data, dict):
      raise TypeError("basic_data must be a dictionnary")
    for key in self.BASIC_STRUCT:
      if not key in basic_data:
        logger.error("Unable to create release, the key [%s] is missing.\nData given:" % key)
        logger.error(basic_data)
        raise TypeError("Your basic_data must contain [%s]" % key)
    self._group = {'name': basic_data["group"], 'url': basic_data['group_href']}
    self._title = basic_data['title']
    self._novelupdates_url = basic_data['href']

  def _add_tag(self, tags, tag_to_add):
    if tag_to_add in tags:
      tags[tag_to_add] += 1
    else:
      tags[tag_to_add] = 1

  def add_in_database(self, database, id_lightnovel):
    logger.debug("Adding a release in id_lightnovel [%d]..." % id_lightnovel)
    logger.debug("Trying to add the group...")
    if not self._group:
      logger.error("Your group is empty!")
      return False
    id_group = database.add_group(self._group)
    if not id_group:
      return False
    id_release = database.add_release({'name': self._title, 'url': self._url, 'id_group': id_group, 'id_lightnovel': id_lightnovel})
    if not id_release:
      return False
    for key, value in self._tags.items():
      id_tag = database.add_tag({'name': key, 'id_release': id_release, 'number': value})
      if not id_tag:
        logger.error("Unable to add tag [%s] in database" % key)
    return True

  def get_soup_content(self):
    '''
    Return string format of the page content
    Or False
    '''
    if not self._soup:
      return False
    else:
      return self._soup.prettify()

  def _find_release_content_position(self, p_tags):
    '''
    Try to guess the release content by finding where are the <p> tags
    '''
    logger.debug("Trying to get content position of [%s]" % self._url)
    if not p_tags:
      logger.error("Unable to find any <p> tags... Stopping here")
      return -1
    i = 0
    index = -1
    size = 0
    logger.debug("Total <p> tags to check: [%d]" % len(p_tags))
    while i < len(p_tags):
      logger.debug("Checking tag <p> index [%d]..." % i)
      tmp_len = len([x for x in p_tags[i].next_siblings if x.name == 'p'])
      logger.debug("Number of p tags found: %d" % tmp_len)
      if tmp_len > size:
        index = i
        size = tmp_len
      i += tmp_len + 1
    return index

  def _get_parent_data(self, p_tag):
    '''
    Try to get the parent tag (and children content) from the <p> tag
    '''
    logger.debug("Trying to get parent data...")
    if not p_tag:
      logger.error("Unable to find your p_tag...")
      return False
    parent_tag = p_tag.parent
    if not parent_tag:
      logger.error("Unable to find a parent for your p_tag....")
      return False
    parent_classes = []
    parent_id = ""
    try:
      parent_classes = parent_tag["class"]
    except KeyError:
      parent_classes = []
    try:
      parent_id = parent_tag["id"]
    except KeyError:
      parent_id = ""
    logger.debug("Parent found:")
    logger.debug("tag: %s" % parent_tag.name)
    logger.debug("classes: %s" % (" - ".join(parent_classes)))
    logger.debug("id: %s" % parent_id)
    self._children_content = parent_tag.contents
    return {"tag": parent_tag.name, "classes": parent_classes, "id": parent_id}

  def _get_number_tags_content(self, p_tag):
    logger.debug("Trying to get number of each tags from content...")
    if not p_tag:
      logger.error("Unable to find your p_tag...")
      return False
    self._pseudo_content = [p_tag] + [tag for tag in p_tag.next_siblings]
    tags_data = dict()
    for tag in self._pseudo_content:
      if tag.name != None:
        if isinstance(tag, NavigableString):
          self._add_tag(tags_data, "string")
        else:
          self._add_tag(tags_data, tag.name)
      else:
        if "None" in tags_data:
          self._add_tag(tags_data, "None")
    return tags_data

  def get_data_content(self):
    self._response = lncreator.utils.get_page_response(self._novelupdates_url)
    if not self._response:
      return False
    logger.info("Trying to get metadata content for url [%s]..." % self._url)
    logger.debug("URL after redirection via response: [%s]" % self._response.url)
    self._url = self._response.url
    self._soup = lncreator.utils.get_bs_format(self._response)
    if not self._soup:
      return False
    p_tags = self._soup.find_all("p")
    index = self._find_release_content_position(p_tags)
    if index == -1:
      logger.error("Unable to find p_tags...")
      return False
    p_tag = p_tags[index]
    parent = self._get_parent_data(p_tag)
    if not parent:
      return False
    self._parent = parent
    tags = self._get_number_tags_content(p_tag)
    if not tags:
      return False
    self._tags = tags
    return True

  def to_csv_with_filename(self, filename):
    pass

  def to_csv_with_writer(self, spamwriter):
    pass


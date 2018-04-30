import sqlite3
from lncreator.logger import logger

class Database(object):
  CREATE_LIGHTNOVEL_TABLE = """CREATE TABLE IF NOT EXISTS lightnovels
      (id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      url TEXT NOT NULL UNIQUE,
      releases_number INTEGER DEFAULT 0,
      pages_number INTEGER DEFAULT 0
      );"""
  CREATE_RELEASE_TABLE = """CREATE TABLE IF NOT EXISTS releases
      (id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      url TEXT NOT NULL UNIQUE,
      id_group INTEGER,
      id_lightnovel INTEGER,
      FOREIGN KEY(id_group) REFERENCES groups(id),
      FOREIGN KEY(id_lightnovel) REFERENCES lightnovels(id)
      );"""
  CREATE_GROUP_TABLE = """CREATE TABLE IF NOT EXISTS groups
      (id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      url TEXT NOT NULL UNIQUE
      );"""
  CREATE_TAG_TABLE = """CREATE TABLE IF NOT EXISTS tags
  (name TEXT NOT NULL,
  number INTEGER DEFAULT 0,
  id_release INTEGER,
  FOREIGN KEY(id_release) REFERENCES releases(id)
  );"""

  SELECT_GROUP_BY_ID = "SELECT * FROM groups WHERE id = :id;"
  SELECT_GROUP_BY_URL = "SELECT * FROM groups WHERE url LIKE :url;"
  SELECT_RELEASE_BY_ID = "SELECT * FROM releases WHERE id = :id;"
  SELECT_RELEASE_BY_URL = "SELECT * FROM releases WHERE url LIKE :url;"
  SELECT_RELEASES_BY_LIGHTNOVEL_ID = "SELECT * FROM releases WHERE id_lightnovel = :id;"
  SELECT_RELEASES_BY_GROUP_ID = "SELECT * FROM releases WHERE id_group = :id;"
  SELECT_TAGS_BY_ID_RELEASE = "SELECT * FROM tags WHERE id_release = :id_release;"
  SELECT_TAG_BY_ID = "SELECT * FROM tags WHERE id = :id;"
  SELECT_TAB_BY_RELEASE_NAME = "SELECT * FROM tags WHERE id_release = :id_release AND name LIKE :name;"
  SELECT_LIGHTNOVEL_BY_URL = "SELECT * FROM lightnovels WHERE url = :url;"
  SELECT_LIGHTNOVEL_BY_ID = "SELECT * FROM lightnovels WHERE id = :id;"
  INSERT_RELEASE = "INSERT INTO releases (name, url, id_group, id_lightnovel) VALUES (:name, :url, :id_group, :id_lightnovel);"
  INSERT_GROUP = "INSERT INTO groups (:name, :url) VALUES(:name, :url);"
  INSERT_LIGHTNOVEL = "INSERT INTO lightnovels (name, url, releases_number, pages_number) VALUES (:name, :url, :releases_number, :pages_number);"
  INSERT_TAG = "INSERT INTO tags (name, number, id_release) VALUES (:name, :number, :id_releases)"
  UPDATE_TAG = "UPDATE tags SET number = :number WHERE id = :id;"

  def __init__(self, dbname):
    logger.info("Creating database / tables for [%s]..." % dbname)
    try:
      self._conn = sqlite3.connect(dbname)
      self._cursor = self._conn.cursor()
    except sqlite3.OperationalError as e:
      logger.error("Database [%s] error: %s" % (dbname, e))
      raise sqlite3.OperationalError(e)
    if not self._create_tables():
      raise sqlite3.OperationalError("Unable to create tables...")

  def __del__(self):
    self._cursor.close()
    logger.info("Database closed")

  def _create_tables(self):
    try:
      self._cursor.execute(self.CREATE_LIGHTNOVEL_TABLE)
      self._cursor.execute(self.CREATE_RELEASE_TABLE)
      self._cursor.execute(self.CREATE_GROUP_TABLE)
      self._cursor.execute(self.CREATE_TAG_TABLE)
    except sqlite3.OperationalError as e:
      logger.error("[Database]: Unable to create tables: [%s]" % e)
      return False
    else:
      logger.info("[Database]: Tables created")
      return True

  def select_entries(self, query, data):
    logger.debug("[Database]: Trying to select entries [%s]..." % query)
    logger.debug(data)
    if not isinstance(data, dict):
      logger.error("[Database]: data must be a dict...")
      return False
    try:
      cursor = self._cursor.execute(query, data)
    except sqlite3.OperationalError as e:
      logger.error("[Database]: Unable to execute select in [%s]: %s" % (query, e))
      return False
    result = curosr.fetchall()
    return result

  def check_entry(self, query, data):
    select_query = None
    if query == self.INSERT_GROUP:
      select_query = self.SELECT_GROUP_BY_URL
    elif query == self.INSERT_RELEASE:
      select_query = self.SELECT_RELEASE_BY_URL
    elif query == self.INSERT_LIGHTNOVEL:
      select_query = self.SELECT_LIGHTNOVEL_BY_URL
    else:
      logger.debug("[Database]: no check function used for [%s]" % query)
      return []
    return self.select_entries(select_query, data)

  def add_entry_with_check(self, query, data, keys):
    logger.info("[Database]: Trying to add an entry [%s]..." % query)
    logger.debug(data)
    if not isinstance(data, dict):
      logger.error("[Database]: data must be a dict...")
      return False
    for key in keys:
      if key not in data:
        logger.error("[Database]: The key [%s] is missing in data" % key)
        return False
    rows = self.check_entry(query, data)
    if rows == False:
      return False
    result_size = len(rows)
    if result_size >= 1:
      logger.warning("[Database]: Your entry already exists, id [%s] returned!" % rows[0][0])
      return rows[0][0]
    try:
      self._cursor.execute(query, data)
      self._conn.commit()
    except sqlite3.OperationalError as e:
      logger.error("[Database]: Unable to add an entry in query [%s]: [%s]" % (query, e))
      return False
    logger.debug("[Database]: Entry created, id returned: [%s]" % self._cursor.lastrowid)
    return self._cursor.lastrowid

  def add_group(self, data):
    return self.add_entry_with_check(self.INSERT_GROUP, data, ['name', 'url'])

  def add_tag(self, data):
    tag = self.select_entries(self.SELECT_TAB_BY_RELEASE_NAME, data)
    if tag == False:
      return False
    if len(tag) == 0:
      return self.add_entry_with_check(self.INSERT_TAG, data, ['name', 'number', 'id_release'])
    else:
      return self.add_entry_with_check(self.UPDATE_TAG, {'id': tag[0][0], 'number': data['number']}, ['number', 'id'])

  def add_release(self, data):
    if not "id_group" in data:
      logger.error("[Database]: The key [%s] is missing in data" % "id_group")
      return False
    if not self.select_entries(self.SELECT_GROUP_BY_ID, data):
      logger.error("[Database]: Unable to find a group with id [%s]" % data['id_group'])
    return self.add_entry_with_check(self.INSERT_RELEASE, data ['name', 'url', 'id_group', 'id_lightnovel'])

  def add_lightnovel(self, data):
    return self.add_entry_with_check(self.INSERT_LIGHTNOVEL, data, ['name', 'url', 'releases_number', 'pages_number'])

LOGGING_LEVEL = 'WARNING'
LOG_STDOUT = True

'''
    configuration for ADSJournals postgres database
'''
# COLLECTIONS is a list of which collections/databases are stored
COLLECTIONS = ['ast', 'phy', 'gen', 'pre']

# DATA_DIRECTORY:
JDB_DATA_DIR = '/data_source/'

# BIBSTEMS has bibstem, R/J/C/etc, and canonical name
BIBSTEMS_FILE = JDB_DATA_DIR + 'bibstems.dat'

# JOURNAL_ABBREV has bibstem and multiple title abbreviations (e.g.
# A&A, AA, Astron. & Astrophys.)
JOURNAL_ABBREV_FILE = JDB_DATA_DIR + 'journals_abbrev.dat'

JOURNAL_ISSN_FILE = JDB_DATA_DIR + 'journal_issn'
ISSN_JOURNAL_FILE = JDB_DATA_DIR + 'issn2journal'
CANONICAL_BIB_FILE = JDB_DATA_DIR + 'bib2accno.dat'

# RASTERIZING.xml directory
RASTER_CONFIG_DIR = JDB_DATA_DIR + 'raster_config/'

# REFSOURCE_FILE
BIB_TO_REFS_FILE = JDB_DATA_DIR + 'citing2file.dat'

BIBSTEM_VOLUMES = ['book', 'conf', 'work', 'proc', 'rept', 'symp', 'prop']

EDITABLE_TABLES = ['abbrevs', 'master', 'idents', 'names', 'publisher', 'titlehistory']


'''
   configuration for Google Sheets service
'''
SECRETS_PATH = '/secrets/'

CREDENTIALS_FILE = SECRETS_PATH + 'foo.dat'

TOKEN_FILE = SECRETS_PATH + 'bar.dat'

HOME_FOLDER_ID = 'dummy_folder_id'

EDITORS = ['mygmailaccount@gmail.com']


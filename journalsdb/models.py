try:
    from adsputils import get_date, UTCDateTime
except ImportError:
    from adsmutils import get_date, UTCDateTime

import json

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (Table, Column, Integer, Numeric, String, TIMESTAMP,
                        ForeignKey, Boolean, Float, Text, UniqueConstraint)
from sqlalchemy.dialects.postgresql import ENUM

Base = declarative_base()


class JournalsMaster(Base):
    __tablename__ = 'master'

    pub_type = ENUM('Journal', 'Conf. Proc.', 'Monograph', 'Book',
                    'Software', 'Other', name='pub_type')
    ref_status = ENUM('yes', 'no', 'partial', 'na', name='ref_status')

    masterid = Column(Integer, primary_key=True, unique=True)
    bibstem = Column(String, unique=True, nullable=False)
    journal_name = Column(String, nullable=False)
    primary_language = Column(String, nullable=False, default='en')
    multilingual = Column(Boolean, nullable=False, default=False)
    defunct = Column(Boolean, nullable=False, default=False)
    pubtype = Column(pub_type, nullable=False)
    refereed = Column(ref_status, nullable=False)
    collection = Column(String, nullable=True)
    completeness_fraction = Column(String, nullable=True)
    completeness_details = Column(Text)
    notes = Column(Text)
    not_indexed = Column(Boolean, nullable=False, default=False)
    deprecated = Column(Boolean, nullable=False, default=False)
    created = Column(UTCDateTime, default=get_date)
    updated = Column(UTCDateTime, onupdate=get_date)

    def __repr__(self):
        return "master.masterid='{self.masterid}'".format(self=self)

    def toJSON(self):
        completeness_details = self.completeness_details
        if completeness_details:
            completeness_details = json.loads(completeness_details)
        return {'bibstem': self.bibstem,
                'journal_name': self.journal_name,
                'primary_language': self.primary_language,
                'multilingual': self.multilingual,
                'defunct': self.defunct,
                'pubtype': self.pubtype,
                'refereed': self.refereed,
                'collection': self.collection,
                'completeness_fraction': self.completeness_fraction,
                'completeness_details': completeness_details,
                'notes': self.notes,
                'not_indexed': self.not_indexed,
                'deprecated': self.deprecated}


class JournalsMasterHistory(Base):
    __tablename__ = 'master_hist'

    histid = Column(Integer, primary_key=True, autoincrement=True,
                    unique=True, nullable=False)
    editid = Column(Integer)
    masterid = Column(Integer)
    bibstem = Column(String)
    journal_name = Column(String)
    primary_language = Column(String)
    multilingual = Column(Boolean)
    defunct = Column(Boolean)
    pubtype = Column(String)
    refereed = Column(String)
    collection = Column(String)
    completeness_fraction = Column(String)
    completeness_details = Column(Text)
    notes = Column(Text)
    not_indexed = Column(Boolean)
    deprecated = Column(Boolean)
    created = Column(UTCDateTime)
    updated = Column(UTCDateTime)
    superseded = Column(UTCDateTime, default=get_date)

    def __repr__(self):
        return "master_hist.masterid='{self.masterid}'".format(self=self)


class JournalsNames(Base):
    __tablename__ = 'names'

    nameid = Column(Integer, primary_key=True, autoincrement=True,
                    unique=True, nullable=False)
    masterid = Column(Integer, ForeignKey('master.masterid'),
                      primary_key=True, nullable=False)
    name_english_translated = Column(String, nullable=False)
    title_language = Column(String, nullable=False)
    name_native_language = Column(String, nullable=False)
    name_normalized = Column(String, nullable=False)
    created = Column(UTCDateTime, default=get_date)
    updated = Column(UTCDateTime, onupdate=get_date)

    def __repr__(self):
        return "names.masterid='{self.masterid}'".format(self=self)

    def toJSON(self):
        return {'name_english_translated': self.name_english_translated,
                'title_language': self.title_language,
                'name_native_language': self.name_native_language,
                'name_normalized': self.name_normalized}


class JournalsNamesHistory(Base):
    __tablename__ = 'names_hist'

    histid = Column(Integer, primary_key=True, autoincrement=True,
                    unique=True, nullable=False)
    editid = Column(Integer)
    nameid = Column(Integer)
    masterid = Column(Integer)
    name_english_translated = Column(String)
    title_language = Column(String)
    name_native_language = Column(String)
    name_normalized = Column(String)
    created = Column(UTCDateTime)
    updated = Column(UTCDateTime)
    superseded = Column(UTCDateTime, default=get_date)

    def __repr__(self):
        return "names_hist.masterid='{self.masterid}'".format(self=self)


class JournalsAbbreviations(Base):
    __tablename__ = 'abbrevs'

    abbrevid = Column(Integer, primary_key=True, autoincrement=True,
                      unique=True, nullable=False)
    masterid = Column(Integer, ForeignKey('master.masterid'),
                      primary_key=True, nullable=False)
    abbreviation = Column(String)
    canonical = Column(Boolean, default=False, nullable=False)
    created = Column(UTCDateTime, default=get_date)
    updated = Column(UTCDateTime, onupdate=get_date)

    def __repr__(self):
        return "abbrevs.abbrevid='{self.abbrevid}'".format(self=self)

    def toJSON(self):
        return {'abbreviation': self.abbreviation}


class JournalsAbbreviationsHistory(Base):
    __tablename__ = 'abbrevs_hist'

    histid = Column(Integer, primary_key=True, autoincrement=True,
                    unique=True, nullable=False)
    editid = Column(Integer)
    abbrevid = Column(Integer)
    masterid = Column(Integer)
    abbreviation = Column(String)
    canonical = Column(Boolean)
    created = Column(UTCDateTime)
    updated = Column(UTCDateTime)
    superseded = Column(UTCDateTime, default=get_date)

    def __repr__(self):
        return "abbrevs.abbrevid='{self.abbrevid}'".format(self=self)


class JournalsIdentifiers(Base):
    __tablename__ = 'idents'

    identid = Column(Integer, primary_key=True, autoincrement=True,
                     unique=True, nullable=False)
    masterid = Column(Integer, ForeignKey('master.masterid'),
                      primary_key=True, nullable=False)
    id_type = Column(String)
    id_value = Column(String)
    created = Column(UTCDateTime, default=get_date)
    updated = Column(UTCDateTime, onupdate=get_date)

    def __repr__(self):
        return "idents.identid='{self.identid}'".format(self=self)

    def toJSON(self):
        return{'id_type': self.id_type,
               'id_value': self.id_value}


class JournalsIdentifiersHistory(Base):
    __tablename__ = 'idents_hist'

    histid = Column(Integer, primary_key=True, autoincrement=True,
                    unique=True, nullable=False)
    editid = Column(Integer)
    identid = Column(Integer)
    masterid = Column(Integer)
    id_type = Column(String)
    id_value = Column(String)
    created = Column(UTCDateTime)
    updated = Column(UTCDateTime)
    superseded = Column(UTCDateTime, default=get_date)

    def __repr__(self):
        return "idents_histidentid='{self.identid}')".format(self=self)


class JournalsPublisher(Base):
    __tablename__ = 'publisher'

    publisherid = Column(Integer, primary_key=True, autoincrement=True,
                         unique=True, nullable=False)
    pubabbrev = Column(String)
    pubaddress = Column(String)
    pubcontact = Column(Text)
    puburl = Column(String)
    pubextid = Column(String)
    pubfullname = Column(String)
    notes = Column(Text)
    created = Column(UTCDateTime, default=get_date)
    updated = Column(UTCDateTime, onupdate=get_date)

    def __repr__(self):
        return "publisher.publisherid='{self.publisherid}'".format(self=self)

    def toJSON(self):
        return {'publisherid': self.publisherid,
                'pubabbrev': self.pubabbrev,
                'pubaddress': self.pubaddress,
                'pubcontact': self.pubcontact,
                'puburl': self.puburl,
                'pubextid': self.pubextid,
                'pubfullname': self.pubfullname,
                'notes': self.notes}

class JournalsPublisherHistory(Base):
    __tablename__ = 'publisher_hist'

    histid = Column(Integer, primary_key=True, unique=True)
    editid = Column(Integer)
    publisherid = Column(Integer)
    pubabbrev = Column(String)
    pubaddress = Column(String)
    pubcontact = Column(Text)
    puburl = Column(String)
    pubextid = Column(String)
    pubfullname = Column(String)
    notes = Column(Text)
    created = Column(UTCDateTime)
    updated = Column(UTCDateTime)
    superseded = Column(UTCDateTime, default=get_date)

    def __repr__(self):
        return "publisher_hist.publisherid='{self.publisherid}'"\
               .format(self=self)


class JournalsTitleHistory(Base):
    __tablename__ = 'titlehistory'

    titlehistoryid = Column(Integer, primary_key=True, autoincrement=True,
                       unique=True, nullable=False)
    masterid = Column(Integer, ForeignKey('master.masterid'),
                      primary_key=True, nullable=False)
    year_start = Column(Integer)
    year_end = Column(Integer)
    vol_start = Column(String)
    vol_end = Column(String)
    publisherid = Column(Integer, ForeignKey('publisher.publisherid'))
    successor_bibstems = Column(String)
    predecessor_bibstems = Column(String)
    successor_issns = Column(String)
    predecessor_issns = Column(String)
    predecessor_codens = Column(String)
    successor_codens = Column(String)
    notes = Column(Text)
    created = Column(UTCDateTime, default=get_date)
    updated = Column(UTCDateTime, onupdate=get_date)

    def __repr__(self):
        return "titlehistory.titlehistoryid='{self.titlehistoryid}'".format(self=self)

    def toJSON(self):
        return {'year_start': self.year_start,
                'year_end': self.year_end,
                'vol_start': self.vol_start,
                'vol_end': self.vol_end,
                'publisherid': self.publisherid,
                'successor_bibstems': self.successor_bibstems,
                'predecessor_bibstems': self.predecessor_bibstems,
                'successor_issns': self.successor_issns,
                'predecessor_issns': self.predecessor_issns,
                'successor_codens': self.successor_codens,
                'predecessor_codens': self.predecessor_codens,
                'notes': self.notes}

class JournalsTitleHistoryHistory(Base):
    __tablename__ = 'titlehistory_hist'

    histid = Column(Integer, primary_key=True, autoincrement=True,
                    unique=True, nullable=False)
    editid = Column(Integer)
    titlehistoryid = Column(Integer)
    masterid = Column(Integer)
    year_start = Column(Integer)
    year_end = Column(Integer)
    vol_start = Column(String)
    vol_end = Column(String)
    publisherid = Column(Integer)
    successor_bibstems = Column(String)
    predecessor_bibstems = Column(String)
    successor_issns = Column(String)
    predecessor_issns = Column(String)
    successor_codens = Column(String)
    predecessor_codens = Column(String)
    notes = Column(Text)
    created = Column(UTCDateTime)
    updated = Column(UTCDateTime)
    superseded = Column(UTCDateTime, default=get_date)

    def __repr__(self):
        return "pubhist_hist.pubhistid='{self.pubhistid}')".format(self=self)


class JournalsRaster(Base):
    __tablename__ = 'raster'

    rasterid = Column(Integer, primary_key=True, autoincrement=True,
                      unique=True, nullable=False)
    masterid = Column(Integer, ForeignKey('master.masterid'),
                       primary_key=True, nullable=False)
    copyrt_file = Column(String, nullable=True)
    pubtype = Column(String, nullable=True)
    bibstem = Column(String, nullable=True)
    abbrev = Column(String, nullable=True)
    width = Column(String, nullable=True)
    height = Column(String, nullable=True)
    embargo = Column(String, nullable=True)
    options = Column(String, nullable=True)
    created = Column(UTCDateTime, default=get_date)
    updated = Column(UTCDateTime, onupdate=get_date)

    def __repr(self):
        return "raster.rasterid='{self.rasterid}'".format(self=self)

    def toJSON(self):
        return{'copyrt_file': self.copyrt_file,
               'pubtype': self.pubtype,
               'bibstem': self.bibstem,
               'abbrev': self.abbrev,
               'width': self.width,
               'height': self.height,
               'embargo': self.embargo,
               'options': self.options}


class JournalsRasterHistory(Base):
    __tablename__ = 'raster_hist'

    histid = Column(Integer, primary_key=True, autoincrement=True,
                    unique=True, nullable=False)
    editid = Column(Integer)
    rasterid = Column(Integer)
    masterid = Column(Integer)
    copyrt_file = Column(String)
    pubtype = Column(String)
    bibstem = Column(String)
    abbrev = Column(String)
    width = Column(String)
    height = Column(String)
    embargo = Column(String)
    options = Column(String)
    created = Column(UTCDateTime)
    updated = Column(UTCDateTime)
    superseded = Column(UTCDateTime, default=get_date)

    def __repr(self):
        return "raster.rasterid='{self.rasterid}'".format(self=self)


class JournalsRasterVolume(Base):
    __tablename__ = 'rastervolume'
    rvolid = Column(Integer, primary_key=True, autoincrement=True,
                    unique=True, nullable=False)
    rasterid = Column(Integer, ForeignKey('raster.rasterid'),
                      primary_key=True, nullable=False)
    volume_number = Column(String, nullable=False)
    volume_properties = Column(Text)
    created = Column(UTCDateTime, default=get_date)
    updated = Column(UTCDateTime, onupdate=get_date)

    def __repr(self):
        return "rastervolume.rvolid='{self.rasterid}'".format(self=self)

    def toJSON(self):
        return {'volume_number': self.volume_number,
                'volume_properties': self.volume_properties}


class JournalsRefSource(Base):
    __tablename__ = 'refsource'

    masterid = Column(Integer, ForeignKey('master.masterid'),
                      primary_key=True, nullable=False)
    refsource_list = Column(Text)
    created = Column(UTCDateTime, default=get_date)

    def __repr__(self):
        return "refsource.masterid='{self.masterid}'".format(self=self)


class JournalsEditControl(Base):
    __tablename__ = 'editcontrol'

    editid = Column(Integer, primary_key=True, autoincrement=True,
                    unique=True, nullable=False)
    tablename = Column(String, nullable=False)
    editstatus = Column(String, nullable=False)
    editfileid = Column(String, nullable=False)
    created = Column(UTCDateTime, default=get_date)
    updated = Column(UTCDateTime, onupdate=get_date)

    def __repr__(self):
        return "editcontrol.editid='{self.editid}'".format(self=self)

from __future__ import absolute_import, unicode_literals
from builtins import str
import csv
import io
import json
import os
from kombu import Queue
from journals import app as app_module
from journals.models import JournalsMaster as master
from journals.models import JournalsMasterHistory as master_hist
from journals.models import JournalsNames as names
from journals.models import JournalsNamesHistory as names_hist
from journals.models import JournalsAbbreviations as abbrevs
from journals.models import JournalsAbbreviationsHistory as abbrevs_hist
from journals.models import JournalsIdentifiers as idents
from journals.models import JournalsIdentifiersHistory as idents_hist
from journals.models import JournalsPublisher as publisher
from journals.models import JournalsPublisherHistory as publisher_hist
from journals.models import JournalsRaster as raster
from journals.models import JournalsRasterHistory as raster_hist
from journals.models import JournalsRasterVolume as rastervol
from journals.models import JournalsRefSource as refsource
from journals.models import JournalsTitleHistory as titlehistory
from journals.models import JournalsTitleHistoryHistory as titlehistory_hist
from journals.models import JournalsEditControl as editctrl
from journals.utils import *
from journals.exceptions import *
from journals.sheetmanager import SpreadsheetManager
import journals.refsource as refsource

TABLES = {'master': master, 'master_hist': master_hist,
          'names': names, 'names_hist': names_hist,
          'abbrevs': abbrevs, 'abbrevs_hist': abbrevs_hist,
          'idents': idents, 'idents_hist': idents_hist,
          'publisher': publisher, 'publisher_hist': publisher_hist,
          'raster': raster, 'raster_hist': raster_hist,
          'titlehistory': titlehistory, 'titlehistory_hist': titlehistory_hist}

TABLE_UNIQID = {'master': 'masterid', 'names': 'nameid', 'abbrevs': 'abbrevid', 'idents': 'identid', 'publisher': 'publisherid', 'titlehistory': 'titlehistoryid', 'raster': 'rasterid', 'rastervol': 'rvolid'}

proj_home = os.path.realpath(os.path.join(os.path.dirname(__file__), '../'))

app = app_module.ADSJournalsCelery('journals', proj_home=proj_home, config=globals().get('config', {}), local_config=globals().get('local_config', {}))
logger = app.logger

app.conf.CELERY_QUEUES = (
    Queue('load-datafiles', app.exchange, routing_key='load-datafiles')
)

@app.task(queue='load-datafiles')
def task_setstatus(idno, status_msg):
    with app.session_scope() as session:
        try:
            update = (session.query(editctrl).filter(editctrl.editid==idno).first())
            update.editstatus = status_msg
            session.commit()
        except Exception as err:
            session.rollback()
            session.flush()
            raise UpdateStatusException(err)

@app.task(queue='load-datafiles')
def task_db_bibstems_to_master(recs):
    pubtypes = {'C': 'Conf. Proc.', 'J': 'Journal', 'R': 'Journal'}
    reftypes = {'C': 'na', 'J': 'no', 'R': 'yes'}
    with app.session_scope() as session:
        extant_bibstems = [x[0] for x in session.query(master.bibstem)]
        if recs:
            for r in recs:
                if r[0] not in extant_bibstems:
                    if r[1] in pubtypes:
                        ptype = pubtypes[r[1]]
                    else:
                        ptype = 'Other'
                    if r[1] in reftypes:
                        rtype = reftypes[r[1]]
                    else:
                        rtype = 'na'
                    session.add(master(bibstem=r[0], journal_name=r[2],
                                               primary_language='en',
                                               pubtype=ptype, refereed=rtype,
                                               defunct=False, not_indexed=False))
                else:
                    logger.debug("task_db_bibstems_to_master: Bibstem %s already in master", r[0])
            try:
                session.commit()
            except Exception as err:
                logger.error("Problem with database commit: %s", err)
                raise DBCommitException("Could not commit to db, stopping now.")

@app.task(queue='load-datafiles')
def task_export_master_to_bibstems():
    with app.session_scope() as session:
        result = session.query(master.bibstem,master.pubtype,master.refereed,master.journal_name).filter_by(not_indexed=False).order_by(master.masterid.asc()).all()
        rows = []
        for r in result:
            (bibstem,pubtype,refereed,pubname) = r
            rows.append({'bibstem': bibstem, 'pubtype': pubtype, 'refereed': refereed, 'pubname':pubname})
        try:
            export_to_bibstemsdat(rows)
        except Exception as err:
            logger.error("Problem exporting master to bibstems.dat: %s" % err)



@app.task(queue='load-datafiles')
def task_db_load_abbrevs(recs):
    with app.session_scope() as session:
        if recs:
            for r in recs:
                try:
                    session.add(abbrevs(masterid=r[0],
                                                      abbreviation=r[1]))
                    session.commit()
                except Exception as err:
                    logger.debug("Problem with abbreviation: %s,%s" %
                                (r[0], r[1]))
        else:
            logger.info("There were no abbreviations to load!")


@app.task(queue='load-datafiles')
def task_db_load_issn(recs):
    with app.session_scope() as session:
        if recs:
            for r in recs:
                try:
                    session.add(idents(masterid=r[0],
                                                    id_type='ISSN',
                                                    id_value=r[1]))
                    session.commit()
                except Exception as err:
                    logger.debug("Duplicate ISSN ident skipped: %s,%s" %
                                (r[0], r[1]))
                    session.rollback()
                    session.flush()
        else:
            logger.info("There were no ISSNs to load!")


@app.task(queue='load-datafiles')
def task_db_load_xref(recs):
    with app.session_scope() as session:
        if recs:
            for r in recs:
                try:
                    session.add(idents(masterid=r[0],
                                                    id_type='CROSSREF',
                                                    id_value=r[1]))
                    session.commit()
                except Exception as err:
                    logger.debug("Duplicate XREF ident skipped: %s,%s" %
                                (r[0], r[1]))
                    session.rollback()
                    session.flush()
        else:
            logger.info("There were no XREF IDs to load!")


@app.task(queue='load-datafiles')
def task_db_load_publisher(recs):
    with app.session_scope() as session:
        if recs:
            for r in recs:
                try:
                    session.add(publisher(masterid=r[0], pubname=r[1],
                                                  puburl=r[2]))
                    session.commit()
                except Exception as err:
                    logger.debug("Duplicate XREF ident skipped: %s,%s" %
                                (r[0], r[1]))
                    session.rollback()
                    session.flush()
        else:
            logger.info("There were no publishers to load!")


@app.task(queue='load-datafiles')
def task_db_load_raster(recs):
    with app.session_scope() as session:
        if recs:
            for r in recs:
                if 'label' in r[1]:
                    copyrt_file = r[1]['label']
                else:
                    copyrt_file = ''
                if 'pubtype' in r[1]:
                    pubtype = r[1]['pubtype']
                else:
                    pubtype = ''
                if 'bibstem' in r[1]:
                    bibstem = r[1]['bibstem']
                else:
                    bibstem = ''
                if 'abbrev' in r[1]:
                    abbrev = r[1]['abbrev']
                else:
                    abbrev = ''
                if 'width' in r[1]:
                    width = r[1]['width']
                else:
                    width = ''
                if 'height' in r[1]:
                    height = r[1]['height']
                else:
                    height = ''
                if 'embargo' in r[1]:
                    embargo = r[1]['embargo']
                else:
                    embargo = ''
                if 'options' in r[1]:
                    options = r[1]['options']
                else:
                    options = ''

                try:
                    session.add(raster(masterid=r[0],
                                       copyrt_file=copyrt_file,
                                       pubtype=pubtype,
                                       bibstem=bibstem,
                                       abbrev=abbrev,
                                       width=width,
                                       height=height,
                                       embargo=embargo,
                                       options=options))
                    session.commit()
                    result = session.query(raster.rasterid).filter_by(masterid=r[0]).first()
                except Exception as err:
                    result = None
                    logger.debug("Cant load raster data for (%s, %s): %s" %
                                (r[0], bibstem, err))
                    session.rollback()
                    session.flush()
                try:
                    r[1]['rastervol']
                except Exception as err:
                    result = None
                else:
                    if result:
                        try:
                            for v in r[1]['rastervol']:
                                session.add(rastervol(rasterid=result,
                                                      volume_number=v['range'],
                                                      volume_properties=json.dumps(v['param'])))
                                session.commit()
                        except Exception as err:
                            logger.debug("Cant load rastervolume data for %s: %s" %
                                        (result, err))
                            session.rollback()
                            session.flush()
        else:
            logger.info("There were no raster configs to load!")



@app.task(queue='load-datafiles')
def task_db_get_bibstem_masterid():
    dictionary = {}
    with app.session_scope() as session:
        try:
            for record in session.query(master.masterid,
                                        master.bibstem):
                dictionary[record.bibstem] = record.masterid
        except Exception as err:
            logger.error("Error: failed to read bibstem-masterid dict from table master")
            raise DBReadException("Could not read from database!")
    return dictionary


@app.task(queue='load-datafiles')
def task_db_load_refsource(masterid, refsource):
    with app.session_scope() as session:
        if masterid and refsource:
            try:
                refsource = json.dumps(refsource.toJSON())
                session.add(refsource(masterid=masterid,
                                              refsource_list=refsource))
                session.commit()
            except Exception as err:
                logger.debug("Error adding refsources for %s: %s" %
                               (masterid, err))
                session.rollback()
                session.commit()
        else:
            logger.error("No refsource data to load!")
    return

def task_export_table_data(tablename):
    try:
        with app.session_scope() as session:
            data = io.StringIO()
            csvout = csv.writer(data, quoting=csv.QUOTE_NONNUMERIC)

            if tablename == 'master':
                csvout.writerow(('masterid','bibstem','journal_name','primary_language','multilingual','defunct','pubtype','refereed','collection','notes','not_indexed'))
                results = session.query(master.masterid, master.bibstem, master.journal_name, master.primary_language, master.multilingual, master.defunct, master.pubtype, master.refereed, master.collection, master.notes, master.not_indexed).order_by(master.masterid.asc()).all()

            elif tablename == 'names':
                csvout.writerow(('nameid','masterid','bibstem','name_english_translated','title_language','name_native_language','name_normalized'))
                results = session.query(names.nameid, names.masterid, master.bibstem, names.name_english_translated, names.title_language, names.name_native_language, names.name_normalized).join(master, names.masterid == master.masterid).order_by(names.masterid.asc()).all()

            elif tablename == 'idents':
                csvout.writerow(('identid','masterid','bibstem','id_type','id_value'))
                results = session.query(idents.identid, idents.masterid, master.bibstem, idents.id_type, idents.id_value).join(master, idents.masterid == master.masterid).order_by(idents.masterid.asc()).all()

            elif tablename == 'abbrevs':
                csvout.writerow(('abbrevid','masterid','bibstem','abbreviation'))
                results = session.query(abbrevs.abbrevid, abbrevs.masterid, master.bibstem, abbrevs.abbreviation).join(master, abbrevs.masterid == master.masterid).order_by(abbrevs.masterid.asc()).all()

            elif tablename == 'publisher':
                csvout.writerow(('publisherid','pubname','pubaddress','pubcontact','puburl','pubextid','notes'))
                results = session.query(publisher.publisherid, publisher.pubname, publisher.pubaddress, publisher.pubcontact, publisher.puburl, publisher.pubextid, publisher.notes).order_by(publisher.publisherid.asc()).all()

            elif tablename == 'titlehistory':
                csvout.writerow(('titlehistoryid','masterid','bibstem','year_start','year_end','complete','publisherid','predecessorid','successorid','notes'))
                results = session.query(titlehistory.statusid, titlehistory.masterid, master.bibstem, titlehistory.year_start, titlehistory.year_end, titlehistory.complete, titlehistory.publisherid, titlehistory.successor_masterid, titlehistory.notes).join(master, titlehistory.masterid == master.masterid).order_by(titlehistory.masterid.asc()).all()

            else:
                results = []

            for rec in results:
                csvout.writerow(rec)

    except Exception as err:
        return
    else:
        return data.getvalue()

def task_checkout_table(tablename):

    if tablename.lower() not in app.conf.EDITABLE_TABLES:
        raise InvalidTableException("Tablename %s is not valid" % tablename)

    try:
        with app.session_scope() as session:
            table_record = session.query(editctrl).filter(editctrl.tablename.ilike(tablename), editctrl.editstatus=='active').first()

            if table_record:
                sheet = SpreadsheetManager(creds=app.conf.CREDENTIALS_FILE, token=app.conf.TOKEN_FILE, folderid=app.conf.HOME_FOLDER_ID, editors=app.conf.EDITORS, sheetid=table_record.editfileid)
                logger.debug("Table %s is already checked out: Time: %s, ID: %s" % (tablename, table_record.created, table_record.editfileid))

            else:
                sheet = SpreadsheetManager(creds=app.conf.CREDENTIALS_FILE, token=app.conf.TOKEN_FILE, folderid=app.conf.HOME_FOLDER_ID, editors=app.conf.EDITORS)
                sheet.create_sheet(title=tablename, folderid=app.conf.HOME_FOLDER_ID)
                session.add(editctrl(tablename=tablename, editstatus='active', editfileid=sheet.sheetid))
                session.commit()

                try:
                    data = task_export_table_data(tablename)
                    sheet.write_table(sheetid=sheet.sheetid, data=data, tablename=tablename, encoding='utf-8')
                except Exception as err:
                    raise WriteDataToSheetException(err)

    except Exception as err:
        raise TableCheckoutException("Error checking out table %s: %s" % (tablename, err))


def task_checkin_table(tablename, masterdict, delete_flag=False):

    if tablename.lower() not in app.conf.EDITABLE_TABLES:
        raise InvalidTableException("Tablename %s is not valid" % tablename)

    try:
        with app.session_scope() as session:
            table_record = session.query(editctrl).filter(editctrl.tablename.ilike(tablename), editctrl.editstatus=='active').first()

            if table_record:
                sheet = SpreadsheetManager(creds=app.conf.CREDENTIALS_FILE, token=app.conf.TOKEN_FILE, folderid=app.conf.HOME_FOLDER_ID, editors=app.conf.EDITORS, sheetid=table_record.editfileid)
                logger.debug("Table %s is currently checked out: Time: %s, ID: %s" % (tablename, table_record.created, table_record.editfileid))

                data = sheet.fetch_table()
                checkin = {'tablename': tablename,
                           'editid': table_record.editid,
                           'data': data
                          }
                try:
                    status = task_update_table(checkin, masterdict)
                except Exception as err:
                    raise FatalCheckinException(err)
                else:
                    task_setstatus(editid, status)


            else:
                logger.debug("Table %s is not checked out." % tablename)

    except Exception as err:
        raise TableCheckinException("Error checking in table %s: %s" % (tablename, err))


def task_update_table(checkin, masterdict):
    try:
        tablename = checkin['tablename']
        editid = checkin['editid']
        checkin_data = checkin['data']
        create = list()
        modify = list()
        discard = list()
        failure = list()
        with app.session_scope() as session:
            t = TABLES[tablename]
            tk = TABLE_UNIQID[tablename]
            for row in checkin_data:
                keyval = row.get(tk, -1)
                try:
                    q = session.query(t).filter(t.__table__.c[tk]==keyval).all()
                    if len(q) == 1:
                        # this is what you want an existing record to be
                        # r is what you're going to modify and update,
                        # s is what you're going to put into _hist.
                        r = q[0]
                        update = 0
                        old_rowdat = {}
                        for k in r.__table__.columns.keys():
                            old_rowdat[k] = getattr(r,k)
                        for k,v in row.items():
                            try:
                                if k != tk and v != getattr(r,k):
                                    update += 1
                                    setattr(r,k,v)
                            except Exception as noop:
                                # unset columns in a returned row may get here,
                                # but that's ok in most cases.
                                pass
                        if update > 0:
                            # this commits changes made to r
                            session.commit()
                            # insert the original record into modify list
                            # to be written to _hist
                            modify.append(old_rowdat)
                        else:
                            discard.append(row)
                    elif len(q) == 0:
                        # this is what you want a new record to be
                        create.append(row)
                    else:
                        # this means you have two or more records with the
                        # same key which should not happen unless you're
                        # adding a record to a table that already exists with
                        # the same key.
                        failure.append(row)
                except Exception as err:
                    # something really fundamentally bad happened while 
                    # handling this...
                    failure.append(row)

                # create new records
            for r in create:
                try:
                    data = t()
                    try:
                        new_masterid = r['masterid']
                        new_bibstem = r['bibstem'] 
                        if masterdict[new_bibstem]:
                            if r['masterid'] == '' or r['masterid'] == None:
                                r['masterid'] = masterdict[new_bibstem]
                    except Exception as noop:
                        # masterid is not a key in this table, no worries
                        pass
                    for k,v in r.items():
                        if v == '':
                            v = None
                        setattr(data, k, v)
                    session.add(data)
                    session.commit()
                except Exception as err:
                    logger.warning('problem with commit: %s' % err)
                    failure.append(r)
                    session.rollback()
                    session.flush()

            # add modified records to the history table
            for s in modify:
                try:
                    thist = tablename + '_hist'
                    tb = TABLES[thist]
                    data = tb()
                    for k, v in s.items():
                        setattr(data, k, s[k])
                    setattr(data, 'editid', editid)
                    session.add(data)
                    session.commit()
                except Exception as err:
                    logger.warning('problem with commit: %s' % err)
                    failure.append(s)
                    session.rollback()
                    session.flush()

            logger.info('Total records from sheet: %s New; %s Updates; %s Ignored; %s Problematic' % (len(create), len(modify), len(discard), len(failure)))

            if len(failure) != 0:
                # IN PROGRESS: you need to do something more useful than
                # just flagging the checkin as failed in editcontrol.  Send
                # failed rows to file or logger in such a way that they can
                # be examined and fixed with a new checkout/checkin
                return 'failed'
            else:
                return 'completed'

    except Exception as err:
        raise UpdateTableException(err)
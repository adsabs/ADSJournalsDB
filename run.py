'''
No.
'''
from __future__ import print_function
import argparse
import json
import os
from adsputils import setup_logging, load_config
from journals import tasks
from journals import utils

proj_home = os.path.realpath(os.path.dirname(__file__))
config = load_config(proj_home=proj_home)
logger = setup_logging('run.py', proj_home=proj_home,
                       level=config.get('LOGGING_LEVEL', 'INFO'),
                       attach_stdout=config.get('LOG_STDOUT', False))



def get_arguments():
    '''
    No.
    '''

    parser = argparse.ArgumentParser(description='Command line options.')

    parser.add_argument('-lm',
                        '--load-master',
                        dest='load_master',
                        action='store_true',
                        help='Load master list of bibstems')

    parser.add_argument('-la',
                        '--load-abbrevs',
                        dest='load_abbrevs',
                        action='store_true',
                        help='Load list of journal name abbreviations')

    parser.add_argument('-lc',
                        '--load-completeness',
                        dest='load_compl',
                        action='store_true',
                        help='Load completeness .csv files')

    parser.add_argument('-li',
                        '--load-issn',
                        dest='load_issn',
                        action='store_true',
                        help='Load journal_issn')

    parser.add_argument('-lr',
                        '--load-rasterconf',
                        dest='load_raster',
                        action='store_true',
                        help='Load rasterization control parameters')

    parser.add_argument('-ls',
                        '--load-refsources',
                        dest='load_refsources',
                        action='store_true',
                        help='Load refsources from citing2file.dat')

    parser.add_argument('-xi',
                        '--checkin-table',
                        dest='checkin_table',
                        action='store',
                        default=None,
                        help='Check IN table TABLE from GSheets')

    parser.add_argument('-xo',
                        '--checkout-table',
                        dest='checkout_table',
                        action='store',
                        default=None,
                        help='Check OUT table TABLE to GSheets')

    parser.add_argument('-db',
                        '--dump-bibstems',
                        dest='dump_bibstems',
                        action='store_true',
                        help='Dump master to bibstems.dat.NEW')

    parser.add_argument('-xd',
                        '--delete-checkin-sheet',
                        dest='delete_flag',
                        action='store_true',
                        default=False,
                        help='Delete checked-in sheet from Google')

    args = parser.parse_args()
    return args


def load_master_table():
    '''
    No.
    '''
    bibstems = utils.read_bibstems_list()
    recs = []
    for key, value in list(bibstems.items()):
        bibstem = key
        pubtype = value['type']
        journal_name = value['pubname']
        recs.append((bibstem, pubtype, journal_name))
    if recs:
        logger.debug("Inserting %s bibstems into Master", len(recs))
        tasks.task_db_bibstems_to_master(recs)
    else:
        logger.debug("No bibstems to insert")
    return


def load_rasterconfig(masterdict):
    '''
    No.
    '''
    try:
        recsr = utils.read_raster_xml(masterdict)
    except Exception as e:
        logger.warning('error in utils.read_raster_xml: %s' % e)
    else:
        logger.debug("Inserting %s raster config records" % len(recsr))
        try:
            tasks.task_db_load_raster(recsr)
        except Exception as err:
            logger.warning("Could not load raster config: %s" % err)
    return


def load_abbreviations(masterdict):
    '''
    No.
    '''
    abbrevs = utils.read_abbreviations_list()
    recs = []
    for key, value in list(abbrevs.items()):
        try:
            if key in masterdict:
                logger.debug("Got masterid for bibstem %s", key)
                masterid = masterdict[key]
                for attrib in value:
                    recs.append((masterid, attrib))
            else:
                logger.debug("No masterid for bibstem %s", key)
        except Exception as err:
            logger.warning("Error with bibstem %s", key)
            logger.warning("Error: %s", err)
    if recs:
        logger.debug("Inserting %s abbreviations into Abbreviations",
                     len(recs))
        try:
            tasks.task_db_load_abbrevs(recs)
        except Exception as err:
            logger.warning("Could not load abbreviations: %s" % err)
    else:
        logger.debug("There are no abbreviations to load.")
    return


def load_completeness(masterdict):
    '''
    No.
    '''
    pub_dict = utils.read_complete_csvs()
    recsi = []
    recsx = []
    recsp = []
    for key, value in list(pub_dict.items()):
        try:
            if key in masterdict:
                logger.debug("Got masterid for bibstem %s", key)
                mid = masterdict[key]
                c = value['startyear']
                d = value['startvol']
                e = value['endvol']
                f = value['complete']
                g = value['comporig']
                i = value['scanned']
                j = value['online']
                if value['issn'] != '':
                    recsi.append((mid, value['issn']))
                if value['xref'] != '':
                    recsx.append((mid, value['xref']))
                if value['publisher'] != '':
                    recsp.append((mid, value['publisher'], value['url']))

            else:
                logger.debug("No mid for bibstem %s", key)
        except Exception as err:
            logger.warning("Error with bibstem %s", key)
            logger.warning("Error: %s", err)
    if recsi:
        tasks.task_db_load_issn(recsi)
    if recsx:
        tasks.task_db_load_xref(recsx)
    if recsp:
        tasks.task_db_load_publisher(recsp)
    return


def load_refsources(masterdict):
    refsources = utils.create_refsource()
    missing_stems = []
    loaded_stems = []

    if refsources:

        for bibstem, refsource in refsources.items():
            try:
                bibstem = bibstem.rstrip('.')
                masterid = masterdict[bibstem]
            except Exception as err:
                logger.debug("missing masterdict bibstem: (%s)" % bibstem)
                missing_stems.append(bibstem)
            else:
                tasks.task_db_load_refsource(masterid,refsource)
                loaded_stems.append(bibstem)

        logger.debug("Loaded bibstems: %s\tMissing bibstems: %s" % (len(loaded_stems), len(missing_stems)))

    return


def load_issn(masterdict):
    try:
        issn_dict = utils.read_issn_file()
        recsif = []
        for k, v in issn_dict.items():
            try:
                mid = masterdict[k]
                recsif.append((mid, v))
            except Exception as noop:
                # print("bibstem %s is not in masterdict, skipping" % k)
                pass
        if len(recsi) != len(issn_dict.keys()):
            logger.warning("Lines were skipped when reading ISSNs from file")
        if recsi:
            tasks.task_db_upsert_issn(recsi)
    except Exception as err:
        logger.error("Failed to load ISSNs from %s: %s" % (config.get('JOURNAL_ISSN_FILE', None), err))

    return


def checkin_table(tablename, masterdict, delete_flag):
    try:
        result = tasks.task_checkin_table(tablename, masterdict, delete_flag=delete_flag)
    except Exception as err:
        logger.warning("Unable to checkin table %s: %s" % (tablename, err))
        return
    else:
        logger.warning("Table %s successfully checked in from Sheets" % tablename)
        return result

def checkout_table(tablename):
    try:
        result = tasks.task_checkout_table(tablename)
    except Exception as err:
        logger.warning("Unable to checkout table %s: %s" % (tablename, err))
        return
    else:
        logger.warning("Table %s is available in Sheets" % tablename)
        return result

def main():
    '''
    No.
    '''

    args = get_arguments()

    # if args.load_master == True:
    # create the set of bibcode-journal name pairs and assign them UIDs;
    # these UIDs will be used as foreign keys in all other tables, so
    # if this fails, you're dead in the water.
    if args.load_master:
        load_master_table()

    # none of the other loaders will work unless you have data in
    # journals.master, so try to load it
    try:
        masterdict = tasks.task_db_get_bibstem_masterid()
        logger.debug("masterdict has %s records", len(masterdict))
    except Exception as err:
        logger.warning("Error reading master table bibstem-masterid mapping: %s", err)
    else:
        # load bibstem-journal name abbreviation pairs
        if args.load_abbrevs:
            load_abbreviations(masterdict)

        if args.load_compl:
            # completeness data
            load_completeness(masterdict)

        if args.load_raster:
            load_rasterconfig(masterdict)

        if args.load_refsources:
            load_refsources(masterdict)

        if args.load_issn:
            load_issn(masterdict)

        if args.checkin_table:
            result = checkin_table(args.checkin_table, masterdict, args.delete_flag)
        
    if args.checkout_table:
        result = checkout_table(args.checkout_table)

    if args.dump_bibstems:
        tasks.task_export_master_to_bibstems()


if __name__ == '__main__':
    main()

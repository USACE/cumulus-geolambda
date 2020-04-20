import argparse
import datetime
import logging
import os
import sys
import tempfile
from timeit import default_timer as timer

from .process import process_snodas_for_date

if __name__ == '__main__':

    start = timer()

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--date', nargs=1, required=True,
                        help='Date string in format YYYYMMDD (example: 20190101)')
    parser.add_argument('--infile-type', required=True, choices=['masked', 'unmasked', ])
    parser.add_argument('--outdir', default=None,
                        help='Output directory to save files. Only required if saving to local filesystem')
    parser.add_argument('--post-to-cumulus', action='store_true',
                        help='Flag to post files to Cumulus database after processing')
    parser.add_argument('--loglevel', default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help="Logging level")
    args = parser.parse_args()

    # Configure logger
    logging.basicConfig(level=args.loglevel, format='%(asctime)s; %(levelname)s; %(message)s')

    # Catch bad dates passed on the command-line (i.e. January 32nd: 20190132)
    try:
        # Datetime represented by grids
        dt = datetime.datetime.strptime(args.date[0], '%Y%m%d')
    except:
        logging.critical('Could not parse supplied date argument: {}'.format(args.date[0]))
        sys.exit(1)

    # If Output Directory is not explictly provided, work in a temporary directory with automatic file cleanup
    # Otherwise, write output files in the explicitly provided directory.
    if args.outdir == None:
        # Process files in a temporary directory
        outdir = tempfile.TemporaryDirectory(prefix='snodas_', ).name
    else:
        # Process files in directory supplied on commandline
        outdir = os.path.abspath(args.outdir)
        # ... Ensure directory exists
        mkdir_p(outdir)

    # Process SNODAS files and return directory to processed files
    processed_files = process_snodas_for_date(dt, args.infile_type, outdir)

    # Post to Cumulus API
    if args.post_to_cumulus:
        # All datetimes for daily SNODAS files are at 0600.
        productfile_datetime = dt + datetime.timedelta(hours=6)

        logging.info('Post files to cumulus')
        for productname, productfile in processed_files['cog'].items():
            logging.debug('POST: {}; {}'.format(productname, productfile))
            post_to_cumulus(productname, productfile, productfile_datetime)

    finish = timer()

    logging.info('Done in: {} seconds'.format(finish - start))

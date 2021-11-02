#!/usr/bin/env python

import io
import sys
import timeit
import argparse
import traceback
import logging
import os

try:
    from . import FastSpell
except ImportError:
    import FastSpell    


__author__ = "Marta Bañón"
__version__ = "Version 0.1 # 01/07/2021 # Initial release # Marta Bañón"
__version__ = "Version 0.1.1 # 01/07/2021 # More flexible management of paths and imports # Marta Bañón"
__version__ = "Version 0.2 # 25/10/2021 # Removed tokenization # Marta Bañón"


def logging_setup(args = None):
    logger = logging.getLogger()
    logger.handlers = [] # Removing default handler to avoid duplication of log messages
    logger.setLevel(logging.ERROR)
    
    h = logging.StreamHandler(sys.stderr)
    if args != None:
       h = logging.StreamHandler(args.logfile)
      
    h.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(h)

    logger.setLevel(logging.INFO)
    
    if args != None:
        if not args.quiet:
            logger.setLevel(logging.INFO)
        if args.debug:
            logger.setLevel(logging.DEBUG)
            
            

def initialization():
    parser = argparse.ArgumentParser(prog=os.path.basename(sys.argv[0]), formatter_class=argparse.ArgumentDefaultsHelpFormatter, description=__doc__)
    parser.add_argument('lang', type=str)
    parser.add_argument('input',  nargs='?', type=argparse.FileType('rt', errors="replace"), default=io.TextIOWrapper(sys.stdin.buffer, errors="replace"),  help="Input sentences.")
    parser.add_argument('output', nargs='?', type=argparse.FileType('wt'), default=sys.stdout, help="Output of the language identification.")
    
    parser.add_argument('--aggr', action='store_true', help='Aggressive strategy (more positives)')
    parser.add_argument('--cons', action='store_true',  help='Conservative strategy (less positives)')
    
    groupL = parser.add_argument_group('Logging')
    groupL.add_argument('-q', '--quiet', action='store_true', help='Silent logging mode')
    groupL.add_argument('--debug', action='store_true', help='Debug logging mode')
    groupL.add_argument('--logfile', type=argparse.FileType('a'), default=sys.stderr, help="Store log to a file")
    groupL.add_argument('-v', '--version', action='version', version="%(prog)s " + __version__, help="show version of this script and exit")
        
    args = parser.parse_args()
    logging_setup(args)
    
    if args.aggr == args.cons:
        #both are true or both are false
        logging.error("Please provide  --aggr or --cons")
        exit(1)
    return args




def perform_identification(args):

    time_start = timeit.default_timer()
    if args.aggr:
        mode="aggr"
    if args.cons:
        mode="cons"
        
    fs = FastSpell.FastSpell(args.lang, mode=mode)
    
    for line in args.input:        
        lident = fs.getlang(line)
        args.output.write(line.strip()+"\t"+lident+"\n")
        
    end_time = timeit.default_timer()
    logging.info("Elapsed time: {}".format(end_time - time_start))     
         



def main(args):
    logging.info("Executing main program...")
    perform_identification(args)
    logging.info("Program finished")

if __name__ == '__main__':
    try:
        logging_setup()
        args = initialization() # Parsing parameters
        main(args)  # Running main program
    except Exception as ex:
        tb = traceback.format_exc()
        logging.error(tb)
        sys.exit(1)
#!/usr/bin/env python
import os
import io
import sys
import yaml
import fasttext
import hunspell
import logging
import urllib.request
import pathlib
import timeit
import argparse
import traceback
import logging

try:
    from .util import logging_setup, remove_unwanted_words, get_hash
except ImportError:
    from util import logging_setup, remove_unwanted_words, get_hash

__author__ = "Marta Bañón"
__version__ = "Version 0.1 # 01/07/2021 # Initial release # Marta Bañón"
__version__ = "Version 0.1.1 # 01/07/2021 # More flexible management of paths and imports # Marta Bañón"
__version__ = "Version 0.2 # 25/10/2021 # Removed tokenization # Marta Bañón"
__version__ = "Version 0.3 # 14/11/2022 # Serbo-Croatian mode # Jaume Zaragoza"
__version__ = "Version 0.4 # 15/11/2022 # Serbo-Croatian script detection # Jaume Zaragoza"

fasttext.FastText.eprint = lambda x: None

HBS_LANGS = ('hbs', 'sh', 'bs', 'sr', 'hr', 'me')


def initialization():
    parser = argparse.ArgumentParser(prog=os.path.basename(sys.argv[0]), formatter_class=argparse.ArgumentDefaultsHelpFormatter, description=__doc__)
    parser.add_argument('lang', type=str)
    parser.add_argument('input',  nargs='?', type=argparse.FileType('rt', errors="replace"), default=io.TextIOWrapper(sys.stdin.buffer, errors="replace"),  help="Input sentences.")
    parser.add_argument('output', nargs='?', type=argparse.FileType('wt'), default=sys.stdout, help="Output of the language identification.")
    
    parser.add_argument('--aggr', action='store_true', help='Aggressive strategy (more positives)')
    parser.add_argument('--cons', action='store_true',  help='Conservative strategy (less positives)')
    parser.add_argument('--hbs', action='store_true',  help="Tag all Serbo-Croatian variants as 'hbs'")
    parser.add_argument('--script', action='store_true',  help="Detect writing script (currently only Serbo-Croatian is supported)")
    
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

    if args.script and args.lang not in HBS_LANGS:
        logging.warning("Script detection is only supported with Serbo-Croatian")

    return args

class FastSpell:
    
    threshold = 0.25 #Hunspell max error rate allowed in a sentence
    prefix = "__label__" #FastText returns langs labeled as __label__LANGCODE
    ft_model_hash = "01810bc59c6a3d2b79c79e6336612f65"
    
    #load config
    cur_path = os.path.dirname(__file__)
    config_path = cur_path + "/config/"
    #similar languages
    similar_yaml_file = open(config_path+"similar.yaml")
    similar_langs = yaml.safe_load(similar_yaml_file)["similar"]


    #hunspell 
    hunspell_codes_file = open(config_path+"hunspell.yaml")
    hunspell_config = yaml.safe_load(hunspell_codes_file) 
    hunspell_codes = hunspell_config["hunspell_codes"]
    if os.path.isabs(hunspell_config["dictpath"]):
        dictpath = hunspell_config["dictpath"]
    else:    
        dictpath = os.path.join(config_path, hunspell_config["dictpath"])


 
    hunspell_objs = {}

    #tokenizers={}

    def __init__(self, lang, mode="cons", hbs=False, script=False):
        assert (mode=="cons" or mode=="aggr"), "Unknown mode. Use 'aggr' for aggressive or 'cons' for conservative"

        self.lang = lang
        self.mode = mode
        self.hbs = hbs
        self.script = script
        
        ft_model_path = os.path.join(self.cur_path, "lid.176.bin") #The model should be in the same directory
        
        hash = get_hash(ft_model_path)
        if hash == self.ft_model_hash:
            self.model = fasttext.load_model(ft_model_path)  #FastText model
        else:
            logging.warning("Downloading FastText model...")
            urllib.request.urlretrieve("https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin", ft_model_path)
            self.model = fasttext.load_model(ft_model_path) 

        self.similar = self.similar_langs.get(lang)

        #If there are languages that can be mistaken 
        #with the target language: prepare an array of Hunspell spellcheckers
        #for all the similar languages
        if self.similar != None:            
            for l in self.similar:
                #load dicts
                try:
                    dict = self.dictpath+self.hunspell_codes.get(l)
                    hunspell_obj = hunspell.HunSpell(dict+'.dic', dict+'.aff') 
                    self.hunspell_objs[l] = hunspell_obj
                except hunspell.HunSpellError:
                    logging.error("Failed building Hunspell object for "+l)
                    logging.error("Please check that " + dict+".dic" + " and " + dict+'.aff' + " do exist.")
                    logging.error("Aborting.") 
                    exit(1)

        # Crate translate tables for script detection
        if script:
            self.script_tables = {
                'hbs_lat': str.maketrans('', '', 'aAbBcčČćĆdDđĐeEfFgGhHiIjJkKlLmMnNoOpPrRsSšŠtuUvVzZžŽ'),
                'hbs_cyr': str.maketrans('', '', 'АаБбВвГгДддЂђЕеЖжЗзИиЙйКкkЛлЉљМмНнЊњОоПпРрЋћТтУуФфХхЦцЧчШшЩщ'),
            }

    def getscript(self, sent):
        # Return as detected script the one that its translate table
        # deletes more characters
        best_count = sys.maxsize
        best_script = None
        for script in self.script_tables.keys():
            count_chars = len(sent.translate(self.script_tables[script]))
            if count_chars < best_count:
                best_count = count_chars
                best_script = script

        return best_script


    def getlang(self, sent):
        
        sent=sent.replace("\n", " ").strip()
        prediction = self.model.predict(sent, k=1)[0][0][len(self.prefix):]

        # Return 'hbs' for all serbo-croatian variants
        # if hbs mode is enabled or hbs is the requested language
        if (self.hbs or self.lang == 'hbs') and prediction in HBS_LANGS:
            if self.script:
                return self.getscript(sent)
            return 'hbs'

        #classic norwegian ñapa
        if prediction == "no":
            prediction = "nb"
        #New serbo-croatian ñapa    
        if prediction == "sh":
            prediction = "sr"
            
        #TODO: Confidence score?

        if self.similar == None or prediction not in self.similar:
        #Non mistakeable language: just return FastText prediction
            return(prediction)
        else:
        #The target language is mistakeable
            spellchecked = {}
            for l in self.hunspell_objs:
                #Get spellchecking for all the mistakeable languages
                logging.debug(l)
                dec_sent = sent.encode(encoding='UTF-8',errors='strict').decode('UTF-8') #Not 100% sure about this...
                raw_toks = sent.strip().split(" ")
                toks = remove_unwanted_words(raw_toks, self.lang)
                try:
                    correct_list = list(map(self.hunspell_objs.get(l).spell, toks))
                except UnicodeEncodeError: #...because it sometimes fails here for certain characters
                    correct_list = []
                corrects = sum(correct_list*1)
                logging.debug("Tokens: " +str(toks))
                logging.debug("Corrects: " + str(correct_list))
                logging.debug("Total: " + str(len(toks)))
                if corrects > 0:
                    error_rate = 1-(corrects/len(toks))
                else:
                    error_rate = 1
                logging.debug("error_rate: " + str(error_rate))
                if error_rate < self.threshold: #we don't keep it if the error rate is above the threshold
                    spellchecked[l] =  error_rate
                logging.debug("----------------")

            if len(spellchecked) > 0:
                #at least one of the spellchecks was below the threshold            
                #get best values and keys
                best_value = min(spellchecked.values())
                best_keys = [k for k, v in spellchecked.items() if v == best_value]
                if len(best_keys)==1:
                    #Only one language scoring the best
                    return(best_keys[0])
                else:
                    #It's a tie!
                    if self.mode == "aggr":
                        #Aggressive approach: if the targetted language is among the best scoring, take it
                        if self.lang in best_keys:
                            return(self.lang)
                        elif prediction in best_keys:
                            #the targetted language is not in the best ones, and the prediction?
                            return(prediction)
                        else:
                            #Just take one
                            return(best_keys[0])
                    if self.mode == "cons":
                        #Conservative: just keep it as unknown
                        return("unk")
            else:
                #Nothing in the spellchecking list
                if self.mode == "aggr":
                    return(prediction)
                else:
                    return("unk")

def perform_identification(args):
    time_start = timeit.default_timer()
    if args.aggr:
        mode="aggr"
    if args.cons:
        mode="cons"
        
    fs = FastSpell(args.lang, mode=mode, hbs=args.hbs, script=args.script)
    
    for line in args.input:        
        lident = fs.getlang(line)
        args.output.write(line.strip()+"\t"+lident+"\n")
        
    end_time = timeit.default_timer()
    logging.info("Elapsed time: {}".format(end_time - time_start))


def main():
    logging_setup()
    args = initialization() # Parsing parameters
    logging.info("Executing main program...")
    perform_identification(args)
    logging.info("Program finished")

if __name__ == '__main__':
    main()

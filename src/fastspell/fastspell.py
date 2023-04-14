#!/usr/bin/env python
import os
import io
import sys
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
    from . import __version__
    from .util import logging_setup, remove_unwanted_words, get_hash, check_dir, load_config
except ImportError:
    from fastspell import __version__
    from util import logging_setup, remove_unwanted_words, get_hash, check_dir, load_config

fasttext.FastText.eprint = lambda x: None

HBS_LANGS = ('hbs', 'sh', 'bs', 'sr', 'hr', 'me')


def initialization():
    parser = argparse.ArgumentParser(prog=os.path.basename(sys.argv[0]), formatter_class=argparse.ArgumentDefaultsHelpFormatter, description=__doc__)
    parser.add_argument('lang', type=str)
    parser.add_argument('input',  nargs='?', type=argparse.FileType('rt', errors="replace"), default=io.TextIOWrapper(sys.stdin.buffer, errors="replace"),  help="Input sentences.")
    parser.add_argument('output', nargs='?', type=argparse.FileType('wt'), default=sys.stdout, help="Output of the language identification.")

    parser.add_argument('-c', '--config_path', default=None, type=check_dir, help="Alternative config path. Must contain 'hunspell.yaml' and 'similar.yaml'.")
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
    ft_download_url = "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin"


    def __init__(self, lang, config_path=None, download_dics=False,
                 mode="cons", hbs=False, script=False):
        assert (mode=="cons" or mode=="aggr"), "Unknown mode. Use 'aggr' for aggressive or 'cons' for conservative"

        self.lang = lang
        self.mode = mode
        self.hbs = hbs
        self.script = script

        self.cur_path = os.path.dirname(__file__)
        self.download_fasttext()
        config = load_config(config_path)
        self.similar_langs, self.hunspell_codes, self.hunspell_paths = config
        self.load_scripts()
        self.load_hunspell_dicts()


    def download_fasttext(self):
        ''' Download and check integrity of FastText model '''
        ft_model_path = os.path.join(self.cur_path, "lid.176.bin") #The model should be in the same directory
        hash = get_hash(ft_model_path)
        if hash == self.ft_model_hash:
            self.model = fasttext.load_model(ft_model_path)  #FastText model
        else:
            logging.warning("Downloading FastText model...")
            urllib.request.urlretrieve(self.ft_download_url, ft_model_path)
            self.model = fasttext.load_model(ft_model_path)


    def search_hunspell_dict(self, lang_code):
        ''' Search in the paths for a hunspell dictionary and load it '''
        for p in self.hunspell_paths:
            if os.path.exists(f"{p}/{lang_code}.dic") and os.path.exists(f"{p}/{lang_code}.aff"):
                try:
                    dicpath = p + '/' + lang_code
                    hunspell_obj = hunspell.Hunspell(lang_code, hunspell_data_dir=p)
                    logging.debug(f"Loaded hunspell obj for '{lang_code}' in path: {dicpath}")
                    break
                except:
                    logging.error("Failed building Hunspell object for " + lang_code)
                    logging.error("Aborting.")
                    exit(1)
        else:
            raise RuntimeError(f"It does not exist any valid dictionary directory"
                               f"for {lang_code} in the paths {self.hunspell_paths}."
                               f"Please, execute 'fastspell-download'.")
        return hunspell_obj


    def load_hunspell_dicts(self):
        #If there are languages that can be mistaken 
        #with the target language: prepare an array of Hunspell spellcheckers
        #for all the similar languages
        # The function will load for this similar.yaml:
        # hbs_lat: [hbs_lat, sl]
        # hbs_cyr: [hbs_cyr, ru, mk, bg]
        # the subsequent list of hunspell objs:
        # hunspell_objs = [hbs_lat, sl, hbs_cyr, ru, mk, bg]

        # Obtain all the possible lists for the given lang
        # a.k.a the list for each script of the lang
        self.similar = []
        for sim_entry in self.similar_langs:
            if sim_entry.split('_')[0] == self.lang:
                self.similar.append(self.similar_langs[sim_entry])

        logging.debug(f"Similar lists for '{self.lang}': {self.similar}")
        self.hunspell_objs = {}
        for similar_list in self.similar:
            for l in similar_list:
                if l in self.hunspell_objs:
                    continue # Avoid loading one dic twice
                #load dicts
                logging.debug(f"Loading dictionary for {l}")
                self.hunspell_objs[l] = self.search_hunspell_dict(self.hunspell_codes[l])


    def load_scripts(self):
        # Crate translate tables for script detection
        self.script_tables = {
            "hbs": {
                # Combination of Gaj's alphabet and Montenegrin Latin
                # plus unicode chars of double letters
                'hbs_lat': str.maketrans('', '',
                    'aAbBcčČćĆdDđĐeEfFgGhHiIjJkKlLmMnNoOpPrRsSšŠŚśtuUvVzZžŽŹźﬁﬂﬆĳœǌ'),
                # Combination of Serbian Cyrillic and Montenegrin Cyrillic
                'hbs_cyr': str.maketrans('', '',
                    'АаБбВвГгДддЂђЕеЖжЗзЗ́з́ИиКкkЛлЉљМмНнЊњОоПпРрСсС́с́ЋћТтУуФфХхЦцЧчШшЩщҵҥӕ'),
            },
        }


    def getscript(self, sent, lang):
        # Return as detected script the one that its translate table
        # deletes more characters
        script_tables = self.script_tables[lang] # grab script tables of the requested lang
        best_count = sys.maxsize
        best_script = None
        for script in script_tables.keys():
            count_chars = len(sent.translate(script_tables[script]))
            if count_chars < best_count:
                best_count = count_chars
                best_script = script

        return best_script


    def getlang(self, sent):
        sent=sent.replace("\n", " ").strip()
        prediction = self.model.predict(sent.lower(), k=1)[0][0][len(self.prefix):]

        # Return 'hbs' for all serbo-croatian variants
        # if hbs mode is enabled or hbs is the requested language
        if (self.hbs or self.lang == 'hbs') and prediction in HBS_LANGS:
            prediction = 'hbs'

        # If prediction does not specify the with variant
        # replace it by any of the variants to trigger hunspell refinement
        if prediction == "no":
            prediction = "nb"
        if prediction == "sh":
            prediction = "sr"

        # Always detect script if supported (will be printed only if requested)
        script = ''
        if prediction in self.script_tables:
            prediction = self.getscript(sent, prediction)
            logging.debug(f"Detected script {prediction}")

        #TODO: Confidence score?

        if self.similar == [] or prediction not in self.hunspell_objs:
        #Non mistakeable language: just return FastText prediction
            refined_prediction = prediction
        else:
        #The target language is mistakeable
            # Obtain the list of languages to spellcheck, only similar for the current lang and script
            current_similar = None
            for sim_list in self.similar:
                if prediction in sim_list or f'{prediction}_{script}' in sim_list:
                    current_similar = sim_list

            spellchecked = {}
            for l in current_similar:
                #Get spellchecking for all the mistakeable languages
                logging.debug(l)
                dec_sent = sent.encode(encoding='UTF-8',errors='strict').decode('UTF-8') #Not 100% sure about this...
                raw_toks = sent.strip().split(" ")
                toks = remove_unwanted_words(raw_toks, self.lang)
                try:
                    correct_list = list(map(self.hunspell_objs[l].spell, toks))
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

            logging.debug(f"Spellchecked: {spellchecked}")
            if len(spellchecked) > 0:
                #at least one of the spellchecks was below the threshold            
                #get best values and keys
                best_value = min(spellchecked.values())
                best_keys = [k for k, v in spellchecked.items() if v == best_value]
                if len(best_keys)==1:
                    #Only one language scoring the best
                    refined_prediction = best_keys[0]
                else:
                    #It's a tie!
                    if self.mode == "aggr":
                        #Aggressive approach: if the targetted language is among the best scoring, take it
                        if self.lang in best_keys:
                            refined_prediction = self.lang
                        elif prediction in best_keys:
                            #the targetted language is not in the best ones, and the prediction?
                            refined_prediction = prediction
                        else:
                            #Just take one
                            refined_prediction = best_keys[0]
                    if self.mode == "cons":
                        #Conservative: just keep it as unknown
                        refined_prediction = "unk"
            else:
                #Nothing in the spellchecking list
                if self.mode == "aggr":
                    refined_prediction = prediction
                else:
                    refined_prediction = "unk"

        # If script detection not requested
        # remove it from prediction
        if self.script:
            return refined_prediction
        else:
            return refined_prediction.split('_')[0]


def perform_identification(args):
    time_start = timeit.default_timer()
    if args.aggr:
        mode="aggr"
    if args.cons:
        mode="cons"

    fs = FastSpell(args.lang, mode=mode, config_path=args.config_path,
                   hbs=args.hbs, script=args.script)

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

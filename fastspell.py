import sys
import timeit
import argparse
import logging
import os
import fasttext
import hunspell
import urllib.request
from sacremoses import MosesTokenizer

__author__ = "Marta Bañón"
__version__ = "Version 0.1 # 01/07/2021 # Initial release # Marta Bañón"

try:
    model = fasttext.load_model('lid.176.bin')  #FastText model
except ValueError as ex:
    logging.warning("Downloading FastText model...")
    urllib.request.urlretrieve("https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin", "lid.176.bin")
    model = fasttext.load_model('lid.176.bin') 
    
threshold = 0.25 #Hunspell max error rate allowed in a sentence
dictpath="/usr/share/hunspell/" #Hunspell .dic and .aff files directory
prefix = "__label__" #FastText returns langs labeled as __label__LANGCODE

#Target langs (keys) dict for mistakeable languages (values)
similar_langs = {
"ca":["es", "ca"],
"da":["da", "nb"],
"es":["es", "gl", "ca"],
"gl":["es", "pt", "gl"],
"nb":["nn", "da", "nb"],
"nn":["nb", "da", "nn"],
"bs":["hr", "sr", "me", "mk", "sq", "bs"],
"cs":["sk", "cs"],
"sk":["cs", "sk"],
"hr":["bs", "sr", "me", "mk", "sq", "hr"],
"me":["bs", "hr", "mk", "sr", "sq", "me"],
"mk":["bs", "hr", "me", "sr", "sq", "mk"],
"sq":["bs", "hr", "me", "mk", "sr", "sq"],
"sr":["bs", "hr", "me", "mk", "sq", "sr"]
}


#TO DO: Change to anything more maintainable
tokenizers = {
"ca": MosesTokenizer("ca"),
"gl": MosesTokenizer("es"), #TO DO
"nb": MosesTokenizer("nb"),
"nn": MosesTokenizer("nb"), #TO DO
"da": MosesTokenizer("da"),
"bs": MosesTokenizer("en"), #TO DO
"cs": MosesTokenizer("cs"),
"sk": MosesTokenizer("sk"),
"hr": MosesTokenizer("en"), #TO DO
"me": MosesTokenizer("en"), #TO DO
"mk": MosesTokenizer("en"), #TO DO
"sq": MosesTokenizer("en"), #TO DO
"sr": MosesTokenizer("en"), #TO DO
"es": MosesTokenizer("es"),
"pt": MosesTokenizer("pt")
}

#This is how hunspell files (.dic and .aff) are named in dictpath
hunspell_codes = {
"ca": "ca_ES",
"gl": "gl_ES",
"nb": "nb_NO",
"nn": "nn_NO",
"da": "da_DK",
"bs": "bs_BA",
"cs": "cs_CZ",
"sk": "sk_SK",
"hr": "hr_HR",
"me": "sr_ME",
"mk": "mk_MK",
"sq": "sq_AL",
"sr": "sr_Latn_RS",
"es": "es_ES",
"pt": "pt_PT"
}

hunspell_objs = {}


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
            
            
#Removes punctuation and propernouns to avoid 
#Hunspell error rates too high
#and focus only on "normal" words.
def remove_non_alpha_and_propernouns(tokens):
    newtokens = []
    isfirsttoken=True
    for token in tokens:
        if token.upper() != token.lower() and (isfirsttoken or token[0]!=token[0].upper()):    
            newtokens.append(token.lower())
        isfirsttoken=False    
    return newtokens        


parser = argparse.ArgumentParser(prog=os.path.basename(sys.argv[0]), formatter_class=argparse.ArgumentDefaultsHelpFormatter, description=__doc__)
parser.add_argument('lang', type=str)

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

similar = similar_langs.get(args.lang)

#If there are languages that can be mistaken 
#with the target language: prepare an array of Hunspell spellcheckers
#for all the similar languages
if similar != None:
    for l in similar:
        dict = dictpath+hunspell_codes.get(l)
        hunspell_obj = hunspell.HunSpell(dict+'.dic', dict+'.aff') 
        hunspell_objs[l] = hunspell_obj
        
    
start_time = timeit.default_timer()

for line in sys.stdin:
    parts = line.strip().split("\t")
    sent = parts[0]
    prediction = model.predict(sent, k=1)[0][0][len(prefix):]
    #classic norwegian ñapa
    if prediction == "no":
        prediction = "nb"
    #TODO: Confidence score?
    
    if similar == None or prediction not in similar:
    #Non mistakeable language
        if prediction == args.lang:
            #this is ok
            print(sent+"\t"+prediction)
        else:
            #this is not ok (but output anyway because this is a benchmark hehe)
            print(sent+"\t"+prediction)    
    else:
    #The target language is mistakeable
        spellchecked = {}
        for l in hunspell_objs:
            #Get spellchecking for all the mistakeable langauges
            logging.debug(l)
            dec_sent = sent.encode(encoding='UTF-8',errors='strict').decode('UTF-8') #Not 100% sure about this...
            raw_toks = tokenizers.get(l).tokenize(dec_sent, escape=False)
            toks = remove_non_alpha_and_propernouns(raw_toks)
            try:
                correct_list = list(map(hunspell_objs.get(l).spell, toks))                      
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
            if error_rate < threshold: #we don't keep it if the error rate is above the threshold
                spellchecked[l] =  error_rate
            logging.debug("----------------")
            
        if len(spellchecked) > 0:
            #at least one of the spellchecks was below the threshold            
            #get best values and keys
            best_value = min(spellchecked.values())
            best_keys = [k for k, v in spellchecked.items() if v == best_value]
            if len(best_keys)==1:
                #Only one language scoring the best
                print(sent+"\t"+best_keys[0])
            else:
                #It's a tie!
                if args.aggr:
                    #Aggressive approach: if the targetted language is among the best scoring, take it
                    if args.lang in best_keys:
                        print(sent+"\t"+args.lang)
                    elif prediction in best_keys:
                        #the targetted language is not in the best ones, and the prediction?
                        print(sent+"\t"+prediction)
                    else:
                        #Just take one
                        print(sent+"\t"+best_keys[0])
                if args.cons:
                    #Conservative: just keep it as unknown
                    print(sent+"\t"+"unk")            
                                         
        else:
            #Nothing in the spellchecking list
            if args.aggr:
                print(sent+"\t"+prediction)
            else:    
                print(sent+"\t"+"unk")
                
end_time = timeit.default_timer()
        

print("Elapsed time: {}".format(end_time - start_time))
    
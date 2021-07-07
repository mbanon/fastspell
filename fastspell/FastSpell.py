from sacremoses import MosesTokenizer
import fasttext
import hunspell
import logging
import urllib.request



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

class FastSpell:
    
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


    #Special tokenizers. If the lang is not in this list, MosesTokenizer(lang) will be used
    #(failing back to "en" if langnot exists)
    special_tokenizers = {
    "gl": MosesTokenizer("es"), #TO DO
    "nn": MosesTokenizer("nb") #TO DO
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
    tokenizers={}

    def __init__(self, lang, mode="cons"):
        assert (mode=="cons" or mode=="aggr"), "Unknown mode. Use 'aggr' for aggressive or 'cons' for conservative"

        self.lang = lang
        self.mode = mode

        try:
            self.model = fasttext.load_model('lid.176.bin')  #FastText model
        except ValueError as ex:
            logging.warning("Downloading FastText model...")
            urllib.request.urlretrieve("https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin", "lid.176.bin")
            self.model = fasttext.load_model('lid.176.bin') 

        self.similar = self.similar_langs.get(lang)
        #If there are languages that can be mistaken 
        #with the target language: prepare an array of Hunspell spellcheckers
        #for all the similar languages
        if self.similar != None:
            for l in self.similar:
                #load dicts
                dict = self.dictpath+self.hunspell_codes.get(l)
                hunspell_obj = hunspell.HunSpell(dict+'.dic', dict+'.aff') 
                self.hunspell_objs[l] = hunspell_obj
                #load tokenizers
                if l in self.special_tokenizers.keys():
                    self.tokenizers[l] = self.special_tokenizers.get(l)
                else:
                    self.tokenizers[l] = MosesTokenizer(l)    
                


    def getlang(self, sent):
        sent=sent.strip()
        prediction = self.model.predict(sent, k=1)[0][0][len(self.prefix):]
        #classic norwegian ñapa
        if prediction == "no":
            prediction = "nb"
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
                raw_toks = self.tokenizers.get(l).tokenize(dec_sent, escape=False)
                toks = remove_non_alpha_and_propernouns(raw_toks)
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



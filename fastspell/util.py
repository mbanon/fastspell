from string import punctuation
from argparse import ArgumentTypeError
import logging
import hashlib
import sys
import os

def logging_setup(args = None):
    logger = logging.getLogger()
    logger.handlers = [] # Removing default handler to avoid duplication of log messages
    logger.setLevel(logging.ERROR)
    
    h = logging.StreamHandler(sys.stderr)
    if args != None:
       h = logging.StreamHandler(args.logfile)
      
    h.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(h)

    if args != None:
        if not args.quiet:
            logger.setLevel(logging.INFO)
        if args.debug:
            logger.setLevel(logging.DEBUG)

#Removes punctuation and propernouns to avoid 
#Hunspell error rates too high
#and focus only on "normal" words.
#Uppercased (propernouns) rule does not apply to German
def remove_unwanted_words(tokens, lang):
    newtokens = []
    isfirsttoken=True
    for token in tokens:
        token=token.strip(punctuation+" ")
        if lang=="de":
            if token.upper() != token.lower():
                newtokens.append(token)
        else:
            if token.upper() != token.lower() and (isfirsttoken or token[0]!=token[0].upper()):    
                newtokens.append(token.lower())
        isfirsttoken=False
    return newtokens

def get_hash(filepath):
    hash = None
    try:
        with open(filepath, 'rb') as model_file:
            file_content = model_file.read()
            md5Hash = hashlib.md5(file_content)
            hash = md5Hash.hexdigest()
        return hash    
    except FileNotFoundError:
        return None

def check_dir(path):
    if not os.path.exists(path):
        raise ArgumentTypeError(f"{path} does not exist")
    if not os.path.isdir(path):
        raise ArgumentTypeError(f"{path} is not a directory")
    return path

def check_file(path):
    if not os.path.exists(path):
        raise ArgumentTypeError(f"{path} does not exist")
    if not os.path.isfile(path):
        raise ArgumentTypeError(f"{path} is not a file")
    return path

from tempfile import TemporaryDirectory
from argparse import ArgumentTypeError
from string import punctuation
import logging
import hashlib
import sys
import os

import yaml


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


def load_config(config_path=None):
    ''' Load FastSpell yaml config files: similar langs and hunspell dicts '''
    if not config_path and "FASTSPELL_CONFIG" in os.environ:
        config_path = os.environ["FASTSPELL_CONFIG"]
        if not os.path.isdir(config_path):
            logging.warning("$FASTSPELL_CONFIG is not a valid path, using default")
            config_path = None

    if not config_path:
        cur_path = os.path.dirname(__file__)
        config_path = cur_path + "/config"

    #similar languages
    similar_yaml_file = open(config_path+"/similar.yaml")
    similar_langs = yaml.safe_load(similar_yaml_file)["similar"]

    #hunspell
    hunspell_codes_file = open(config_path+"/hunspell.yaml")
    hunspell_config = yaml.safe_load(hunspell_codes_file)
    hunspell_codes = hunspell_config["hunspell_codes"]
    if hunspell_config["dictpath"]:
        # If config has a hunspell path, add it
        if os.path.isabs(hunspell_config["dictpath"]):
            config_dictpath = hunspell_config["dictpath"]
        else:
            config_dictpath = os.path.join(config_path, hunspell_config["dictpath"])
        hunspell_paths = [config_dictpath]
    else:
        hunspell_paths = []

    # Paths to search for dictionaries
    # Firstly use hunspell path from config if there is
    # secondly try local/share/hunspell (which is the default download)
    # finally add all the remainin hunspell paths
    if "HOME" in os.environ:
        hunspell_paths.append(os.path.expanduser("~/.local/share/fastspell"))
        hunspell_paths.append(os.path.expanduser("~/.local/share/hunspell"))
    if "VIRTUAL_ENV" in os.environ:
        hunspell_paths.append(os.path.expandvars("$VIRTUAL_ENV/share/hunspell"))
    if "/usr/share/hunspell" not in hunspell_paths:
        hunspell_paths.append("/usr/share/hunspell")
    logging.debug(f"Paths to search for hunspell directories in order: {hunspell_paths}")
    if not hunspell_paths:
        raise RuntimeError("There are no possible paths to look for dictionaries")

    return similar_langs, hunspell_codes, hunspell_paths


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

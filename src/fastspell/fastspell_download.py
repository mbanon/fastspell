#!/usr/bin/env python
from tempfile import TemporaryDirectory
from shutil import copyfile
import argparse
import logging
import tarfile
import sys
import os

from urllib import request

try:
    from . import FastSpell
    from .util import logging_setup, load_config
except ImportError:
    from fastspell import FastSpell
    from util import logging_setup, load_config


def download_dictionaries(dest, lang_codes: dict, force=False):
    ''' Download dictionaries from github '''
    repo_url = "https://github.com/mbanon/fastspell/releases/download/dictionaries_v1/fastspell_dictionaries.tgz"

    if not os.path.exists(dest):
        raise RuntimeError(f"Download directory '{dest}' does not exist")

    # Check that dictionaries exist
    all_correct = True
    logging.debug("Checking existence of hunspell dictionaries.")
    for lang in lang_codes.keys():
        dic_dest = os.path.join(dest, f"{lang_codes[lang]}.dic")
        aff_dest = os.path.join(dest, f"{lang_codes[lang]}.aff")
        if not os.path.exists(dic_dest) or not os.path.exists(aff_dest):
            logging.debug(f"Dictionary for {lang} {lang_codes[lang]} does not exist")
            all_correct = False

    # Download again if something is missing or download is forced
    if all_correct and not force:
        logging.info("All dictionaries already exist, finishing. Use --force to force download.")
        return

    with TemporaryDirectory() as dirname:
        # Download repo zip in tempdir
        logging.info(f"Downloading to tempdir {dirname}")
        file_path = os.path.join(dirname, 'dicts.tgz')
        request.urlretrieve(repo_url, file_path)

        # Extract zip
        logging.info("Extracting tar")
        with tarfile.open(file_path) as tar:
            tar.extractall(path=dirname)

        # Copy dictionaries to path for each lang requested
        logging.info(f"Copying to {dest}")
        for lang in lang_codes.keys():
            cur_dic = os.path.join(dirname, f"{lang_codes[lang]}.dic")
            cur_aff = os.path.join(dirname, f"{lang_codes[lang]}.aff")
            if not os.path.exists(cur_dic):
                logging.warning(f"Could not download dictionary for {lang} {lang_codes[lang]}")
                continue

            dic_dest = os.path.join(dest, f"{lang_codes[lang]}.dic")
            aff_dest = os.path.join(dest, f"{lang_codes[lang]}.aff")
            copyfile(cur_dic, dic_dest)
            copyfile(cur_aff, aff_dest)
            logging.debug(f"Copied hunspell dict for '{lang}' to {dic_dest}")

        logging.info("Download finished")


def main():
    parser = argparse.ArgumentParser(
            description="Download Hunspell dictionaries and FastText model")

    default_dir = os.path.expanduser('~/.local/share/fastspell')
    parser.add_argument('download_dir', nargs='?',
                        default=default_dir,
                        type=str,
                        help='Directory to store downloaded hunspell dictionaries.'
                        f' By default fastspell will use "{default_dir}"')
    parser.add_argument('-f', '--force', action='store_true', help='Force download of dictionaries')
    groupL = parser.add_argument_group('Logging')
    groupL.add_argument('-q', '--quiet', action='store_true', help='Silent logging mode')
    groupL.add_argument('--debug', action='store_true', help='Debug logging mode')
    groupL.add_argument('--logfile', type=argparse.FileType('a'), default=sys.stderr, help="Store log to a file")

    args = parser.parse_args()
    logging_setup(args)

    # Trigger fasttext download
    dummy = FastSpell(lang='en', mode='aggr')
    logging.warning("Dictionaries are now installed alongside FastSpell with pip"
                    " Use '-f' option to force download of dictionaries.")
    if not args.force:
        sys.exit(0)

    # Load config from yaml files to obtain needed dictionaries
    _, hunspell_codes, hunspell_paths = load_config()
    logging.debug(hunspell_codes)
    if args.download_dir == default_dir and not os.path.exists(args.download_dir):
        os.makedirs(args.download_dir, exist_ok=True)
    download_dictionaries(args.download_dir, hunspell_codes, force=args.force)

if __name__ == "__main__":
    main()

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
from sklearn.feature_extraction import DictVectorizer
import pycountry
import xgboost
from sklearn.model_selection import GridSearchCV

try:
    from . import __version__
    from .util import logging_setup, remove_unwanted_words, get_hash, check_dir, load_config
    from .fastspell import FastSpell
except ImportError:
    from fastspell import __version__
    from util import logging_setup, remove_unwanted_words, get_hash, check_dir, load_config
    from fastspell import FastSpell

class FastSpellAI(FastSpell):
    def __init__(self, lang, *args, **kwargs):
        super().__init__(lang, *args, **kwargs)

ft_download_url = "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin"
ft_model_path = "lid.176.bin"
if os.path.exists(ft_model_path):
    ft_model = fasttext.load_model(ft_model_path)
else:
    urllib.request.urlretrieve(ft_download_url, ft_model_path)
    ft_model = fasttext.load_model(ft_model_path)

ft_prefix = "__label__"

fsobj = FastSpellAI("en")

languages = [label[len(ft_prefix):] for label in fsobj.model.get_labels()]

unsupported = []
hunspell_objs = {}
for language in languages:
    try:
        search_l = None
        if language in fsobj.hunspell_codes:
            search_l = fsobj.hunspell_codes[language]
        elif f"{language}_lat" in fsobj.hunspell_codes:
            search_l = fsobj.hunspell_codes[f"{language}_lat"]
        elif f"{language}_cyr" in fsobj.hunspell_codes:
            search_l = fsobj.hunspell_codes[f"{language}_cyr"]
        else:
            search_l = language
        hunspell_objs[language] = fsobj.search_hunspell_dict(search_l)
    except:
        unsupported.append(language)

print(len(languages))
print(len(unsupported))
print(unsupported)

prediction = fsobj.model.predict("Ciao, mondo!".lower(), k=3)
print(prediction)
print(prediction[0])
print(prediction[0][0])
print(prediction[0][0][len(ft_prefix):])

sentences = []
labels = []
count = 0
with open("../sentences.csv", "r") as f:
    for l in f:
        number, language, text = next(f).split("\t")

        if language != "ita":
            continue

        lang = pycountry.languages.get(alpha_3=language)

        text = text.replace("\n", " ").strip()
        prediction = fsobj.model.predict(text.lower(), k=3)

        # print(prediction)

        lang0 = prediction[0][0][len(ft_prefix):]
        lang0_prob = prediction[1][0]
        if len(prediction[0]) >= 2:
            lang1 = prediction[0][1][len(ft_prefix):]
            lang1_prob = prediction[1][1]
        else:
            # If there's only one option... Not much to do.
            continue
        if len(prediction[0]) >= 3:
            lang2 = prediction[0][2][len(ft_prefix):]
            lang2_prob = prediction[1][2]
        else:
            lang2 = None
            lang2_prob = 0.0

        label = None
        if lang0 == lang.alpha_2:
            label = 0
        elif lang1 == lang.alpha_2:
            label = 1
        elif lang2 == lang.alpha_2:
            label = 2

        if label is None:
            continue

        # print(lang0)

        raw_tokens = text.strip().split(" ")
        if lang0 in hunspell_objs:
            tokens = remove_unwanted_words(raw_tokens, lang0)
            correct = 0
            for token in tokens:
                try:
                    if hunspell_objs[lang0].spell(token):
                        correct += 1
                except UnicodeEncodeError as ex:
                    pass
            lang0_dic_tokens = correct / len(tokens)
        else:
            lang0_dic_tokens = None

        if lang1 in hunspell_objs:
            tokens = remove_unwanted_words(raw_tokens, lang1)
            correct = 0
            for token in tokens:
                try:
                    if hunspell_objs[lang1].spell(token):
                        correct += 1
                except UnicodeEncodeError as ex:
                    pass
            lang1_dic_tokens = correct / len(tokens)
        else:
            lang1_dic_tokens = None

        if lang2 in hunspell_objs:
            tokens = remove_unwanted_words(raw_tokens, lang2)
            
            correct = 0
            for token in tokens:
                try:
                    if hunspell_objs[lang2].spell(token):
                        correct += 1
                except UnicodeEncodeError as ex:
                    pass

            lang2_dic_tokens = correct / len(tokens)
        else:
            lang2_dic_tokens = None

        sentences.append({
            "fastText_lang0": lang0_prob,
            "fastText_lang1": lang1_prob,
            "fastText_lang2": lang2_prob,
            "lang0_dic_tokens": lang0_dic_tokens,
            "lang1_dic_tokens": lang1_dic_tokens,
            "lang2_dic_tokens": lang2_dic_tokens,
        })
        labels.append(label)

        # count += 1
        # if count == 7:
        #     break

print(len(sentences))

dict_vectorizer = DictVectorizer()
X = dict_vectorizer.fit_transform(sentences)

xgb_model = xgboost.XGBClassifier(n_jobs=10)

clf = GridSearchCV(
    xgb_model,
    {"max_depth": [1, 2, 4, 6], "n_estimators": [25, 50, 100, 200]},
    verbose=1,
    n_jobs=1,
)
clf.fit(X, labels)
print(clf.best_score_)
print(clf.best_params_)
print(clf.best_estimator_)

clf.best_estimator_.save_model("model.ubj")

X_try = dict_vectorizer.fit_transform([sentences[0]])
classes = xgb_model.predict(X)
if classes[0] == 0:
    print("Lang0 chosen")
elif classes[0] == 1:
    print("Lang2 chosen")
elif classes[0] == 2:
    print("Lang3 chosen")

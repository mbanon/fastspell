# FastSpell
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/fastspell)
![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/mbanon/fastspell/release.yaml)

Targetted language identifier, based on FastText and Hunspell.

## How it works 

FastSpell will try to determine the language of a sentence by using **[FastText](https://fasttext.cc/)**.

If the language detected is very similar to the target language (i.e. FastText detected Spanish, while the targetted language is Galician), extra checks are performed with **[Hunspell](http://hunspell.github.io/)** to determine the language more precisely.

## Citation

If you find **FastSpell** useful, please consider citing the following paper:

> Marta Bañón, Gema Ramírez-Sánchez, Jaume Zaragoza-Bernabeu, and Sergio Ortiz Rojas, \
> "[FastSpell: The LangId Magic Spell](https://aclanthology.org/2024.lrec-main.626/)", \
> in **Proceedings of the 2024 Joint International Conference on Computational Linguistics, Language Resources and Evaluation (LREC-COLING 2024)**,\
> pages 7133–7140, Torino, Italia. ELRA and ICCL.

```
@inproceedings{banon-etal-2024-fastspell-langid,
    title = "{F}ast{S}pell: The {L}ang{I}d Magic Spell",
    author = "Ba{\~n}{\'o}n, Marta  and
      Ram{\'\i}rez-S{\'a}nchez, Gema  and
      Zaragoza-Bernabeu, Jaume  and
      Ortiz Rojas, Sergio",
    editor = "Calzolari, Nicoletta  and
      Kan, Min-Yen  and
      Hoste, Veronique  and
      Lenci, Alessandro  and
      Sakti, Sakriani  and
      Xue, Nianwen",
    booktitle = "Proceedings of the 2024 Joint International Conference on Computational Linguistics, Language Resources and Evaluation (LREC-COLING 2024)",
    month = may,
    year = "2024",
    address = "Torino, Italia",
    publisher = "ELRA and ICCL",
    url = "https://aclanthology.org/2024.lrec-main.626",
    pages = "7133--7140",
    abstract = "Language identification is a crucial component in the automated production of language resources, particularly in multilingual and big data contexts. However, commonly used language identifiers struggle to differentiate between similar or closely-related languages. This paper introduces FastSpell, a language identifier that combines fastText (a pre-trained language identifier tool) and Hunspell (a spell checker) with the aim of having a refined second-opinion before deciding which language should be assigned to a text. We provide a description of the FastSpell algorithm along with an explanation on how to use and configure it. To that end, we motivate the need of such a tool and present a benchmark including some popular language identifiers evaluated during the development of FastSpell. We show how FastSpell is useful not only to improve identification of similar languages, but also to identify new ones ignored by other tools.",
}
```

## Requirements & Installation

**FastSpell** can be installed from PyPI
```
pip install fastspell
```
or directly from source:
```
pip install .
```
Note that it requires Python3.8 or higher, and the `python3-dev` package:

```
sudo apt-get install python3-dev
```

**IMPORTANT**:
In some cases (for example, when using Python 3.10), the `cyhunspell` version 2.0.2 installation will fail. If that's the case, you need to install `cyhunspell==2.0.3` before installing `fastspell`:

First make sure build dependencies are installed
```
sudo apt install build-essential autoconf autopoint libtool
```
then install the pip package
```
pip install git+https://github.com/MSeal/cython_hunspell@2.0.3
```

### Model download

To trigger the FastText model download before running fastspell, run:
```
fastspell-download
```
Since version 0.7 all the dictionaries are installed automatically with pip and there is no need to do anything else.
For further explanation about how configuration works, [see below](#configuration).

### Conda
Also, you can install the conda package:
```
conda install -c conda-forge -c bitextor fastspell
```

### Automatic testing
Some automatic tests are provided to check that the installation went fine. In order to check it, go to the `/tests` directory and run:
```
python3 -m unittest discover
```
You might need to istall the `unittest` package with `pip`, in  case you don't have it installed beforehand.

## Configuration

A few configuration files are provided under the `fastspell/config` directory.
If you need to change default configuration, you can provide the path to your config directory with `-c`/`--config` or with the environment variable `FASTSPELL_CONFIG`.

#### similar.yaml

In this dictionary-like file, similar languages are stored. These are the languages that are going to be "double-checked" with Hunspell after being identified with FastText. For example, see the line `gl: [es, pt, gl] `. This means that, when the targetted language is Galician, and FastText identifies a given sentence as Spanish, Portuguese or Galician, extra checks will be performed with Hunspell to confirm which of the three similar languages is more suitable for the sentence.

Please note that you need Hunspell dictionaries for all the languages in this file (if you use the `fastspell-download` command, there is nothing else to do). This file can be modified to remove a language you are not interested in, or a language for which you don't have Hunspell dictionaries, or to add new similar or target languages.

#### hunspell.yaml

In this file, the names of the dictionaries are stored. All similar languages must be in this list in order to properly work.

For example, the first entry in the `hunspell_codes` is ` ca: ca_ES`, and the dictionary path is `~/.local/share/fastspell/`. That means that the Hunspell files for Catalan are  `~/.local/share/fastspell/ca_ES.dic` and `~/.local/share/fastspell/ca_ES.aff`.

By default `dicpath` is empty, which means FastSpell will look in these directories for the dictionaries:
```python
fastspell_dictionaries.__path__[0]
```
```
~/.local/share/fastspell
~/.local/share/hunspell
$VIRTUAL_ENV/share/hunspell
/usr/share/hunspell
```
To use a custom path, put it in `dicpath` and will be the first one to search.


## Usage

### Module:
In order to use **FastSpell** as a Python module, just install and import it :
```
from fastspell import FastSpell
```
Build a FastSpell object, like:
```
fsobj = FastSpell.FastSpell("en", mode="cons")
```
(learn more about modes in the section below)

And then use the `getlang` function with the sentences you want to identify, for example:
```
fsobj.getlang("Hello, world")
#'en'
fsobj.getlang("Hola, mundo")
#'es'

```

### CLI:
```
iusage: fastspell [-h] [--aggr] [--cons] [--hbs] [-q] [--debug]
                 [--logfile LOGFILE] [-v]
                 lang [input] [output]

positional arguments:
  lang
  input              Input sentences. (default: <_io.TextIOWrapper
                     name='<stdin>' encoding='UTF-8'>)
  output             Output of the language identification. (default:
                     <_io.TextIOWrapper name='<stdout>' mode='w'
                     encoding='UTF-8'>)

optional arguments:
  -h, --help         show this help message and exit
  --aggr             Aggressive strategy (more positives) (default: False)
  --cons             Conservative strategy (less positives) (default: False)
  --hbs              Return all Serbo-Croatian variants as 'hbs' (default:
                     False)

Logging:
  -q, --quiet        Silent logging mode (default: False)
  --debug            Debug logging mode (default: False)
  --logfile LOGFILE  Store log to a file (default: <_io.TextIOWrapper
                     name='<stderr>' mode='w' encoding='UTF-8'>)
  -v, --version      show version of this script and exit
```


## Aggressive vs Conservative

FastSpell comes in two flavours: Aggressive and Conservative.

The **Aggressive** mode is less hesitant to tag a sentence with the target language, and never has doubts. The **Conservative** version, on the other hand, is more reluctant to tag a sentence with the target language and will use the `unk`(unknown) tag in case of doubt (when there is a tie between the target language and other language, for example)

## Benchmark 

Benchmark data: https://github.com/mbanon/benchmarks

Results:  https://docs.google.com/spreadsheets/d/158ZRWMgRH5TptlFWpKyh5uRL5jTkKW1d4KGJg1AZf7A/edit?usp=sharing 


## Usage example

Input text:
```
19-01-2011 47 comentarios 7o Xornadas de Xardinería de Galicia (RE)PLANTEAR
• Proceso de valoración de idoneidade: entrevistas psicosociais e visita domiciliaria e aplicación de test psicolóxicos, se é o caso.
- Chrome e Firefox en MacOS non son compatibles (unicamente Safari é compatible con MacOS), pero invocarase PSAL ao intentar empregar Chrome ou Firefox.
Mago da luz / Maga da luz
Celebrada a homenaxe a Xosé Manuel Seivane Rivas
A instalación eléctrica en teletraballo
Saltar á navegación Navegación INICIO
Julio Freire, competidor da FGA, invitado polo Kennel club de Inglaterra, para participar nos Crufts 2014 (Birmingham, 6 - 9 de marzo).
25 de xullo - Truong Tan Sang toma posesión como presidente de Vietnam
Quen pode solicitar o dito financiamento?
```
Command:
```
fastspell  --aggr lang inputtext
fastspell  --cons lang inputtext
```
Aggressive output:
```
19-01-2011 47 comentarios 7o Xornadas de Xardinería de Galicia (RE)PLANTEAR     gl
• Proceso de valoración de idoneidade: entrevistas psicosociais e visita domiciliaria e aplicación de test psicolóxicos, se é o caso.   gl
- Chrome e Firefox en MacOS non son compatibles (unicamente Safari é compatible con MacOS), pero invocarase PSAL ao intentar empregar Chrome ou Firefox.        gl
Mago da luz / Maga da luz       gl
Celebrada a homenaxe a Xosé Manuel Seivane Rivas        gl
A instalación eléctrica en teletraballo gl
Saltar á navegación Navegación INICIO   gl
Julio Freire, competidor da FGA, invitado polo Kennel club de Inglaterra, para participar nos Crufts 2014 (Birmingham, 6 - 9 de marzo). es
25 de xullo - Truong Tan Sang toma posesión como presidente de Vietnam  gl
Quen pode solicitar o dito financiamento?       gl
```

Conservative output:
```
19-01-2011 47 comentarios 7o Xornadas de Xardinería de Galicia (RE)PLANTEAR     unk
• Proceso de valoración de idoneidade: entrevistas psicosociais e visita domiciliaria e aplicación de test psicolóxicos, se é o caso.   gl
- Chrome e Firefox en MacOS non son compatibles (unicamente Safari é compatible con MacOS), pero invocarase PSAL ao intentar empregar Chrome ou Firefox.        gl
Mago da luz / Maga da luz       unk
Celebrada a homenaxe a Xosé Manuel Seivane Rivas        gl
A instalación eléctrica en teletraballo unk
Saltar á navegación Navegación INICIO   gl
Julio Freire, competidor da FGA, invitado polo Kennel club de Inglaterra, para participar nos Crufts 2014 (Birmingham, 6 - 9 de marzo). es
25 de xullo - Truong Tan Sang toma posesión como presidente de Vietnam  gl
Quen pode solicitar o dito financiamento?       gl
```
Getting stats:
```
cat inputtext | fastspell --aggr $L | cut -f2 | sort | uniq -c | sort -nr
cat inputtext | fastspell --cons $L | cut -f2 | sort | uniq -c | sort -nr
```
Aggressive:
```
9 gl
1 es
```
Conservative:
```
6 gl
3 unk
1 es
```


---

![Connecting Europe Facility](https://www.paracrawl.eu/images/logo_en_cef273x39.png)

All documents and software contained in this repository reflect only the authors' view. The Innovation and Networks Executive Agency of the European Union is not responsible for any use that may be made of the information it contains.

# FastSpell

Targetted language identifier, based on FastText and Hunspell.

## How it works 

FastSpell will try to determine the language of a sentence by using **[FastText](https://fasttext.cc/)**.

If the language detected is very similar to the target language (i.e. FastText detected Spanish, while the targetted language is Galician), extra checks are performed with **[Hunspell](http://hunspell.github.io/)** to determine the language more precisely.


## Requirements & Installation

**FastSpell** can be installed from PyPI
```
pip install fastspell
```
or directly from source:
```
pip install .
```
Note that **Hunspell** requires `python-dev` and `libhunspell-dev`:

```
sudo apt-get install python-dev libhunspell-dev
```

Before running FastSpell for any of the languages listed as [similar](https://github.com/mbanon/fastspell/blob/main/fastspell/config/similar.yaml), you must have all the [needed Hunspell dictionaries](https://github.com/mbanon/fastspell/blob/main/fastspell/config/hunspell.yaml) for that language.
For further explanation about how configuration works, [see below](#configuration).
You can use the `fastspell-download` command to download all the needed files for the default configuration, just run it without arguments:
```
fastspell-download
```

### Conda
Also, you can install the conda package:
```
conda install -c conda-forge -c bitextor fastspell
```

### RedHat installation
For RedHat and its derivatives
```
sudo dnf install hunspell hunspell-devel
```
must be ran to install Hunspell.

If you found an installation error during `pip install hunspell` that says `/usr/bin/ld: cannot find -lhunspell`, you'll probably need to add a symlink to `/usr/lib64` or other path in your environment (like `/home/user/.local/lib`).
```
sudo ln -s /usr/lib64/libhunspell-1.7.so /usr/lib64/libhunspell.so
```

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

![comparative.png](comparative.png)


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
fastspell $L --aggr inputtext
fastspell $L --cons inputtext
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
cat inputtext | fastspell $L --aggr | cut -f2 | sort | uniq -c | sort -nr
cat inputtext | fastspell $L --cons | cut -f2 | sort | uniq -c | sort -nr
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


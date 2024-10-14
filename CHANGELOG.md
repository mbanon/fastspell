# CHANGELOG

## FastSpell 0.12
- Added more languages: am, ti

## FastSpell 0.11.1
- Restrict numpy version to <2


## FastSpell 0.11
- Added support for Serbian cyrillic and latin dictionaries.
- Changes in Slovak and Slovene similar languages.


## FastSpell 0.10
- Added more languages: af, ar, az, be, bn, cy, et, fa, fi, ga, gu, he, hi, hu, id, kk, kn, ky, lt, lv, mn, ml, mr, ms, ne, pl, pt, ru, so, sv, ta, te, th, tr, tt, uk, ur, uz
- Fixed bug with character encoding that resulted in some sentences not being evaluated for certain languages.
- Fix issue that was preventing non-latin words from being evaluated.
- Improved removal of punctuation of evaluated tokens
- Conservative mode is now less conservative:
  - Raised error threshold
  - Tag targetted language in case of tie, if error rate is 0


## FastSpell 0.9:
- Now using CyHunspell.
- Added automatic tests.

## FastSpell 0.8:
- Icelandic mistakeable languages.

## FastSpell 0.7:
- Default dictionaries are now installed via pip as a dependency.
- Download of dictionaries in `fastspell-download` is deprecated.

## FastSpell 0.6.1:
### Changed:
- Trigger fasttext download in fastspell-download command.
- Use specific github tag/release to store dictionaries.

## FastSpell 0.6:
### Added:
- Automatic download of Hunspell dictionaries.
### Changed:
- Changeable configuration.
- Migrate to pyproject and src/ code structure

## FastSpell 0.5:
### Added:
- Support for mixed scripts.
### Changed:
- Lowercase text for FastText prediction.

## FastSpell 0.4:
### Added:
- Serbo-Croatian script detection.

## FastSpell 0.3:
### Added:
- Serbo-Croatian mode.

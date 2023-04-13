import unittest
import logging

from fastspell import FastSpell

class FastSpellTest(unittest.TestCase):
	@classmethod
	def setUpClass(cls) -> None:
		logger = logging.getLogger()
		# logger.setLevel(logging.DEBUG)

	def test_simple(self):
		lines = [
			('Hello, world', 'en'),
			('¿Cómo te llamas? disculpe adiós', 'es'),
		]

		fs = FastSpell('en', mode='cons')

		for line, expected in lines:
			self.assertEqual(fs.getlang(line), expected, f'Line: {line}')

	def test_similar(self):
		lines = [
			('Hello, world', 'en'),
			('¿Cómo te llamas? disculpe adiós', 'es'),
			('Como te chamas? desculpe adeus', 'pt'), # I'd say 'gl' but alas.
		]

		# 'es' has similar languages in the default config
		fs = FastSpell('es', mode='cons')

		self.assertEqual(
			[fs.getlang(line) for line, _ in lines],
			[lang for _, lang in lines])


from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parent.parent
BASE = 'https://tiagosillos.art.br'


class SeoGenerationTests(unittest.TestCase):
    def test_sitemap_and_catalog_remain_consistent_after_regeneration(self):
        with tempfile.TemporaryDirectory(prefix='seo-check-', dir=ROOT.parent) as temp:
            site = Path(temp) / 'site'
            shutil.copytree(ROOT, site, ignore=shutil.ignore_patterns('.git', '__pycache__'))
            # Uma exclusão editorial e um redirecionamento não podem virar indexáveis.
            for slug, directive in [('private', '<meta name="robots" content="noindex,follow">'),
                                    ('redirect', '<meta http-equiv="refresh" content="0;url=/">')]:
                page = site / slug / 'index.html'
                page.parent.mkdir()
                page.write_text(f'<html><head><title>Fixture</title>{directive}</head><body></body></html>', encoding='utf-8')

            def generate():
                subprocess.run([sys.executable, str(site / 'tools' / 'apply_seo.py')],
                               cwd=temp, check=True, capture_output=True)

            def snapshot():
                return {p.relative_to(site).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in site.rglob('*') if p.is_file()}

            generate()
            first = snapshot()
            generate()
            self.assertEqual(first, snapshot(), 'Reaplicar o SEO precisa ser idempotente')

            urls = [loc.text for loc in ET.parse(site / 'sitemap.xml').findall('.//{*}loc')]
            self.assertEqual(len(urls), len(set(urls)))
            for prefix in ('/editora/', '/site_links/', '/experimentos/', '/private/', '/redirect/'):
                self.assertFalse(any(urlsplit(url).path.startswith(prefix) for url in urls), prefix)
            self.assertIn(BASE + '/', urls)
            for url in urls:
                parsed = urlsplit(url)
                self.assertEqual(parsed.scheme + '://' + parsed.netloc, BASE)
                page = site / parsed.path.lstrip('/') / 'index.html'
                self.assertTrue(page.is_file(), url)
                soup = BeautifulSoup(page.read_text(encoding='utf-8'), 'html.parser')
                self.assertEqual([tag['href'] for tag in soup.select('link[rel="canonical"]')], [url])
                for tag in soup.select('meta[name="robots"], meta[name="googlebot"]'):
                    self.assertNotIn('noindex', tag.get('content', '').lower(), url)
                self.assertIsNone(soup.find('meta', attrs={'http-equiv': 'refresh'}), url)

            experiment = BeautifulSoup((site / 'experimentos/bubble-fluid-v1/index.html').read_text(encoding='utf-8'), 'html.parser')
            self.assertIn('noindex', experiment.select_one('meta[name="robots"]')['content'])
            catalog = BeautifulSoup((site / 'catalogo/index.html').read_text(encoding='utf-8'), 'html.parser')
            cards = [a['href'] for a in catalog.select('.cover-grid a.book-card')]
            self.assertEqual(len(cards), len(set(cards)))
            for page in (site / 'livros').glob('*/index.html'):
                url = f'/livros/{page.parent.name}/'
                self.assertIn(url, cards, 'Livro sem link no catálogo: ' + url)
                self.assertIn(BASE + url, urls)


if __name__ == '__main__':
    unittest.main()

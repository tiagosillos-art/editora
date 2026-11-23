from pathlib import Path
import hashlib
import json
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
        with tempfile.TemporaryDirectory(prefix='seo-check-') as temp:
            site = Path(temp) / 'site'
            shutil.copytree(ROOT, site, ignore=shutil.ignore_patterns('.git', '__pycache__', '_arquivo-webgl', 'relatório', '.catalogo-deps'))
            archived = site / '_arquivo-webgl' / 'index.html'
            archived.parent.mkdir()
            archived.write_text('<html><head><title>WebGL antigo</title></head><body></body></html>', encoding='utf-8')
            archived_content = archived.read_bytes()
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
            self.assertEqual(archived_content, archived.read_bytes(), 'O arquivo WebGL deve permanecer intacto')

            urls = [loc.text for loc in ET.parse(site / 'sitemap.xml').findall('.//{*}loc')]
            self.assertEqual(len(urls), len(set(urls)))
            for prefix in ('/editora/', '/site_links/', '/experimentos/', '/private/', '/redirect/', '/_arquivo-webgl/'):
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

            books = json.loads((site / 'data/livros.json').read_text(encoding='utf-8'))
            self.assertEqual(len(books), len({book['slug'] for book in books}))
            collection_url = '/colecoes/biblioteca-franciscana/'
            self.assertIn(BASE + collection_url, urls)
            home = BeautifulSoup((site / 'index.html').read_text(encoding='utf-8'), 'html.parser')
            self.assertIsNotNone(home.select_one(f'.hero a[href="{collection_url}"]'))
            self.assertIsNotNone(catalog.select_one(f'a[href="{collection_url}"]'))
            collection = BeautifulSoup((site / collection_url.lstrip('/') / 'index.html').read_text(encoding='utf-8'), 'html.parser')
            groups = collection.select('.cover-grid[data-series]')
            self.assertEqual([grid.find_parent('section')['id'] for grid in groups], ['fontes', 'sabatier', 'thode'])
            for grid in groups:
                entries = sorted((book for book in books if book.get('series') == grid['data-series']),
                                 key=lambda book: book.get('volume') or 0)
                self.assertTrue(entries, grid['data-series'])
                self.assertEqual([card['href'] for card in grid.select('.book-card')],
                                 [f"/livros/{book['slug']}/" for book in entries])

            print_cards = {card['href'] for card in catalog.select('.book-card[data-impresso]')}
            self.assertEqual(print_cards, {f"/livros/{book['slug']}/" for book in books if book.get('print_br')})
            for book in books:
                path = site / 'livros' / book['slug'] / 'index.html'
                if not path.is_file():
                    continue
                self.assertTrue((site / book['cover'].lstrip('/')).is_file(), book['slug'])
                page = BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')
                if edition := book.get('print_br'):
                    self.assertEqual([link['href'] for link in page.select('.print-edition a')], [edition['url']])
                if play := book.get('play'):
                    self.assertEqual([link['href'] for link in page.select('.stores .play')], [play])
                    self.assertIsNone(page.select_one('.stores .amazon'))


if __name__ == '__main__':
    unittest.main()

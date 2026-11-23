from pathlib import Path
from bs4 import BeautifulSoup
import json, re, html

ROOT=Path(__file__).resolve().parent.parent
BASE='https://tiagosillos.art.br'
INSTAGRAM='https://www.instagram.com/tiagosillos.art/'
SITE='Tiago Sillos Art'
EDITOR='Tiago Sillos Padovani'
ASSOCIATE_TAG='tiagosillosar-20'
GA_MEASUREMENT_ID='G-EYGB2RVCFD'

# Links completos gerados no SiteStripe. Mantemos o ASIN canônico nos dados/Schema
# e usamos estes URLs somente nos botões de saída para a Amazon.
AFFILIATE_LINKS={
    'B0GQNCFMJR':'https://www.amazon.com.br/dp/B0GQNCFMJR?tag=tiagosillosar-20',
    'B0H6NB1D9B':'https://www.amazon.com.br/dp/B0H6NB1D9B?linkCode=ll2&tag=tiagosillosar-20&linkId=9143c167a60d28962fb8a212d07a040e',
    'B0HMWKVPLF':'https://www.amazon.com.br/dp/B0HMWKVPLF?tag=tiagosillosar-20',
    'B0H6LMVSMB':'https://www.amazon.com.br/dp/B0H6LMVSMB?linkCode=ll2&tag=tiagosillosar-20&linkId=23d27c39c6273eb06f964693698105da',
    'B0H8YSZGMH':'https://www.amazon.com.br/dp/B0H8YSZGMH?linkCode=ll2&tag=tiagosillosar-20&linkId=9d4c908e278df8b6d9001855141fedd8',
    'B0HFBDLJBY':'https://www.amazon.com.br/dp/B0HFBDLJBY?linkCode=ll2&tag=tiagosillosar-20&linkId=80709d785033dff84aacc8c0aee63bbd',
    'B0HFM6SH29':'https://www.amazon.com.br/dp/B0HFM6SH29?linkCode=ll2&tag=tiagosillosar-20&linkId=adc5eba1876a4ae25019c5ebf79351e9',
    'B0GRHQ3R6N':'https://www.amazon.com.br/dp/B0GRHQ3R6N?linkCode=ll2&tag=tiagosillosar-20&linkId=bbc492def82271d4ea78397a5d7aa3d7',
    'B0HD16ZQV5':'https://www.amazon.com.br/dp/B0HD16ZQV5?linkCode=ll2&tag=tiagosillosar-20&linkId=9d5aa135e8820e801a2e4996060202c3',
    'B0HDD7D7SM':'https://www.amazon.com.br/dp/B0HDD7D7SM?linkCode=ll2&tag=tiagosillosar-20&linkId=0234ca79fd35da126cdebacb67645cef',
    'B0H925FSZS':'https://www.amazon.com.br/dp/B0H925FSZS?linkCode=ll2&tag=tiagosillosar-20&linkId=af709746082b1b1ea6fef7666c274937',
    'B0H6QZF4MT':'https://www.amazon.com.br/dp/B0H6QZF4MT?linkCode=ll2&tag=tiagosillosar-20&linkId=40706323dfad939fb529521631c82b4a',
    'B0H6LVKK2Y':'https://www.amazon.com.br/dp/B0H6LVKK2Y?linkCode=ll2&tag=tiagosillosar-20&linkId=4d685791a2c93d63feee2a2bd80f740b',
    'B0H6QZNVRW':'https://www.amazon.com.br/dp/B0H6QZNVRW?linkCode=ll2&tag=tiagosillosar-20&linkId=ddd21889503c8d93032cd459df2618f5',
    'B0H999CW3J':'https://www.amazon.com.br/dp/B0H999CW3J?linkCode=ll2&tag=tiagosillosar-20&linkId=3f7ba607313fa87e75d03162f9179f35',
    'B0HBCPVMDN':'https://www.amazon.com.br/dp/B0HBCPVMDN?linkCode=ll2&tag=tiagosillosar-20&linkId=86d7df9cdfd53c1511e9fe4c5482bda8',
}

books=json.loads((ROOT/'data/livros.json').read_text(encoding='utf-8'))
by_slug={b['slug']:b for b in books}

for b in books:
    if b.get('cover'): b['cover']='/'+b['cover'].replace('/editora/','/').lstrip('/')
(ROOT/'data/livros.json').write_text(json.dumps(books,ensure_ascii=False,indent=2),encoding='utf-8')

def canon(rel):
    return BASE+'/' if rel==Path('index.html') else BASE+'/'+rel.parent.as_posix()+'/'

def kind(rel):
    if rel==Path('index.html'): return 'home'
    if rel.parts[0]=='livros': return 'book'
    if rel.parts[0]=='catalogo': return 'catalog'
    if rel.parts[0]=='colecoes': return 'collection'
    if rel.parts[0]=='sobre': return 'about'
    return 'page'

def authors(s):
    return [x.strip() for x in re.split(r'\s*[&;]\s*|\s+e\s+',s) if x.strip()]

def meta(soup,**a):
    t=soup.new_tag('meta')
    for k,v in a.items(): t[k.replace('_','-')]=v
    soup.head.append(t)

def link(soup,rel,href): soup.head.append(soup.new_tag('link',rel=rel,href=href))

def excluded_from_index(soup):
    for tag in soup.find_all('meta'):
        name=tag.get('name','').lower()
        directives=re.split(r'[\s,]+',tag.get('content','').lower())
        if name in {'robots','googlebot'} and {'noindex','none'} & set(directives):
            return True
        if tag.get('http-equiv','').lower()=='refresh':
            return True
    return False

def complete_catalog(soup,entries):
    # Os livros devem estar no HTML, inclusive sem executar JavaScript.
    grid=soup.select_one('.cover-grid')
    if not grid: return
    cards={a['href']:a for a in grid.select('a.book-card[href]')}
    categories={'arte':'Arte e estética','filosofia':'Filosofia','literatura':'Literatura','teosofia':'Teosofia','psicologia':'Psicologia','sonhos':'Sonhos','ciencia':'Ciência e tecnologia'}
    for book in entries:
        href=f"/livros/{book['slug']}/"
        if not (ROOT/'livros'/book['slug']/'index.html').is_file(): continue
        card=cards.get(href)
        if card is None:
            card=soup.new_tag('a',href=href,attrs={'class':'book-card','data-category':book['category']})
            cover=soup.new_tag('div',attrs={'class':'cover-wrap'})
            cover.append(soup.new_tag('img',src=book['cover'],alt='Capa de '+book['title'],loading='lazy'))
            card.append(cover)
            info=soup.new_tag('div',attrs={'class':'meta'})
            category='E-books para Impacientes' if book.get('series')=='E-books para Impacientes' else categories.get(book['category'],book['category'])
            for tag,cls,value in [('div','tagline',category),('h3',None,book['title']),('div','author',book['author'])]:
                child=soup.new_tag(tag)
                if cls: child['class']=cls
                child.string=value
                info.append(child)
            card.append(info)
            grid.append(card)
        print_label=card.select_one('.print-label')
        if print_label: print_label.decompose()
        card.attrs.pop('data-impresso',None)
        if book.get('print_br'):
            card['data-impresso']='true'
            label=soup.new_tag('div',attrs={'class':'print-label'})
            label.string='Impresso no Brasil'
            card.select_one('.meta').append(label)

def apply_ga(soup):
    # Remove versões anteriores para manter a instalação idempotente.
    for t in list(soup.find_all('script')):
        src=t.get('src','')
        body=t.string or ''
        if 'googletagmanager.com/gtag/js' in src or 'GA_MEASUREMENT_ID' in body or "gtag('config'" in body:
            t.decompose()
    loader=soup.new_tag('script',src=f'https://www.googletagmanager.com/gtag/js?id={GA_MEASUREMENT_ID}')
    loader['async']=''
    soup.head.append(loader)
    tag=soup.new_tag('script')
    tag.string=f"""window.dataLayer = window.dataLayer || [];
function gtag(){{dataLayer.push(arguments);}}
gtag('js', new Date());
gtag('config', '{GA_MEASUREMENT_ID}');

document.addEventListener('DOMContentLoaded', function() {{
  document.querySelectorAll('a[href*="amazon."]').forEach(function(a) {{
    a.addEventListener('click', function() {{
      gtag('event', 'amazon_click', {{
        link_url: a.href,
        link_text: (a.textContent || '').trim(),
        page_path: location.pathname
      }});
    }});
  }});
}});"""
    soup.head.append(tag)
def jsonld(soup,obj):
    t=soup.new_tag('script',type='application/ld+json'); t.string=json.dumps(obj,ensure_ascii=False,separators=(',',':')); soup.head.append(t)

def org():
    return {'@type':'Organization','@id':BASE+'/#organization','name':SITE,'url':BASE+'/','sameAs':[INSTAGRAM],'founder':{'@type':'Person','name':EDITOR,'url':BASE+'/sobre/'}}

def asin_from_book(book):
    asin=(book or {}).get('asin','')
    if asin: return asin
    m=re.search(r'/dp/([A-Z0-9]{10})',(book or {}).get('amazon',''))
    return m.group(1) if m else ''

def apply_affiliate_link(soup,book):
    asin=asin_from_book(book)
    btn=soup.select_one('a.btn.amazon')
    if not asin or not btn: return False
    url=AFFILIATE_LINKS.get(asin)
    if not url:
        current=btn.get('href','')
        url=current if f'/dp/{asin}?' in current and f'tag={ASSOCIATE_TAG}' in current else f'https://www.amazon.com.br/dp/{asin}?tag={ASSOCIATE_TAG}'
    btn['href']=url
    btn['rel']='sponsored noopener'
    btn['target']='_blank'
    old=soup.select_one('.amazon-associate-disclosure')
    if not old:
        stores=btn.find_parent(class_='stores')
        if stores:
            p=soup.new_tag('p')
            p['class']='amazon-associate-disclosure'
            small=soup.new_tag('small')
            small.string='Link patrocinado. Como participante do Programa de Associados da Amazon, sou remunerado pelas compras qualificadas efetuadas.'
            p.append(small)
            stores.insert_after(p)
    return True

def apply_print_edition(soup,book):
    stores=soup.select_one('.stores')
    if not stores: return
    existing=soup.select_one('.print-edition')
    if existing: existing.decompose()
    edition=book.get('print_br')
    if not edition: return
    section=soup.new_tag('section',attrs={'class':'print-edition','aria-labelledby':'edicao-impressa'})
    heading=soup.new_tag('h2',id='edicao-impressa')
    heading.string='Edição impressa no Brasil'
    details=soup.new_tag('p')
    details.string=f"{edition['binding']} · {edition['size']} · {edition['pages']} páginas"
    button=soup.new_tag('a',href=edition['url'],target='_blank',rel='noopener noreferrer',attrs={'class':'btn'})
    button.string=f"Comprar na {edition['store']}" if edition['store']=='UICLAP' else f"Comprar no {edition['store']}"
    section.extend([heading,details,button])
    anchor=soup.select_one('.amazon-associate-disclosure') or stores
    anchor.insert_after(section)

pages=[]
# Percorre apenas as pastas ativas, sem entrar no arquivo do site antigo.
excluded_dirs={'editora','site_links','tests','_arquivo-webgl','relatório'}
page_files=[ROOT/'index.html']
for directory in sorted(ROOT.iterdir()):
    if directory.is_dir() and not directory.name.startswith('.') and directory.name not in excluded_dirs:
        page_files.extend(sorted(directory.rglob('index.html')))
for p in sorted(page_files):
    rel=p.relative_to(ROOT)
    text=p.read_text(encoding='utf-8').replace('/editora/','/')
    text=text.replace('<a class="artlink" href="/">Galeria de arte</a>',f'<a class="artlink" href="{INSTAGRAM}" target="_blank" rel="noopener noreferrer">Instagram</a>')
    text=text.replace('<a href="/">Galeria</a>',f'<a href="{INSTAGRAM}" target="_blank" rel="noopener noreferrer">Instagram</a>')
    soup=BeautifulSoup(text,'html.parser')
    if not soup.head: continue
    noindex=rel.parts[0]=='experimentos' or excluded_from_index(soup)
    apply_ga(soup)
    c=canon(rel); k=kind(rel); title=soup.title.get_text(strip=True) if soup.title else SITE
    book=by_slug.get(rel.parts[1]) if k=='book' else None
    play_url=(book or {}).get('play')
    for a in list(soup.find_all('a',href=True)):
        if 'play.google.com/store/books' in a['href'] and a['href']!=play_url:
            a.decompose()
    if k=='catalog':
        complete_catalog(soup,books)
    if rel.as_posix()=='colecoes/biblioteca-arte-estetica-moderna/index.html':
        complete_catalog(soup,(b for b in books if b.get('series')=='Biblioteca de Arte e Estética Moderna'))
    d=soup.find('meta',attrs={'name':'description'}); desc=d.get('content','').strip() if d else ''
    if not desc: desc='Editora independente dedicada à arte abstrata, estética e vanguardas modernas.'
    for t in list(soup.find_all('script',attrs={'type':'application/ld+json'})): t.decompose()
    for t in list(soup.head.find_all(['meta','link'])):
        if t.name=='meta':
            n=(t.get('name') or '').lower(); prop=(t.get('property') or '').lower()
            if n in {'robots','author','twitter:card','twitter:title','twitter:description','twitter:image'} or prop.startswith('og:'): t.decompose()
        elif 'canonical' in (t.get('rel') or []): t.decompose()
    link(soup,'canonical',c)
    meta(soup,name='robots',content='noindex,follow' if noindex else 'index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1')
    meta(soup,name='author',content=EDITOR)
    img=BASE+'/assets/capas/ponto-e-linha-sobre-o-plano.jpg'
    if book:
        img=BASE+'/'+book['cover'].lstrip('/')
        apply_affiliate_link(soup,book)
        apply_print_edition(soup,book)
    for prop,val in [('og:locale','pt_BR'),('og:site_name',SITE),('og:type','book' if k=='book' else 'website'),('og:title',title),('og:description',desc),('og:url',c),('og:image',img),('og:image:alt',('Capa de '+book['title']) if book else SITE)]: meta(soup,property=prop,content=val)
    for name,val in [('twitter:card','summary_large_image'),('twitter:title',title),('twitter:description',desc),('twitter:image',img)]: meta(soup,name=name,content=val)
    if k=='home':
        schema={'@context':'https://schema.org','@graph':[org(),{'@type':'WebSite','@id':BASE+'/#website','url':BASE+'/','name':SITE,'inLanguage':'pt-BR','publisher':{'@id':BASE+'/#organization'}},{'@type':'WebPage','@id':c+'#webpage','url':c,'name':title,'description':desc,'isPartOf':{'@id':BASE+'/#website'},'about':{'@id':BASE+'/#organization'},'inLanguage':'pt-BR'}]}
    elif k=='about':
        schema={'@context':'https://schema.org','@graph':[org(),{'@type':'Person','@id':BASE+'/sobre/#tiago','name':EDITOR,'url':c,'sameAs':[INSTAGRAM],'jobTitle':['Arquiteto','Artista visual','Tradutor','Editor']},{'@type':'AboutPage','@id':c+'#webpage','url':c,'name':title,'description':desc,'inLanguage':'pt-BR'}]}
    elif k in {'catalog','collection'}:
        seen=[]
        for a in soup.find_all('a',href=True):
            h=a['href']
            if h.startswith('/livros/') and h not in seen: seen.append(h)
        schema={'@context':'https://schema.org','@graph':[org(),{'@type':'CollectionPage','@id':c+'#webpage','url':c,'name':title,'description':desc,'inLanguage':'pt-BR','mainEntity':{'@type':'ItemList','itemListElement':[{'@type':'ListItem','position':i+1,'url':BASE+h} for i,h in enumerate(seen)]}}]}
    elif k=='book' and book:
        aa=[{'@type':'Person','name':x} for x in authors(book['author'])]
        bs={'@type':'Book','@id':c+'#book','name':book['title'],'url':c,'image':img,'author':aa if len(aa)>1 else aa[0],'publisher':{'@id':BASE+'/#organization'},'inLanguage':'pt-BR'}
        if book['author']!=EDITOR:
            bs['translator']={'@type':'Person','name':EDITOR}
        if book.get('subtitle'): bs['alternativeHeadline']=book['subtitle']
        if str(book.get('pages','')).isdigit(): bs['numberOfPages']=int(book['pages'])
        same=[u for u in [book.get('amazon'),book.get('play')] if u]
        if same: bs['sameAs']=same
        if edition:=book.get('print_br'):
            bs['workExample']={'@type':'Book','bookFormat':'https://schema.org/Paperback','url':edition['url'],'numberOfPages':edition['pages'],'inLanguage':'pt-BR'}
        if book.get('series'): bs['isPartOf']={'@type':'BookSeries','name':book['series']}
        if book.get('subjects'): bs['keywords']=book['subjects']
        schema={'@context':'https://schema.org','@graph':[org(),bs,{'@type':'WebPage','@id':c+'#webpage','url':c,'name':title,'description':desc,'mainEntity':{'@id':c+'#book'},'inLanguage':'pt-BR'}]}
    else: schema={'@context':'https://schema.org','@graph':[org(),{'@type':'WebPage','url':c,'name':title,'description':desc,'inLanguage':'pt-BR'}]}
    jsonld(soup,schema); p.write_text(str(soup),encoding='utf-8')
    if not noindex: pages.append(c)

pages=list(dict.fromkeys(pages))
xml=['<?xml version="1.0" encoding="UTF-8"?>','<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for u in pages:
    pr='1.0' if u==BASE+'/' else ('0.9' if '/livros/' in u else '0.8')
    xml += ['  <url>',f'    <loc>{html.escape(u)}</loc>',f'    <priority>{pr}</priority>','  </url>']
xml.append('</urlset>')
(ROOT/'sitemap.xml').write_text('\n'.join(xml)+'\n',encoding='utf-8')
(ROOT/'robots.txt').write_text(f'User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n',encoding='utf-8')

(ROOT/'editora').mkdir(exist_ok=True)
(ROOT/'editora/index.html').write_text('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="robots" content="noindex,follow"><link rel="canonical" href="https://tiagosillos.art.br/"><meta http-equiv="refresh" content="0;url=/"><title>Tiago Sillos Art</title><script>location.replace(\'/\');</script></head><body><p><a href="/">Ir para Tiago Sillos Art</a></p></body></html>',encoding='utf-8')

(ROOT/'site_links').mkdir(exist_ok=True)
(ROOT/'site_links/index.html').write_text('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="robots" content="noindex,follow"><link rel="canonical" href="https://tiagosillos.art.br/"><meta http-equiv="refresh" content="0;url=/"><title>Tiago Sillos Art</title><script>location.replace(\'/\');</script></head><body><p><a href="/">Ir para Tiago Sillos Art</a></p></body></html>',encoding='utf-8')
print(f'SEO e links de compra aplicados em {len(pages)} páginas.')

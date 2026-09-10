from pathlib import Path
from bs4 import BeautifulSoup
import json, re, html, shutil

ROOT=Path('.')
BASE='https://tiagosillos.art.br'
INSTAGRAM='https://www.instagram.com/tiagosillos.art/'
SITE='Tiago Sillos Art'
EDITOR='Tiago Sillos Padovani'
ASSOCIATE_TAG='tiagosillosar-20'

# Links completos gerados no SiteStripe. Mantemos o ASIN canônico nos dados/Schema
# e usamos estes URLs somente nos botões de saída para a Amazon.
AFFILIATE_LINKS={
    'B0H6NB1D9B':'https://www.amazon.com.br/dp/B0H6NB1D9B?linkCode=ll2&tag=tiagosillosar-20&linkId=9143c167a60d28962fb8a212d07a040e',
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
    b['play']=''
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
    return [x.strip() for x in re.split(r'\s*&\s*|\s+e\s+',s) if x.strip()]

def meta(soup,**a):
    t=soup.new_tag('meta')
    for k,v in a.items(): t[k.replace('_','-')]=v
    soup.head.append(t)

def link(soup,rel,href): soup.head.append(soup.new_tag('link',rel=rel,href=href))
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
    url=AFFILIATE_LINKS.get(asin)
    if not url: return False
    btn=soup.select_one('a.btn.amazon')
    if not btn: return False
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

pages=[]
for p in sorted(ROOT.rglob('index.html')):
    rel=p.relative_to(ROOT)
    if rel.parts[0] in {'editora','.git','.github'}: continue
    text=p.read_text(encoding='utf-8').replace('/editora/','/')
    text=text.replace('<a class="artlink" href="/">Galeria de arte</a>',f'<a class="artlink" href="{INSTAGRAM}" target="_blank" rel="noopener noreferrer">Instagram</a>')
    text=text.replace('<a href="/">Galeria</a>',f'<a href="{INSTAGRAM}" target="_blank" rel="noopener noreferrer">Instagram</a>')
    soup=BeautifulSoup(text,'html.parser')
    if not soup.head: continue
    for a in list(soup.find_all('a',href=True)):
        if 'play.google.com/store/books' in a.get('href',''):
            a.decompose()
    c=canon(rel); k=kind(rel); title=soup.title.get_text(strip=True) if soup.title else SITE
    d=soup.find('meta',attrs={'name':'description'}); desc=d.get('content','').strip() if d else ''
    if not desc: desc='Editora independente dedicada à arte abstrata, estética e vanguardas modernas.'
    for t in list(soup.find_all('script',attrs={'type':'application/ld+json'})): t.decompose()
    for t in list(soup.head.find_all(['meta','link'])):
        if t.name=='meta':
            n=(t.get('name') or '').lower(); prop=(t.get('property') or '').lower()
            if n in {'robots','author','twitter:card','twitter:title','twitter:description','twitter:image'} or prop.startswith('og:'): t.decompose()
        elif 'canonical' in (t.get('rel') or []): t.decompose()
    link(soup,'canonical',c)
    meta(soup,name='robots',content='index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1')
    meta(soup,name='author',content=EDITOR)
    img=BASE+'/assets/capas/ponto-e-linha-sobre-o-plano.jpg'; book=None
    if k=='book':
        book=by_slug.get(rel.parts[1]); img=BASE+'/'+book['cover'].lstrip('/') if book else img
        if book: apply_affiliate_link(soup,book)
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
        bs={'@type':'Book','@id':c+'#book','name':book['title'],'url':c,'image':img,'author':aa if len(aa)>1 else aa[0],'translator':{'@type':'Person','name':EDITOR},'publisher':{'@id':BASE+'/#organization'},'inLanguage':'pt-BR'}
        if book.get('subtitle'): bs['alternativeHeadline']=book['subtitle']
        if str(book.get('pages','')).isdigit(): bs['numberOfPages']=int(book['pages'])
        same=[u for u in [book.get('amazon')] if u]
        if same: bs['sameAs']=same
        if book.get('series'): bs['isPartOf']={'@type':'BookSeries','name':book['series']}
        if book.get('subjects'): bs['keywords']=book['subjects']
        schema={'@context':'https://schema.org','@graph':[org(),bs,{'@type':'WebPage','@id':c+'#webpage','url':c,'name':title,'description':desc,'mainEntity':{'@id':c+'#book'},'inLanguage':'pt-BR'}]}
    else: schema={'@context':'https://schema.org','@graph':[org(),{'@type':'WebPage','url':c,'name':title,'description':desc,'inLanguage':'pt-BR'}]}
    jsonld(soup,schema); p.write_text(str(soup),encoding='utf-8'); pages.append(c)

pages=list(dict.fromkeys(pages))
xml=['<?xml version="1.0" encoding="UTF-8"?>','<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for u in pages:
    pr='1.0' if u==BASE+'/' else ('0.9' if '/livros/' in u else '0.8')
    xml += ['  <url>',f'    <loc>{html.escape(u)}</loc>',f'    <priority>{pr}</priority>','  </url>']
xml.append('</urlset>')
(ROOT/'sitemap.xml').write_text('\n'.join(xml)+'\n',encoding='utf-8')
(ROOT/'robots.txt').write_text(f'User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n',encoding='utf-8')

shutil.rmtree(ROOT/'editora',ignore_errors=True); (ROOT/'editora').mkdir()
(ROOT/'editora/index.html').write_text('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="robots" content="noindex,follow"><link rel="canonical" href="https://tiagosillos.art.br/"><meta http-equiv="refresh" content="0;url=/"><title>Tiago Sillos Art</title><script>location.replace(\'/\');</script></head><body><p><a href="/">Ir para Tiago Sillos Art</a></p></body></html>',encoding='utf-8')
print(f'SEO, links de associado e limpeza do Google Play aplicados em {len(pages)} páginas.')

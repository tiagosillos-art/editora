from pathlib import Path
from bs4 import BeautifulSoup
import json, re, html, shutil

ROOT=Path('.')
BASE='https://tiagosillos.art.br'
INSTAGRAM='https://www.instagram.com/tiagosillos.art/'
SITE='Tiago Sillos Art'
EDITOR='Tiago Sillos Padovani'
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

pages=[]
for p in sorted(ROOT.rglob('index.html')):
    rel=p.relative_to(ROOT)
    if rel.parts[0] in {'editora','.git','.github'}: continue
    text=p.read_text(encoding='utf-8').replace('/editora/','/')
    text=text.replace('<a class="artlink" href="/">Galeria de arte</a>',f'<a class="artlink" href="{INSTAGRAM}" target="_blank" rel="noopener noreferrer">Instagram</a>')
    text=text.replace('<a href="/">Galeria</a>',f'<a href="{INSTAGRAM}" target="_blank" rel="noopener noreferrer">Instagram</a>')
    soup=BeautifulSoup(text,'html.parser')
    if not soup.head: continue
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
        same=[u for u in [book.get('amazon'),book.get('play')] if u]
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
print(f'SEO aplicado em {len(pages)} páginas.')

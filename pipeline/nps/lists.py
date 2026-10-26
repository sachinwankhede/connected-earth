#!/usr/bin/env python3
"""lists.py: download the official NPSpecies checklist for each matched unit. Writes pipeline/nps/lists/<CODE>.json
Each species: category, order, family, scientific name, common names, occurrence."""
import json,os,sys,subprocess,xml.etree.ElementTree as ET
here=os.path.dirname(os.path.abspath(__file__)); os.makedirs(os.path.join(here,'lists'),exist_ok=True)
def fetch(code):
    r=subprocess.run(['curl','-s','-L','-m','120','https://irmaservices.nps.gov/v3/rest/npspecies/checklist/'+code],capture_output=True)
    root=ET.fromstring(r.stdout); ns=root.tag.split('}')[0]+'}' if '}' in root.tag else ''
    out=[]
    for it in root:
        d={c.tag.replace(ns,''):(c.text or '') for c in it}
        out.append(dict(cat=d.get('Category'),order=d.get('Order'),family=d.get('Family'),name=d.get('ScientificName'),common=d.get('CommonNames'),occ=d.get('Occurrence'),nat=d.get('Nativeness'),abund=d.get('Abundance')))
    return out
if __name__=='__main__':
    codes=sorted({v['code'] for v in json.load(open(os.path.join(here,'codes.json'))).values() if v['code']})
    for c in codes:
        p=os.path.join(here,'lists',c+'.json')
        if os.path.exists(p): continue
        try: L=fetch(c)
        except Exception as e: print(c,'ERR',e); continue
        json.dump(L,open(p,'w'),ensure_ascii=False); print(c,len(L),flush=True)

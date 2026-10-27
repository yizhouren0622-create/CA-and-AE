"""Read a separately obtained pwrmos.lib and prepare the textbook model port.
Tested source: OrCAD revision1.24 dated1998-10-19.
Source URL: https://robustdesignconcepts.com/files/pspice/libs/pwrmos.lib
Usage: python3 ae-8.6.4-prepare-models.py /path/to/pwrmos.lib
The original/default model cards are not bundled with this website.
"""
from pathlib import Path
import re,sys
if len(sys.argv)!=2:raise SystemExit(__doc__)
S=Path(__file__).resolve().parent
raw=Path(sys.argv[1]).read_text(errors='strict')
def parse_num(s):
 s=s.lower();m=re.fullmatch(r'([+\-\d.e]+)(meg|[fpnumkg]?)',s);assert m,s
 return float(m[1])*{'':1,'f':1e-15,'p':1e-12,'n':1e-9,'u':1e-6,'m':1e-3,'k':1e3,'meg':1e6,'g':1e9}[m[2]]
mods=[]
for name,kp,w,vto,rds in [('IRF9512','10.15u','16u','-.7','266.7k'),('IRF832','20.85u','16u','.7','2meg'),('IRF840','20.85u','32u','.7','2meg'),('IRF9510','10.15u','16u','-.7','266.7k')]:
 line=re.search(r'(?is)\.model\s+'+name+r'\s+(nmos|pmos)\((.*?)\)',raw);assert line
 typ=line[1].upper();p=dict((k.lower(),v) for k,v in re.findall(r'(\w+)\s*=\s*([^\s+)]+)',line[2]));p.update(kp=kp,w=w,l='1u',vto=vto,rds=rds)
 # Internal MOS removes duplicated junction diode. External diode carries original N,TT,CBD.
 core={k:v for k,v in p.items() if k not in ['w','l','rds','rg','is','n','tt','cbd','pb','mj','fc','rd','rs']};core.update(is_='1e-30',cbd='0',rd='0',rs='0')
 coretxt=' '.join(f'{k.rstrip("_")}={v}' for k,v in core.items())
 ds='si di' if typ=='NMOS' else 'di si'
 diodetxt=' '.join(f'{k}={p.get(src,default)}' for k,src,default in [('is','is','1e-14'),('n','n','1'),('tt','tt','0'),('cjo','cbd','0'),('vj','pb','.8'),('m','mj','.5'),('fc','fc','.5')])
 mods.append(f'''.subckt B24_{name} d g s
Rgate g gi {p.get('rg','1u')}
Rdrain d di {p.get('rd','1u')}
Rsource s si {p.get('rs','1u')}
Rleak d s {rds}
Mcore di gi si si CORE_{name} W={w} L=1u
Dbody {ds} D_{name}
.model CORE_{name} {typ} ({coretxt})
.model D_{name} D ({diodetxt})
.ends B24_{name}
''')
(S/'ae-8.6.4-modified-models.lib').write_text('\n'.join(mods))

print('Created ae-8.6.4-modified-models.lib; run the downloaded ngspice decks in this directory.')

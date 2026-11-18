"""Static mathematical typography for explicit TeX and legacy inline notation."""
from functools import lru_cache
import html
import re
import xml.etree.ElementTree as ET
from latex2mathml.converter import convert
from latex2mathml.exceptions import MissingSuperScriptOrSubscriptError, NoAvailableTokensError

NS='http://www.w3.org/1998/Math/MathML'
ET.register_namespace('',NS)
def node(tag,text=None,children=()):
    e=ET.Element('{'+NS+'}'+tag)
    e.text=text
    e.extend(children)
    return e
def tag(e):return e.tag.rsplit('}',1)[-1]
def row(elements):return elements[0] if len(elements)==1 else node('mrow',children=elements)

def fractions(e):
    """Stack slash operators without flattening existing fractions or cases."""
    for child in list(e):fractions(child)
    if tag(e) not in ('mrow','mtd','math'):return
    # Group balanced fences exactly once, preserving the original parentheses.
    result=[];stack=[]
    for c in list(e):
        t=c.text if tag(c)=='mo' else None
        if t in ('(','[') or (t=='|' and (not stack or stack[-1][0]!='|')):
            stack.append((t,[c]));continue
        if stack and (stack[-1][0],t) in [('(',')'),('[',']'),('|','|')]:
            _,children=stack.pop();children.append(c)
            c=node('mrow',children=children);_divide_grouped(c)
        if stack:stack[-1][1].append(c)
        else:result.append(c)
    # Unmatched evaluation bars are left intact; no source syntax is dropped.
    while stack:
        _,children=stack.pop()
        if stack:stack[-1][1].extend(children)
        else:result.extend(children)
    e[:]=result
    _divide_grouped(e)

def _divide_grouped(e):
    items=list(e)
    # Parentheses not adjacent to a slash need no rewriting. Locate each operand
    # with a depth scan instead of deleting any original grouping or signs.
    while any(tag(x)=='mo' and x.text=='/' for x in items):
        i=next(j for j,x in enumerate(items) if tag(x)=='mo' and x.text=='/')
        def boundary(x):
            return tag(x)=='mspace' or (tag(x)=='mo' and x.text not in ('(',')','[',']','⁢'))
        left=i-1;depth=0
        while left>=0:
            x=items[left];t=x.text if tag(x)=='mo' else None
            if t in (')',']'):depth+=1
            elif t in ('(','['):
                if depth==0:break
                depth-=1
            elif depth==0 and boundary(x):break
            left-=1
        left+=1
        right=i+1;depth=0
        while right<len(items):
            x=items[right];t=x.text if tag(x)=='mo' else None
            if t in ('(','['):depth+=1
            elif t in (')',']'):
                if depth==0:break
                depth-=1
            elif depth==0 and boundary(x):break
            right+=1
        if left==i or right==i+1:raise ValueError('Division is missing an operand')
        items[left:right]=[node('mfrac',children=[row(items[left:i]),row(items[i+1:right])])]
    e[:]=items

@lru_cache(maxsize=30000)
def render_math(tex,display=False):
    if re.search(r'[\x00-\x09\x0b-\x1f]',tex):raise ValueError('Control character in TeX; use a raw string or escape backslashes')
    tree=ET.fromstring(convert(tex))
    fractions(tree)
    # Use the mathematical accent glyph rather than a visible ASCII caret.
    for accent in tree.iter():
        if tag(accent)=='mover' and len(accent)==2 and tag(accent[1])=='mo' and accent[1].text=='^':
            accent[1].text='ˆ'
    tree.set('display','block' if display else 'inline')
    tree.set('displaystyle','true')
    if any(tag(e)=='mo' and e.text=='/' for e in tree.iter()):raise ValueError('Unstacked division: '+tex)
    return ET.tostring(tree,encoding='unicode')

SUB='₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐₑₕᵢⱼₖₗₘₙₒₚᵣₛₜᵤᵥₓ'
SUB_ASC='0123456789+-=()aehijklmnoprstuvx'
SUP='⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁱⁿᵗ'
SUP_ASC='0123456789+-=()int'
SUB_MAP=str.maketrans(SUB,SUB_ASC)
SUP_MAP=str.maketrans(SUP,SUP_ASC)
GREEK={'α':'alpha','β':'beta','γ':'gamma','δ':'delta','ε':'epsilon','θ':'theta','λ':'lambda','μ':'mu','µ':'mu','π':'pi','ρ':'rho','σ':'sigma','τ':'tau','φ':'phi','ω':'omega','Δ':'Delta','Σ':'sum','∑':'sum','∞':'infty','∫':'int'}
FUNCTIONS={'sin','cos','tan','exp','ln','log','arctan','min','max','lim','sqrt'}
MACROS={'CMRR':r'\mathrm{CMRR}','KCL':r'\mathrm{KCL}','KVL':r'\mathrm{KVL}','RMS':r'\mathrm{RMS}'}
UNITS=r'(?:kΩ|MΩ|mΩ|Ω|kohms?|kilohms?|ohms?|MHz|kHz|Hz|rad|cm|mm|μm|µm|nm|m|ms|μs|µs|ns|μA|µA|mA|fA|nA|pA|kA|mV|μV|µV|kV|mW|μW|µW|kW|mF|μF|µF|nF|pF|mH|μH|µH|kJ|μC|µC|mC|nC|pC|dB|VA|var|V|A|W|F|H|S|C|J|s)'
NUMBER=r'(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+−-]?\d+)?'
QUANTITY=re.compile(NUMBER+r'\s*'+UNITS+r'(?=$|[^A-Za-z_₀-₉])')
WORD=re.compile(r'[A-Za-zαβγδεθλμµπρστφω](?:[A-Za-z0-9′̇]|_[A-Za-z0-9]+|_[+−-]|['+SUB+'])*')
SCOPED_SUBS={
 'A':['vd','vc','vf','vo','vs','v','f','i','p','r'],
 'g':['m1','mQ','ds','m'],
 'r':['ds0','ds','be2','be','bb','in','eq','o','i','d','a','b','P'],
 'T':['global'], 't':['ms'],
 'v':['i2d','gs1','be1','cm','id','ic','oc','la','ra','n1','n3','p1','p3','o1','o2','o4','i1','i2','i3','i4','gs','DS','GS','GD','AB','AK','i','o','s','p','n','f','c','x','y','t','A','B','C','D','G','L','M','N','P'],
 'V':['start','end','CES','CEQ','BEQ','DSQ','GSQ','REF','OQ','DQ','CQ','BQ','EQ','SQ','GQ','TN','TP','TH','TO','DS','GS','SD','SG','BE','CE','CC','EE','DD','SS','GG','OV','AO','om','th','T','A','B','C','D','E','F','G','I','L','M','N','O','P','R','S','X','Z','a','b','c','d','e','f','i','o','m','x','y'],
 'R':['g1','g2','g3','f1','f2','b1','b2','e1','c3','i1','i2','TH','si','id','in','eq','th','ab','G','L','P','b','c','d','e','f','g','i','o','s'],
 'u':['AB','ab','ac','ae','be','cb','cd','cf','db','df','ef','xy','C','d','s','i','o'],
 'U':['AB','xy','Th','th'], 'K':['CMR','n','p','P'],
 'I':['CEO','CQ','DQ','ZT','B','C','D','E','L','O','Q','R','S','V','Z','m'],
 'i':['out','b2','s','o','i','B','C','D','E','L','R','b','c','d','e','f'],
 'C':['ox','ab','b1','s'], 'P':['OM','RM','ZM','L','R','Z','i'],
 'Z':['L','b','f','i'], 'Q':['f'], 'B':['f'], 'F':['v'], 'p':['Us'], 'n':['V'],
}
ALIASES={'vc':'v_c','vb':'v_b','va':'v_a','Rg1':'R_g1','Rg2':'R_g2','Rg3':'R_g3','duC':'du_C','duL':'du_L','diL':'di_L','diC':'di_C','Uth':'U_th','Rth':'R_th','xid':'x_id','xf':'x_f','fc':'f_c','uC':'u_C','uL':'u_L','iL':'i_L','iC':'i_C','uR':'u_R','vL':'v_L','vR':'v_R','vC':'v_C','vO':'v_O','vo':'v_o','vi':'v_i','UTh':'U_th','RTh':'R_th','Pmax':'P_max','VREF':'V_REF','gm':'g_m','gds':'g_ds','rds':'r_ds','ro':'r_o','rbe':'r_be','rbb':'r_bb','Av':'A_v','Avd':'A_vd','Avc':'A_vc','Avs':'A_vs','Af':'A_f','RL':'R_L','RF':'R_F','RG':'R_G','RD':'R_D','RS':'R_S','VDD':'V_DD','VSS':'V_SS','VCC':'V_CC','VEE':'V_EE','VGS':'V_GS','VDS':'V_DS','VSG':'V_SG','VSD':'V_SD','VBE':'V_BE','VCE':'V_CE','ID':'I_D','IB':'I_B','IC':'I_C','IE':'I_E','IZ':'I_Z','Io':'I_o','Is':'I_s','Us':'U_s','Tau':r'\tau','tau':r'\tau','lambda':r'\lambda','beta':r'\beta','alpha':r'\alpha','omega':r'\omega','pi':r'\pi'}

# Unambiguous component and bias-point names also occur alone in prose.
# Re remains the real-part operator; authors must write R_e for emitter R.
ALIASES.update({name:tex for name,tex in [
 ('Rb','R_b'),('Rc','R_c'),('Rd','R_d'),('Rs','R_s'),
 ('Rf','R_f'),('Rg','R_g'),('Ri','R_i'),('Ro','R_o'),
 ('Rac','R_ac'),('Kn','K_n'),('Kp','K_p'),
 ('VGSQ','V_GSQ'),('VDSQ','V_DSQ'),('VBEQ','V_BEQ'),('VCEQ','V_CEQ'),
 ('VBQ','V_BQ'),('VCQ','V_CQ'),('VEQ','V_EQ'),('VGQ','V_GQ'),
 ('VDQ','V_DQ'),('VSQ','V_SQ'),('ICQ','I_CQ'),('IBQ','I_BQ'),
 ('IEQ','I_EQ'),('IDQ','I_DQ'),('ICM','I_CM'),('PCM','P_CM')
]})

# Plain English followed by a number (chapter6, about3) is not a product
# of letter variables with a final subscript. Keep recognized circuit names.
INDEXED_NAMES=set(SCOPED_SUBS)|set(ALIASES)|{'RC','LC','sRC','sCR','sC','sR','jC','jR','jL'}
INDEXED_NAMES.update(re.sub(r'\d+$','',base+sub) for base,subs in SCOPED_SUBS.items() for sub in subs)

def identifier(word):
    stem=re.match(r'[A-Za-z]+(?=\d)',word)
    if stem and '_' not in word:
        if stem[0] in {'is','as','at','and','to','of','in','on','or','for','by'}:return None
        if len(stem[0])>1 and stem[0] not in INDEXED_NAMES:return None
    if word in ('An','At','In','If','It','As','DC','AC','SI','PDF','PIV','TI','SPICE','NMOS','PMOS','CMOS','FET','JFET','BJT','BiFET','CMRR','RMS','KCL','KVL','NPN','PNP','BALANCE'):return None
    if word=='Re':return r'\operatorname{Re}'
    if word in ('K′_nW','i_sR'):
        return {"K′_nW":r"K'_n W",'i_sR':r'i_s R'}[word]
    for name in ('omega','lambda','alpha','beta','tau','pi','sum','int'):
        if word.startswith(name+'_'):return '\\'+name+'_{'+word[len(name)+1:]+'}'
    if re.fullmatch(r'[VvUuI][A-Zabdefgimnopsxyz]',word):word=word[0]+'_'+word[1]
    if re.fullmatch(UNITS,word):return r'\mathrm{'+word.replace('Ω',r'\Omega ').replace('μ',r'\mu ').replace('µ',r'\mu ')+'}'
    if word in MACROS:return None # Keep prose abbreviations as text.
    if word in FUNCTIONS:return '\\'+word
    if word in ALIASES:word=ALIASES[word]
    if word.startswith('\\'):return word
    # Genuine file/model identifiers are literal names, not variable subscripts.
    if re.fullmatch(r'(?:ngspice|LTspice|PSpice|IRF)\d+',word,re.I):return None
    if word.startswith(('UA741','BZX','1N')):return None
    result=[];i=0
    while i<len(word):
        base=word[i]
        if not (base.isascii() and base.isalpha()) and base not in GREEK:return None
        i+=1;sub='';accent=''
        if i<len(word) and word[i] in '′̇':accent=word[i];i+=1
        if i<len(word) and word[i]=='_':
            i+=1
            m=re.match(r'[A-Za-z0-9]+|[+−-]',word[i:])
            if not m:return None
            sub=m[0]
            # Separate adjacent factors only when the next factor has its own
            # explicit subscript: g_mR_s means g_m times R_s, not g_{mR}_s.
            for option in sorted(SCOPED_SUBS.get(base,[]),key=len,reverse=True):
                tail=word[i+len(option):]
                if sub.startswith(option) and re.match(r'[A-Za-z](?:_|[₀-₉])',tail):
                    sub=option;break
            i+=len(sub)
        if base=='j' and i<len(word) and word[i] in '0123456789':
            digits=re.match(r'\d+',word[i:])[0];result.append('j'+digits);i+=len(digits);continue
        while i<len(word) and (word[i] in SUB or word[i].isdigit()):
            sub+=word[i].translate(SUB_MAP);i+=1
        if i<len(word) and word[i]=='′':accent='′';i+=1
        symbol='\\'+GREEK[base]+' ' if base in GREEK else base
        if accent=='̇':symbol=r'\dot{'+symbol+'}'
        elif accent=='′':symbol+="'"
        result.append(symbol+('_{'+(r'\mathrm{'+sub+'}' if not sub.isdigit() else sub)+'}' if sub else ''))
    # Unmarked English words must not be interpreted as products of variables.
    if len(word)>1 and '_' not in word and not any(c in SUB or c in GREEK or c in '′̇' or c.isdigit() for c in word):
        if word not in {'RC','LC','sRC','sCR','sC','sR','jC','jR','jL','dq','kT','rD','ui','dt','du','di','dv','ds','Ri','Li','Cu','RiL','IR','UR'} and not word.isupper():return None
    return ''.join(result)

def scientific(value):
    match=re.fullmatch(r'(.+)[eE]([+−-]?\d+)',value)
    return match[1]+r'\times10^{'+match[2].replace('−','-')+'}' if match else value

def raw_to_tex(raw):
    raw=raw.replace('sqrt(', '√(')
    result=[];i=0
    while i<len(raw):
        ch=raw[i]
        q=QUANTITY.match(raw,i)
        if q:
            num=re.match(NUMBER,q[0])[0];unit=q[0][len(num):].strip()
            unit=unit.replace('µ','μ').replace('Ω',r'\Omega ').replace('μ',r'\mu ')
            end=q.end();power=''
            while end<len(raw) and raw[end] in SUP:
                power+=raw[end].translate(SUP_MAP);end+=1
            if not power and end<len(raw) and raw[end]=='^':
                exponent=re.match(r'\^([+-]?\d+)',raw[end:])
                if exponent:power=exponent[1];end+=len(exponent[0])
            unit_tex=r'\mathrm{'+unit+'}'+('^{'+power+'}' if power else '')
            # A numerical result such as 14/23 A carries A outside the ratio.
            # For t/20ms or V/40kΩ the quantity is the complete denominator.
            numeric_ratio=re.search(r'(?:^|[=+−(-])\s*'+NUMBER+r'\s*/\s*$',raw[:i])
            if numeric_ratio:result.append(scientific(num)+r'\, '+unit_tex)
            else:result.append('{'+scientific(num)+r'\,'+unit_tex+'}')
            i=end;continue
        number=re.match(NUMBER,raw[i:])
        if number:
            result.append(scientific(number[0]));i+=len(number[0]);continue
        m=WORD.match(raw,i)
        if m:
            word=m[0]
            # A differential belongs to the integrand, not to its last index.
            differential=re.fullmatch(r'([vui]_[A-Za-z]*\d+)d',word) and raw[m.end():m.end()+1] in ('τ','t')
            value=identifier(word[:-1]) + r'\,\mathrm{d}' if differential else identifier(word)
            if value is None:raise ValueError('Non-math word: '+word)
            # Space-separated result units remain outside a preceding fraction.
            # Quantities such as 20ms remain atomic denominator operands above.
            if i and raw[i-1].isspace() and re.fullmatch(UNITS,word):result.append(r'\,')
            result.append(value);i=m.end();continue
        if ch in GREEK:result.append('\\'+GREEK[ch]+' ');i+=1;continue
        if ch in SUP:
            power=''
            while i<len(raw) and raw[i] in SUP:power+=raw[i].translate(SUP_MAP);i+=1
            if power in ('+','-'):
                suffix=re.match(r'\d+',raw[i:])
                if suffix:power+=suffix[0];i+=len(suffix[0])
            result.append('^{'+power+'}');continue
        if ch in SUB:
            sub=''
            while i<len(raw) and raw[i] in SUB:sub+=raw[i].translate(SUB_MAP);i+=1
            result.append('_{'+sub+'}');continue
        if ch=='√':
            tail=raw[i+1:]
            if tail.startswith('('):
                depth=1;end=i+2
                while end<len(raw) and depth:
                    if raw[end]=='(':depth+=1
                    if raw[end]==')':depth-=1
                    end+=1
                if depth:raise ValueError('Unbalanced root')
                result.append(r'\sqrt{'+raw_to_tex(raw[i+2:end-1])+'}');i=end;continue
        if ch=='^' and i+1<len(raw) and raw[i+1]=='(':
            depth=1;end=i+2
            while end<len(raw) and depth:
                if raw[end]=='(':depth+=1
                if raw[end]==')':depth-=1
                end+=1
            if depth:raise ValueError('Unbalanced exponent')
            result.append('^{'+raw_to_tex(raw[i+2:end-1])+'}');i=end;continue
        result.append({'×':r'\times ','·':r'\cdot ','≤':r'\le ','≥':r'\ge ','≈':r'\approx ','≠':r'\ne ','→':r'\to ','⇒':r'\Rightarrow ','∥':r'\parallel ','√':r'\sqrt ','−':'-','Ω':r'\Omega '}.get(ch,ch));i+=1
    return ''.join(result)

TOKEN=re.compile('|'.join([
 r'(?P<id>\b\d+(?:\.\d+){2,}[a-z]?\b|\b\d{1,2}-\d{1,2}\b)',
 r'(?P<quantity>'+NUMBER+r'\s*'+UNITS+r'(?=$|[^A-Za-z_₀-₉]))',
 r'(?P<number>'+NUMBER+r')',r'(?P<word>'+WORD.pattern+r')',
 r'(?P<symbol>[αβγδεθλμµπρστφωΔΣ∑∞∫Ω±∠°'+SUB+SUP+r'])',
 r'(?P<operator>[=+−*/^<>≤≥≈≠×·→⇒∥√-])',
 r'(?P<fence>[()\[\]{}|])',r'(?P<space>\s+)',r'(?P<other>.)'
]))

def _legacy_text(s,language):
    tokens=list(TOKEN.finditer(s));out=[];i=0
    def plain(value):return html.escape(value.replace('/', '、' if language=='zh' else ' and '))
    while i<len(tokens):
        t=tokens[i];kind=t.lastgroup
        valid=kind in ('quantity','number','symbol','operator','fence','space') or (kind=='word' and identifier(t[0]) is not None)
        if not valid:
            out.append(plain(t[0]));i+=1;continue
        end=i;has_math=False;depth=0;last_good=i
        while end<len(tokens):
            u=tokens[end];k=u.lastgroup;w=u[0]
            if k=='word' and identifier(w) is None:break
            if k not in ('word','quantity','number','symbol','operator','fence','space'):break
            if k=='fence':
                if w in '([{':depth+=1
                elif w in ')]}':
                    if depth==0:break
                    depth-=1
            if k in ('word','quantity','symbol','operator'):has_math=True
            end+=1
            if depth==0 and k!='space':last_good=end
        end=last_good
        if end<=i:
            out.append(plain(t[0]));i+=1;continue
        raw=s[t.start():tokens[end-1].end()]
        # Preserve ordinary counts, standalone punctuation and English articles.
        substantive=any(c.isalpha() or c in GREEK or c in SUB or c in SUP for c in raw) or '/' in raw or '^' in raw
        if has_math and substantive and raw.strip() not in ('a','I','s','A','V') and not (language=='en' and re.fullmatch(r'\(\d+\)\s+[Aa]',raw.strip())):
            try:
                leading=raw[:len(raw)-len(raw.lstrip())]
                out.append(plain(leading)+'<span class="math-inline">'+render_math(raw_to_tex(raw.strip()))+'</span>')
            except (ValueError,IndexError,MissingSuperScriptOrSubscriptError,NoAvailableTokensError):out.append(plain(raw))
        else:out.append(plain(raw))
        i=end
    return ''.join(out)

@lru_cache(maxsize=20000)
def format_text(value,language='zh'):

    chunks=re.split(r'([A-Za-z][A-Za-z0-9_-]*\.(?:lib|cir|raw|log|csv|json|py|pdf))',str(value))
    return ''.join('<code>'+html.escape(chunk)+'</code>' if re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*\.(?:lib|cir|raw|log|csv|json|py|pdf)',chunk) else _format_chunk(chunk,language) for chunk in chunks)

def _format_chunk(value,language):
    parts=re.split(r'(\$[^$]+\$)',str(value))
    return ''.join('<span class="math-inline">'+render_math(p[1:-1])+'</span>' if p.startswith('$') and p.endswith('$') else _legacy_units(p,language) for p in parts)


def _legacy_units(value,language):
    value=value.replace('dB/十倍频','dB每十倍频')
    units={'rad/s':r'\frac{\mathrm{rad}}{\mathrm s}','dB/decade':r'\frac{\mathrm{dB}}{\mathrm{decade}}'}
    return ''.join('<span class="math-inline">'+render_math(units[p])+'</span>' if p in units else _legacy_text(p,language) for p in re.split(r'(rad/s|dB/decade)',value))

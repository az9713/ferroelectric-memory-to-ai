"""Editable conceptual SVG + abstract LEF/GDS, explicitly without process rules."""
from pathlib import Path
import json
import math
import struct
import datetime
import xml.etree.ElementTree as ET
H=Path(__file__).resolve().parent

def svg(name,w,h,body,title):
    text=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-label="{title}"><title>{title}</title><rect width="100%" height="100%" fill="#f8fafb"/><style>text{{font:15px sans-serif;fill:#192c38}}.small{{font-size:12px}}.label{{font-weight:bold}}</style>{body}</svg>'
    ET.fromstring(text);(H/(name+'.svg')).write_text(text,encoding='utf-8')

body=''
layers=[('Metal gate / injection barrier','#71899e'),('HZO ferroelectric (upper)','#69abb2'),('Al₂O₃ tunnel insert','#ddb969'),('HZO ferroelectric (lower)','#69abb2'),('Interface dielectric','#e4c990'),('Semiconductor channel: Si, Ge, or oxide','#b7c6a0')]
for i,(label,color) in enumerate(layers):
    y=45+i*42;body+=f'<rect x="45" y="{y}" width="350" height="35" fill="{color}"/><text x="420" y="{y+23}">{label}</text>'
body+='<text x="45" y="25" class="label">Conceptual laminated stack — not to scale</text><text x="45" y="332">Gate voltage divides across layers; trapped sheets alter displacement continuity.</text><text x="65" y="112">↑ P</text><text x="140" y="196">↓ P</text><text x="50" y="380" class="small">The channel is a separate material from the ferroelectric. This drawing specifies no fabrication process.</text>'
svg('cross-section',850,405,body,'Conceptual laminated ferroelectric gate stack')
body='<text x="30" y="28" class="label">Read path with abstract stateful device</text>'
for x,y,w,h,label in [(30,80,150,80,'Read/write driver'),(260,80,170,80,'Access isolation'),(510,80,170,80,'Stateful cell'),(510,250,170,70,'Sense amplifier')]:
    body+=f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#d7e8ed" stroke="#255965"/><text x="{x+12}" y="{y+45}">{label}</text>'
body+='<path d="M180 120H260 M430 120H510 M595 160V250" stroke="#255965" stroke-width="3" fill="none"/><text x="190" y="106" class="small">WL</text><text x="602" y="207" class="small">BL, parasitic C</text><text x="30" y="235">Drivers must supply write voltage, isolate reads,</text><text x="30" y="260">and protect low-voltage controller logic.</text><text x="30" y="365" class="small">Conceptual system schematic. Executed SPICE uses ideal read/write isolation and assumed cell conductance.</text>'
svg('cell-schematic',780,395,body,'Memory cell and read write peripheral roles')
body='<text x="30" y="28" class="label">16 × 8 memory macro — abstract geometry</text>'
for r in range(16):
    for c in range(8):body+=f'<rect x="{80+c*24}" y="{60+r*15}" width="20" height="11" fill="#85b9be" stroke="#38616a"/>'
body+='<rect x="35" y="60" width="30" height="240" fill="#dfc57b"/><text x="15" y="330">Row decoder</text><rect x="80" y="315" width="192" height="40" fill="#c3cfae"/><text x="92" y="341">Column sensing / I/O</text><text x="335" y="100">128 bit locations</text><text x="335" y="135">One word = 8 bits</text><text x="335" y="170">Logical address = 0…15</text><text x="335" y="220">4 µm cell pitch assumed</text><text x="335" y="255">80 × 100 µm macro footprint</text><text x="30" y="405" class="small">Rectangles are bit locations, not transistor layouts. Peripherals are not characterized.</text>'
svg('array-organization',720,435,body,'Abstract sixteen word eight bit array and periphery')
body='<text x="30" y="26" class="label">Conceptual chip floorplan — 600 × 400 µm</text><rect x="40" y="55" width="600" height="400" fill="#eef3f4" stroke="#244b5b" stroke-width="2"/><rect x="80" y="95" width="180" height="100" fill="#b5cfae" stroke="#244b5b"/><text x="95" y="130">Digital controller</text><text x="95" y="155" class="small">Generic synthesis verified</text><rect x="360" y="205" width="80" height="100" fill="#83b5bd" stroke="#244b5b"/><text x="454" y="240">Abstract research macro</text><text x="454" y="266" class="small">Placement ≠ fabrication</text><path d="M260 145H310V255H360" fill="none" stroke="#b18236" stroke-width="8"/><text x="264" y="340" class="small">Illustrative bus route; no parasitic extraction</text><text x="65" y="430">I/O ring, power grid, clock tree, and routing rules remain unspecified.</text><text x="30" y="490" class="small">This is an inspectable planning layout, not placement/routing of a characterized standard-cell library.</text>'
svg('floorplan',850,515,body,'Conceptual controller and abstract memory macro floorplan')

pins=['CLK','CS','WE']+[f'ADDR[{i}]' for i in range(4)]+[f'DIN[{i}]' for i in range(8)]+[f'DOUT[{i}]' for i in range(8)]+['VDD','VSS']
lef=['VERSION 5.8 ;','BUSBITCHARS "[]" ;','DIVIDERCHAR "/" ;','MACRO FE_MEMORY_ABSTRACT',' CLASS BLOCK ;',' ORIGIN 0 0 ;',' FOREIGN FE_MEMORY_ABSTRACT 0 0 ;',' SIZE 80 BY 100 ;',' SYMMETRY X Y ;']
pin_records=[]
for i,p in enumerate(pins):
    y=3+i*3.6;x=78 if p.startswith('DOUT') else 0
    direction='OUTPUT' if p.startswith('DOUT') else 'INOUT' if p in ['VDD','VSS'] else 'INPUT'
    use='POWER' if p=='VDD' else 'GROUND' if p=='VSS' else 'SIGNAL'
    lef += [f' PIN {p}',f'  DIRECTION {direction} ;',f'  USE {use} ;','  PORT','   LAYER abstract_metal1 ;',f'   RECT {x} {y:.2f} {x+2} {y+1:.2f} ;','  END',f' END {p}']
    pin_records.append({'name':p,'rect_um':[x,y,x+2,y+1],'direction':direction})
lef+=['END FE_MEMORY_ABSTRACT','END LIBRARY']
(H/'memory-abstract.lef').write_text('\n'.join(lef)+'\n')
# Minimal technology vocabulary allows parsing; it supplies no foundry rules.
(H/'abstract-tech.lef').write_text('VERSION 5.8 ;\nUNITS\n DATABASE MICRONS 1000 ;\nEND UNITS\nLAYER abstract_metal1\n TYPE ROUTING ;\n DIRECTION HORIZONTAL ;\n PITCH 1 ;\n WIDTH 1 ;\n SPACING 1 ;\nEND abstract_metal1\nEND LIBRARY\n')

def record(kind, dtype, payload=b''):
    if len(payload)%2:payload+=b'\0'
    return struct.pack('>HBB',len(payload)+4,kind,dtype)+payload
def i2(*v):return struct.pack('>'+'h'*len(v),*v)
def i4(*v):return struct.pack('>'+'i'*len(v),*v)
def real8(v):
    if v==0:return bytes(8)
    exponent=64
    while v>=1:v/=16;exponent+=1
    while v<1/16:v*=16;exponent-=1
    return bytes([exponent])+int(v*2**56).to_bytes(7,'big')
now=datetime.datetime.now();dt=[now.year,now.month,now.day,now.hour,now.minute,now.second]*2
gds=record(0,2,i2(600))+record(1,2,i2(*dt))+record(2,6,b'ABSTRACT_ONLY')+record(3,5,real8(.001)+real8(1e-9))
gds+=record(5,2,i2(*dt))+record(6,6,b'FE_MEMORY_ABSTRACT')
rects=[(0,0,80,100,100)]+[(16+c*4,18+r*4,19+c*4,21+r*4,101) for r in range(16) for c in range(8)]
for x0,y0,x1,y1,layer in rects:
    xy=[round(v*1000) for v in [x0,y0,x1,y0,x1,y1,x0,y1,x0,y0]]
    gds+=record(8,0)+record(13,2,i2(layer))+record(14,2,i2(0))+record(16,3,i4(*xy))+record(17,0)
gds+=record(7,0)+record(4,0);(H/'memory-abstract.gds').write_bytes(gds)
assert all(0<=p['rect_um'][0]<p['rect_um'][2]<=80 and 0<=p['rect_um'][1]<p['rect_um'][3]<=100 for p in pin_records)
# Verify record boundaries independently of construction and count geometry elements.
pos=0;boundaries=0
while pos<len(gds):
    length,kind,dtype=struct.unpack('>HBB',gds[pos:pos+4]);assert length>=4 and pos+length<=len(gds)
    boundaries+=kind==8;pos+=length
assert pos==len(gds) and boundaries==129
(H/'abstract-macro.json').write_text(json.dumps({'classification':'abstract, uncharacterized, not fabrication ready',
    'size_um':[80,100],'capacity_bits':128,'pitch_um':4,'pins':pin_records,
    'timing':'Assumed 10ns controller clock; 2-cycle read and 4-cycle write; not measured analog timings',
    'power':'Not characterized; Python educational energy model is separate and not this footprint',
    'layers':'GDS 100 boundary, 101 symbolic bit location; arbitrary layer numbers; LEF abstract_metal1 is not a foundry layer',
    'checks':'PASS: pin containment, 129 GDS boundaries, SVG XML; not DRC/LVS/PEX/STA'},indent=2))
print('PASS: conceptual diagrams, 25 contained pins, 129 abstract GDS boundaries')

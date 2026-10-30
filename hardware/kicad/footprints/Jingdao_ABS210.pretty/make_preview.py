"""Annotate the VTK render without changing the 3D model."""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
P=Path(__file__).resolve().parent
im=Image.open(P/'_vtk_render.png').convert('RGB')
# Tight crop to emphasize the housing and the small semicircular top-edge notch.
crop=im.crop((235,150,1085,740))
W,H=1260,975
bg='#f7f9fb'
canvas=Image.new('RGB',(W,H),bg)
render=crop.resize((1180,820),Image.Resampling.LANCZOS)
canvas.paste(render,(40,125))
d=ImageDraw.Draw(canvas)
header=ImageFont.truetype('/usr/share/fonts/truetype/lato/Lato-Bold.ttf',43)
sub=ImageFont.truetype('/usr/share/fonts/truetype/lato/Lato-Regular.ttf',24)
note=ImageFont.truetype('/usr/share/fonts/truetype/lato/Lato-Medium.ttf',23)
d.text((65,42),'Jingdao ABS210  |  C123897',font=header,fill='#26313c')
d.text((67,96),'Revised 3D model – clearer package indexing notch',font=sub,fill='#506070')
# VTK notch at ~500,435 -> cropped/resized image location 40+(500-235)*1180/850,
# 125+(435-150)*820/590 ≈ 408, 521
notch_xy=(407,521)
# Annotate the physical notch with an understated leader line, not a pin-1 dot.
d.rounded_rectangle((75,610,330,661),radius=9,fill='#ffffff',outline='#d2dae1',width=2)
d.text((93,623),'Indexing recess',font=note,fill='#374d61')
d.line([(330,635),(365,600),(399,545)], fill='#597c96', width=3, joint='curve')
d.polygon([(399,545),(388,558),(405,557)],fill='#597c96')
d.text((67,924),'Notch geometry is a visual approximation; pin numbering must follow the datasheet.',font=sub,fill='#5b6875')
canvas.save(P/'C123897_Jingdao_ABS210_preview.png',optimize=True)

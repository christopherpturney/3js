import numpy as np, json
from PIL import Image
from scipy import ndimage
S = 2.4236
imgs = {1:((928,667),2.7965), 2:((810,775),S), 3:((778,783),S), 4:((709.5,534),S), 5:((399.5,318),S), 6:((383.5,272),S), 7:((370.5,407),S)}
def world(k, px, py):
    (tx,ty),s = imgs[k]; return ((px-tx)/s, -(py-ty)/s)
# corners from the measurement endpoints (world ft, north up, origin = red pin)
M = json.load(open('scratchpad/markers.json'))
P = {k:[world(int(k),*p) for p in v["pts"]] for k,v in M.items()}
for k,v in P.items(): print(k, [tuple(round(c,1) for c in p) for p in v])
# rotation so the building west face (SW->NW) points straight up
sw, nw = np.array(P['6'][1]), np.array(P['6'][0])
d = nw - sw; theta = np.pi/2 - np.arctan2(d[1], d[0])
print("rotate deg", np.degrees(theta))
R = np.array([[np.cos(theta),-np.sin(theta)],[np.sin(theta),np.cos(theta)]])
json.dump({"theta":theta, "P":P}, open('scratchpad/frame.json','w'))
# mosaic in the rotated frame at RES px/ft
RES = 3.0
X0,X1,Y0,Y1 = -330, 330, -330, 330
W,H = int((X1-X0)*RES), int((Y1-Y0)*RES)
gx, gy = np.meshgrid(X0 + (np.arange(W)+0.5)/RES, Y1 - (np.arange(H)+0.5)/RES)
# rotated -> world
Rinv = R.T
wx = Rinv[0,0]*gx + Rinv[0,1]*gy; wy = Rinv[1,0]*gx + Rinv[1,1]*gy
samples = []
for k,((tx,ty),s) in imgs.items():
    a = np.array(Image.open(f'images/{k}.webp').convert('RGB')).astype(np.float32)
    px = tx + s*wx; py = ty - s*wy
    ok = (px>=0)&(px<a.shape[1]-1)&(py>=0)&(py<a.shape[0]-1)
    out = np.full((H,W,3), np.nan, np.float32)
    for c in range(3):
        out[...,c] = np.where(ok, ndimage.map_coordinates(a[...,c], [py, px], order=1, mode='nearest'), np.nan)
    samples.append(out)
st = np.stack(samples)                      # 7 x H x W x 3
med = np.nanmedian(st, axis=0)
cnt = np.sum(~np.isnan(st[...,0]), axis=0)
med = np.nan_to_num(med, nan=255).clip(0,255).astype(np.uint8)
Image.fromarray(med).save('scratchpad/mosaic.png')
json.dump({"RES":RES,"X0":X0,"Y1":Y1,"theta":theta}, open('scratchpad/mosaic.json','w'))
print("mosaic", W, H, "coverage>=3:", (cnt>=3).mean().round(2))

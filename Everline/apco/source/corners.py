import numpy as np, json
from scipy.optimize import least_squares
F = json.load(open('scratchpad/frame.json')); P = F["P"]; th = F["theta"]
R = np.array([[np.cos(th),-np.sin(th)],[np.sin(th),np.cos(th)]])
avg = lambda *ps: np.mean(np.array(ps), 0)
obs = {"NW": avg(P['1'][0], P['2'][1]), "NE": avg(P['2'][0], P['3'][0]),
       "SE": avg(P['3'][1], P['4'][0]), "SW": avg(P['1'][1], P['4'][1], P['5'][1])}
names = ["NW","NE","SE","SW"]; L = {("NW","NE"):308.00, ("NE","SE"):355.65, ("SE","SW"):359.64, ("SW","NW"):400.36}
x0 = np.concatenate([obs[n] for n in names])
def resid(x):
    q = {n: x[2*i:2*i+2] for i,n in enumerate(names)}
    r = [(np.linalg.norm(q[a]-q[b]) - l) * 5 for (a,b),l in L.items()]     # lengths weighted strongly
    r += list((x - x0) * 0.2)                                               # stay near observed spots
    return r
sol = least_squares(resid, x0).x
C = {n: sol[2*i:2*i+2] for i,n in enumerate(names)}
for (a,b),l in L.items(): print(f"{a}-{b}: fitted {np.linalg.norm(C[a]-C[b]):.2f} ft (measured {l})")
for n in names: print(n, "moved", round(np.linalg.norm(C[n]-obs[n]),2), "ft")
# building reference points (rotated frame)
Bnw, Bsw = np.array(P['6'][0]), np.array(P['6'][1])
rot = lambda p: (R @ np.asarray(p)).tolist()
out = {"corners": {n: rot(C[n]) for n in names}, "bldg_west_face": [rot(Bsw), rot(Bnw)],
       "m7": [rot(P['7'][1]), rot(P['7'][0])], "theta_deg": float(np.degrees(th))}
json.dump(out, open('scratchpad/site_ref.json','w'), indent=1)
print(json.dumps(out, indent=1))

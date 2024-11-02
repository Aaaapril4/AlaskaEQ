import numpy as np
import sys

value = float(sys.argv[1])
cptname = sys.argv[2]

with open(cptname, 'r') as f:
    lines = f.readlines()

v, r, g, b = [], [], [], []
for line in lines:
    line = line.split()
    try:
        v1, v2 = float(line[0]), float(line[2])
        rgb1 = [float(x) for x in line[1].split('/')]
        rgb2 = [float(x) for x in line[3].split('/')]
    except:
        break
    v.extend([v1, v2])
    r.extend([rgb1[0], rgb2[0]])
    g.extend([rgb1[1], rgb2[1]])
    b.extend([rgb1[2], rgb2[2]])

v, r, g, b = np.array(v), np.array(r), np.array(g), np.array(b)
r_new = np.interp(value, v, r)
g_new = np.interp(value, v, g)
b_new = np.interp(value, v, b)
print('/'.join([str(r_new), str(g_new), str(b_new)]))
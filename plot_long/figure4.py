import pandas as pd
import subprocess
import numpy as np
from intersect import intersect
import matplotlib.pyplot as plt

lines = [(-166.7289, 57.1638, -163.3779, 51.4890),
         (-166.5030, 57.2085, -162.2143, 51.7472),
         (-166.1261, 57.3225, -161.2374, 52.0261),
         (-165.5666, 57.5065, -160.4467, 52.2743),
         (-164.6230, 57.8112, -160.0024, 52.4208),
         (-163.6231, 58.0704, -159.5355, 52.5371),
         (-163.0620, 58.2165, -158.6702, 52.7535),
         (-162.7961, 58.2963, -157.2281, 52.73), #(-162.7961, 58.2963, -157.5648, 53.0666),
         (-162.8567, 58.2595, -155.64, 53.15), #(-162.8567, 58.2595, -156.2074, 53.5504),
         (-163.1317, 58.1186, -154.3015, 53.4), #(-163.1317, 58.1186, -155.3611, 53.9662),
         (-162.6869, 58.4257, -153.3305, 53.6), #(-162.6869, 58.4257, -154.7484, 54.3313),
         (-161.7346, 58.9493, -153.1611, 53.6), #(-161.7346, 58.9493, -154.5077, 54.4402),
         (-161.1099, 59.2547, -152.4240, 53.8), #(-161.1099, 59.2547, -153.8852, 54.7176),
         (-160.3342, 59.6126, -151.9108, 53.95), #(-160.3342, 59.6126, -153.3717, 54.9321),
         (-160.2092, 59.6835, -150.1560, 54.3), #(-160.2092, 59.6835, -152.2832, 55.4391), 
         (-159.9176, 59.8654, -149.0829, 54.8), #(-159.9176, 59.8654, -151.4315, 55.8980), 
         (-159.4877, 60.1441, -148.2828, 55.2), #(-159.4877, 60.1441, -150.7436, 56.2858),
         (-159.4511, 60.1783, -147.4977, 56.2), #(-159.4511, 60.1783, -149, 56.7),
         (-159.1358, 60.4845, -148, 57)]

catf = '/mnt/scratch/jieyaqi/alaska/alaska_long/catalogs_background.csv'
cat = pd.read_csv(catf)
trench = np.loadtxt('trench.dat')
trench[:, 0] = [x - 180 if x > 0 else x for x in trench[:, 0]]

def run_command(command):
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    return result.stdout

def get_catalog(i, lon1, lat1, lon2, lat2, cat, cut_off):
    print(i)
    line = run_command(f"gmt project -C{lon1}/{lat1} -E{lon2}/{lat2} -G0.1")
    line = np.array([x.split('\t') for x in line.strip().split('\n')])
    line = line.astype(float)
    trench_dist = intersect(line[:, 0], line[:, 1], trench[:, 0], trench[:, 1])
    
    slab = run_command(f"gmt project -C{lon1}/{lat1} -E{lon2}/{lat2} -G0.1 | gmt grdtrack -Gslab2.grd -T0.1 | awk '{{print $1, $2, $4}}' | gmt project -C{lon1}/{lat1} -E{lon2}/{lat2} -Q")
    slab = np.array([x.split('\t') for x in slab.strip().split('\n')])
    slab = slab[[slab[:, 2] != "NaN"]]
    slab = slab.astype(float)
    slab[:, 3] = slab[:, 3] - trench_dist
    
    cat_proj = run_command(f"awk -F, 'NR>1 {{print $2, $3}}' {catf} | gmt project -C{lon1}/{lat1} -E{lon2}/{lat2} -Q" )
    cat_proj = np.array([x.split('\t') for x in cat_proj.strip().split('\n')]) # _, _, dist, proj_dist, proj_lon, proj_lat
    cat_proj = cat_proj.astype(float)
    
    res = cat
    res["dist"] = cat_proj[:, 2] - trench_dist
    res[abs(cat_proj[:, 3]) <= cut_off].to_csv(f'{i}.csv', index = False)
    return res[abs(cat_proj[:, 3]) <= cut_off], slab[:, 2:4]

def plot_cross_section(ax, cat, slab, text):
    ax.set_xlim([-500, 100])
    ax.set_ylim([0, 250])
    ax.invert_yaxis()

    ax.scatter(cat['dist'], cat['depth_km'], s = 0.1, c = 'black')
    ax.plot(slab[:, 1], slab[:, 0], c = 'red')

    ax.text(60, 220, text, horizontalalignment='left', verticalalignment='top')
    return ax

fig, axes = plt.subplots(4, 5, figsize=(20, 8), sharex=True, sharey=True)
axes = axes.flatten()

for i, ax in enumerate(axes[:len(lines)]):
    cat_temp, slab = get_catalog(i+1, *lines[i], cat, 25)
    plot_cross_section(ax, cat_temp, slab, i+1)

plt.tight_layout()
plt.savefig('figure4.pdf', format = 'pdf')
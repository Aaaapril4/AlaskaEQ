import numpy as np
import pandas as pd
import swifter
from math import radians, sin, cos, asin, sqrt
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

volcano = pd.read_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/volcano_AP.csv')
volcano = volcano[~volcano['radius'].isna()]
volcano = volcano.sort_values("Longitude")
volcano = volcano.reset_index()
bin_edges = np.arange(0, 40+3, 3)
depth_bins = len(bin_edges) - 1
heatmap_data = np.zeros((depth_bins, len(volcano)))

def great_circle(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    '''
    Calculate the great circle distance between two points on the earth (specified in decimal degrees)
    '''
    
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371
    return c * r

# Create figure
cmap = mcolors.LinearSegmentedColormap.from_list("custom_cmap", ["#FFFFFF", "#DE7017"])
plt.figure(figsize=(8, 4))

cat = pd.read_csv('/mnt/scratch/jieyaqi/alaska/alaska_long/catalogs_new_10.csv')
labels = []
for i, row in volcano.iterrows():
    dist = cat.swifter.apply(lambda x: great_circle(x["longitude"], x["latitude"], row["Longitude"], row["Latitude"]), axis = 1)
    labels.append(row["Volcano Name"])
    vol_cat = cat[dist <= row["radius"] * 1.2]
    counts, _ = np.histogram(vol_cat['depth_km'], bins=bin_edges)
    
    if counts.max() > 0:
        counts = counts / counts.max()
    
    heatmap_data[:, i] = counts[::-1]  # Flip depth for correct Y-axis

# Create heatmap plot
c = plt.pcolormesh(np.arange(len(volcano)), bin_edges[-2::-1], heatmap_data, cmap=cmap, shading='auto')
plt.xticks(np.arange(0, len(volcano)), labels)
# Formatting
plt.ylim(40, 0)  # Invert Y-axis
plt.ylabel("Depth (km)")
plt.colorbar(c, label="Normalized Count", pad = 0.01)
plt.xlim(0-0.5, len(volcano)-0.5)
plt.tight_layout()
plt.savefig('/mnt/home/jieyaqi/code/AlaskaEQ/plot_long/figure7.pdf', format='pdf')
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

x_positions = np.arange(3, 20) + 0.5
# Create figure
cmap = mcolors.LinearSegmentedColormap.from_list("custom_cmap", ["#FFFFFF", "#56508E"])
# cmap = 'YlOrBr'
fig, axes = plt.subplots(3, 1, figsize=(8, 9), sharex=True, gridspec_kw={'height_ratios': [1, 1, 1]})
ax1, ax2, ax3 = axes  # Top and bottom histograms

# absolute depth distribution
bin_edges = np.arange(0, 200+10, 10)
depth_bins = len(bin_edges) - 1
# heatmap_data = np.zeros((depth_bins, 19))
heatmap_data = np.zeros((depth_bins, 17))

# for i in range(1, 20):
for i in range(3, 20):
    cat = pd.read_csv(f'/mnt/home/jieyaqi/code/AlaskaEQ/plot_long/{i}.csv')
    cat = cat[~cat['slab_normal_depth_km'].isna()]
    counts, _ = np.histogram(cat['depth_km'], bins=bin_edges)
    
    # Normalize counts
    if counts.max() > 0:
        counts = counts / counts.max()
    
    # Store in heatmap array (flip for correct orientation)
    # heatmap_data[:, i-1] = counts[::-1]  # Flip depth for correct Y-axis
    heatmap_data[:, i-3] = counts[::-1]  # Flip depth for correct Y-axis

# Create heatmap plot
# c = ax1.pcolormesh(np.arange(1, 21), bin_edges[::-1], heatmap_data, cmap=cmap, shading='auto')
c = ax1.pcolormesh(np.arange(3, 21), bin_edges[::-1], heatmap_data, cmap=cmap, shading='auto')
# Formatting
ax1.set_ylim(200, 0)  # Invert Y-axis
# ax1.set_xlim(1, 20)
ax1.set_xlim(3, 20)
ax1.set_ylabel("Depth (km)")
ax1.set_xticks(x_positions)
# ax1.set_xticklabels(range(1, 20))
ax1.set_xticklabels(range(3, 20))
fig.colorbar(c, orientation='vertical', ax=ax1, pad = 0.01)


bin_edges = np.arange(0, 50+2.5, 2.5)
depth_bins = len(bin_edges) - 1
# heatmap_data = np.zeros((depth_bins, 19))
heatmap_data = np.zeros((depth_bins, 17))
# for i in range(1, 20):
for i in range(3, 20):
    cat = pd.read_csv(f'/mnt/home/jieyaqi/code/AlaskaEQ/plot_long/{i}.csv')
    cat = cat[(cat['slab_normal_depth_km'] > 5) & (cat['depth_km'] < 120) & (cat['dist'] < -100) & (cat['dist'] > -275)& (cat['time2background'] < 0)]
    counts, _ = np.histogram(cat['slab_normal_depth_km'], bins=bin_edges)
    counts = counts / counts.max()
    # heatmap_data[:, i-1] = counts[::-1]  # Flip depth for correct Y-axis
    heatmap_data[:, i-3] = counts[::-1]  # Flip depth for correct Y-axis

# c = ax2.pcolormesh(np.arange(1, 21), bin_edges[::-1], heatmap_data, cmap=cmap, norm=mcolors.Normalize(vmin=0, vmax=0.7), shading='auto')
c = ax2.pcolormesh(np.arange(3, 21), bin_edges[::-1], heatmap_data, cmap=cmap, norm=mcolors.Normalize(vmin=0, vmax=0.7), shading='auto')

ax2.set_ylim(5, 50)  # Invert Y-axis
# ax2.set_xlim(1, 20)
ax2.set_xlim(3, 20)
ax2.invert_yaxis()
ax2.set_ylabel("Slab-normal Depth (km)")
ax2.set_xticks(x_positions)
# ax2.set_xticklabels(range(1, 20))
ax2.set_xticklabels(range(3, 20))
fig.colorbar(c, orientation='vertical', ax=ax2, pad = 0.01)

# outer-rise
bin_edges = np.arange(0, 50+2.5, 2.5)
depth_bins = len(bin_edges) - 1
# heatmap_data = np.zeros((depth_bins, 19))
heatmap_data = np.zeros((depth_bins, 17))
for i in range(3, 20):
# for i in range(1, 20):
    cat = pd.read_csv(f'/mnt/home/jieyaqi/code/AlaskaEQ/plot_long/{i}.csv')
    # cat = cat[cat['time2background'] < -882]
    cat = cat[cat['slab_normal_depth_km'].isna()]
    counts, _ = np.histogram(cat['depth_km'], bins=bin_edges)

    # heatmap_data[:, i-1] = counts[::-1]  # Flip depth for correct Y-axis
    heatmap_data[:, i-3] = counts[::-1]  # Flip depth for correct Y-axis

# Create heatmap plot
# c = ax3.pcolormesh(np.arange(1, 21), bin_edges[::-1], heatmap_data, cmap=cmap, norm=mcolors.Normalize(vmin=0, vmax=20), shading='auto')
c = ax3.pcolormesh(np.arange(3, 21), bin_edges[::-1], heatmap_data, cmap=cmap, norm=mcolors.Normalize(vmin=0, vmax=60), shading='auto')

ax3.set_ylim(0, 50)  # Invert Y-axis
ax3.invert_yaxis()
# ax3.set_xlim(1, 20)
ax3.set_xlim(3, 20)
ax3.set_ylabel("Depth (km)")
ax3.set_xticks(x_positions)
# ax3.set_xticklabels(range(1, 20))
ax3.set_xticklabels(range(3, 20))
fig.colorbar(c, orientation='vertical', ax=ax3, pad = 0.01)

# plt.tight_layout()
plt.subplots_adjust(hspace=0.1, wspace=0.05)
plt.savefig('figure5.pdf', format='pdf')
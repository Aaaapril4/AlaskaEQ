import numpy as np
from scipy.interpolate import griddata
import sys
import obspy
from shapely.geometry import LineString

def line2grid(lon, lat, lon_grid, lat_grid):
    z_grid = np.zeros_like(lon_grid)
    line_value = 1  
    for i in range(len(lon)):
        nearest_x = np.abs(lon_grid[0] - lon[i]).argmin()
        nearest_y = np.abs(lat_grid[:,0] - lat[i]).argmin()
    z_grid[nearest_y, nearest_x] = line_value
    return z_grid

line1 = sys.argv[1] # line
line2 = sys.argv[2] # trench
# line1 = 'plot/line1'
# line2 = 'plot/line2'
# read grid
lon_1, lat_1, _ = np.loadtxt(line1, unpack=True)
lon_2, lat_2 = np.loadtxt(line2, unpack=True)
lon_2 = [x - 180 if x > 0 else x for x in lon_2]
line1 = LineString([[lon_1[i], lat_1[i]] for i in range(len(lon_1))])
line2 = LineString([[lon_2[i], lat_2[i]] for i in range(len(lon_2))])
intersection = line1.intersection(line2)
if len(list(intersection.coords)) != 0:
    [(lon, lat)] = list(intersection.coords)
    d, _, _ = obspy.geodetics.base.gps2dist_azimuth(lat, lon, lat_1[0], lon_1[0])
    print(d/1000)

# ## using grid
# lon_grid = np.linspace(-166, -148, 10001)
# lat_grid = np.linspace(50, 60, 10001)
# lon_grid, lat_grid = np.meshgrid(lon_grid, lat_grid)

# line1_grid = line2grid(lon_1, lat_1, lon_grid, lat_grid)
# line2_grid = line2grid(lon_2, lat_2, lon_grid, lat_grid)

# # Calculate the difference grid
# diff_grid = line1_grid - line2_grid

# # Find where the difference is close to zero
# tolerance = 1e-6
# intersection_mask = (np.abs(diff_grid) < tolerance) & (line1_grid > 0.95) & (line2_grid > 0.95)
# intersection_points = np.argwhere(intersection_mask)

# # Extract the x and y coordinates of the intersection points
# intersection_coords = [(lon_grid[x][y], lat_grid[x][y]) for [x, y] in intersection_points]

# dist = []
# for [lon, lat] in intersection_coords:
#     d, _, _ = obspy.geodetics.base.gps2dist_azimuth(lat, lon, lat_1[0], lon_1[0])
#     dist.append(d)
# sum(dist) / len(dist)
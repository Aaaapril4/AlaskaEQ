import obspy
import numpy as np
import sys

fname = sys.argv[1]
lon_column, lat_column = [int(x) for x in sys.argv[2:4]]
start_lon, start_lat = [float(x) for x in sys.argv[4:6]]
vol = float(sys.argv[6])
if len(sys.argv) == 8:
    sep = sys.argv[7]
    data = np.loadtxt(fname, dtype=str, delimiter=sep)
else:
    sep = " "
    data = np.loadtxt(fname, dtype=str)
if len(data) != 0:
    for i in range(len(data[:,0])):
        d, _, _ = obspy.geodetics.base.gps2dist_azimuth(float(data[i, lat_column]), float(data[i, lon_column]), start_lat, start_lon)
        print(sep.join(np.concatenate([[d/1000 - vol], data[i]])))
import sys
import numpy as np
import subprocess


if __name__ == '__main__':
   fname = sys.argv[1]
   lon0, lat0, lon1, lat1 = sys.argv[2].split('/')
   trench = float(sys.argv[6])
   cut_off = float(sys.argv[3])
   lon_column, lat_column = int(sys.argv[4]), int(sys.argv[5])
   if len(sys.argv) == 8:
      sep = sys.argv[7]
      data = np.loadtxt(fname, dtype=str, delimiter=sep, skiprows=1)
   else:
      sep = " "
      data = np.loadtxt(fname, dtype=str, skiprows=1)

   result = subprocess.run(" ".join(["awk -F, 'NR>1{print $"+str(lon_column+1)+", $"+str(lat_column+1)+"}'", fname, "|", "gmt", "project", "-C"+lon0+"/"+lat0, "-E"+lon1+"/"+lat1, "-Q"]), shell=True, capture_output=True, text=True)
   result = result.stdout.strip().split('\n')
   for i in range(len(result)):
      _, _, dist, proj_dist, proj_lon, proj_lat = result[i].split('\t')
      dist = float(dist)
      if abs(float(proj_dist)) < cut_off:
         print(sep.join(np.concatenate([[dist - trench, proj_lon, proj_lat], data[i]])))
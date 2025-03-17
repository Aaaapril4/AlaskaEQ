from collections import defaultdict
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

isc_cat = pd.read_csv('../data/isc_catalog.csv')
cat = pd.read_csv('/mnt/scratch/jieyaqi/alaska/alaska_long/catalogs_new_10.csv')

plt.rcParams["font.size"] = 18

isc_cat['year'] = isc_cat['time'].apply(lambda x: x.split('-')[0])
years = defaultdict(int)
def count(y):
    years[y] += 1
    return

isc_cat['year'].apply(lambda x: count(x))
years = sorted(years.items(), key=lambda x: x[0])
isc_years = years.copy()

cat['year'] = cat['time'].apply(lambda x: x.split('-')[0])
years = defaultdict(int)
cat['year'].apply(lambda x: count(x))
years = sorted(years.items(), key=lambda x: x[0])
cat_years = years.copy()

plt.figure(figsize=(15, 7))

bar_width = 0.45

isc_bar = plt.bar(np.arange(2023-1997+1) - bar_width/2, [x[1] for x in isc_years], width=bar_width, color='#FF6AAD', label='ISC Catalog')
# plt.bar_label(isc_bar, padding=1)
bar_long = plt.bar(np.arange(2023-1997+1) + bar_width/2, [x[1] for x in cat_years], width=bar_width, color='#6868FF', label='Catalog in this study')
# plt.bar_label(bar_long, padding=1)

plt.xlabel("Year")
# plt.xticks(ticks=np.arange(2022-1997+1, 5), labels=[x[0] for x in isc_years])
plt.xticks(ticks=[3, 8, 13, 18, 23], labels=[2000, 2005, 2010, 2015, 2020])
plt.legend()
plt.margins(x=0.01)
plt.tight_layout()

# plt.show()
plt.savefig('figure3.pdf', format = 'pdf')
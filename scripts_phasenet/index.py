# %%
from obspy.clients.filesystem.tsindex import Indexer
from obspy.clients.filesystem.tsindex import Client
from obspy import UTCDateTime

# %%
# indexer = Indexer("./tongaml_continious_seeds", filename_pattern='*.mseed',index_cmd="/mnt/home/xiziyi/source/mseedindex/mseedindex",parallel=1)

# %%
# indexer.run()

# %%


# %%
indexer = Indexer("./phasenet/test", filename_pattern='*.mseed',
                  index_cmd="/mnt/home/jieyaqi/code/mseedindex/mseedindex", parallel=1)

# %%
indexer.run()

# %%

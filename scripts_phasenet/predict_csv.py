import pandas as pd

Pthres = 0.5
Sthres = 0.3
picks = pd.read_csv('/mnt/scratch/jieyaqi/alaska/phasenet/result/phase_arrivals.csv')
picks['id'] = picks.apply(lambda x: x['net']+'.'+x['sta']+'..BH', axis=1)
picks['timestamp'] = picks['time']
picks['prob'] = picks['amp']
picks['type'] = picks['phase']
picks = picks.replace('TP', 'P')
picks = picks.replace('TS', 'S')
picks['timestamp'] = picks['timestamp'].apply(lambda x: pd.Timestamp(x))
picks = picks[picks['type'].isin(['P', 'S'])]
picksp = picks[picks['type']=='P']
pickss = picks[picks['type']=='S']
picks = pd.concat([picksp[picksp['prob'] >= Pthres], pickss[pickss['prob'] >= Sthres]])
picks.to_csv('PhaseNetPicks.csv', 
             columns=['id', 'timestamp', 'type', 'prob'], 
             date_format='%Y-%m-%dT%H:%M:%S.%f',
             index = False)
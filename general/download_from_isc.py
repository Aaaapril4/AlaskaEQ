from urllib.request import urlopen
import re
import pandas as pd

def remove_html_tags(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def fetch_url(url):
    with urlopen(url) as response:
        body = response.read()
        content = body.decode('utf-8')
    content = remove_html_tags(content)
    content = content.replace(' ', '')
    c_list = content.split('\n')
    c_list = list(filter(None, c_list))

    # find the start of the form
    i = 0
    while 'EVENTID' not in c_list[i]:
        i += 1
    start = i
    # find the end of the form
    i = -1
    while len(c_list[i].split(',')) != len(c_list[start].split(',')):
        i -= 1
    end = i

    c_list = c_list[start: end + 1]
    c_list = [x.split(',') for x in c_list]
    return c_list

def clean_arrival(c_list):
    c_list = [x[:15] for x in c_list]
    isc = pd.DataFrame(c_list[1:], columns=c_list[0])
    isc = isc[isc['REPPHASE'] !='IAML']
    isc = isc[isc['REPPHASE'] != '']
    isc['timestamp'] = isc['DATE'] + 'T' + isc['TIME']
    isc['type'] = isc['REPPHASE'].apply(lambda x: x[0])
    isc = isc[['EVENTID', 'STA', 'timestamp', 'type']]
    isc = isc.rename(columns={'EVENTID': 'event_index', 'STA':'station'})
    return isc


def clean_catalog(c_list):
    c_list = [x[:9] + ['|'.join(x[9:])] if x[9]!='' else x[:9] + [''] for x in c_list ]
    c_list = [x[:10] for x in c_list]
    isc = pd.DataFrame(c_list[1:], columns=c_list[0])
    isc['time'] = isc['DATE'] + 'T' + isc['TIME']
    isc = isc[['EVENTID', 'AUTHOR', 'time', 'LAT', 'LON', 'DEPTH', 'AUTHOR|TYPE|MAG']]
    isc = isc.rename(columns={'EVENTID': 'event_index', 
                              'AUTHOR':'author', 
                              'LAT': 'latitude', 
                              'LON': 'longitude', 
                              'DEPTH': 'depth', 
                              'AUTHOR|TYPE|MAG': 'magnitude'})
    return isc


if __name__ == '__main__':
    c_list = fetch_url('http://www.isc.ac.uk/cgi-bin/web-db-run?iscreview=on&out_format=CSV&ttime=on&phaselist=&sta_list=&stn_ctr_lat=&stn_ctr_lon=&stn_radius=&max_stn_dist_units=deg&stnsearch=RECT&stn_top_lat=50&stn_bot_lat=60&stn_left_lon=-166&stn_right_lon=-148&stn_srn=&stn_grn=&searchshape=RECT&bot_lat=50&top_lat=60&left_lon=-166&right_lon=-148&ctr_lat=&ctr_lon=&radius=&max_dist_units=deg&srn=&grn=&start_year=1980&start_month=1&start_day=1&start_time=00%3A00%3A00&end_year=2023&end_month=12&end_day=31&end_time=23%3A59%3A59&min_dep=&max_dep=&min_mag=&max_mag=&req_mag_type=Any&req_mag_agcy=AEIC&include_links=on&request=STNARRIVALS')
    isc = clean_arrival(c_list)
    isc.to_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/isc_arrival_reviewed.csv', index = False)

    c_list = fetch_url('http://www.isc.ac.uk/cgi-bin/web-db-run?request=REVIEWED&out_format=CATCSV&searchshape=RECT&bot_lat=50&top_lat=60&left_lon=-166&right_lon=-148&ctr_lat=&ctr_lon=&radius=&max_dist_units=deg&srn=&grn=&start_year=1980&start_month=1&start_day=01&start_time=00%3A00%3A00&end_year=2023&end_month=12&end_day=31&end_time=23%3A59%3A59&min_dep=&max_dep=&min_mag=&max_mag=&req_mag_type=&req_mag_agcy=AEIC&include_links=on')
    isc = clean_catalog(c_list)
    isc.to_csv('/mnt/home/jieyaqi/code/AlaskaEQ/data/isc_catalog_reviewed.csv', index=False)

from olpy import simulate
from sqlalchemy import create_engine
import numpy as np
import pandas as pd
import uuid
from datetime import datetime
import time
import random
from olpy.flight import Flight
from shapely.geometry import Point, Polygon
from geopy.geocoders import Nominatim
locator = Nominatim(user_agent="myGeocoder")


long_beach_beat = Polygon([(33.765006, -118.203539),
(33.819782, -118.204589),
(33.804562, -118.144767),
(33.756065, -118.139132),
(33.765006, -118.203539)])

# Util functions

def generate_random_lat_long(number, polygon):
    list_of_points = []
    minx, miny, maxx, maxy = polygon.bounds
    counter = 0
    while counter < number:
        pnt = Point(random.uniform(minx, maxx), random.uniform(miny, maxy))
        if polygon.contains(pnt):
            list_of_points.append((pnt.x, pnt.y))
            counter += 1
    return list_of_points

def random_date_in_date_range(start, end):
    #current time in unix utc
    start_timestamp = datetime.strptime(start,'%Y-%m-%d').timestamp()
    end_timestamp = datetime.strptime(end,'%Y-%m-%d').timestamp()

    random_timestamp = np.random.randint(start_timestamp, end_timestamp)

    random_date = datetime.fromtimestamp(random_timestamp).strftime('%Y-%m-%d')

    return random_date

def random_date_up_to_x_days_after_previous_date(date, days):
    timestamp = datetime.strptime(date,'%Y-%m-%d').timestamp()
    days_in_seconds = days*24*60*60
    one_day = 24*60*60
    time_difference = np.random.randint(days_in_seconds) + one_day #add a day so possible range is 1-x days rather than 0-x
    new_date = datetime.fromtimestamp(timestamp + time_difference).strftime('%Y-%m-%d')
    return new_date

# Dicts for creating classes


council_districts = {
    'Santa Clara': 0.2,
    'San Mateo': 0.5,
    'San Francisco': 0.3
}

stay_away_dict = {
    100: 0.4,
    200: 0.3,
    300: 0.2,
    400: 0.1
}


#Classes which generate data

class GuidesPerson():
    '''
    Generate Person Info (ID, FirstName, MiddleName, LastName, SSN, Sex, DOB)
    Include Mugshot and Drivers License in Person Info (ImageID, Image, DLNo)
    '''
    def __init__(self, key):

        self.inmate = simulate.subjectgenerator.Subject()
        self.inmate.generate()
        self.inmate = vars(self.inmate)['subject']
        self.inmate['SubjectIdentification'] = str(uuid.uuid1())

        self.inmate['ImageID'] = str(uuid.uuid1())
        self.inmate['Image'] = 'Bytes'

        self.inmate['DLNo'] = np.random.randint(1000000,9999999)

        today = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d')

        probation = 'Y'

        if probation == 'Y':
            self.inmate['ProbationID'] = str(uuid.uuid1())
            self.inmate['ProbationStart'] = random_date_in_date_range('2015-01-01', today)
            self.inmate['ProbationEnd'] = random_date_up_to_x_days_after_previous_date(self.inmate['ProbationStart'], 1000)


    @property
    def __dict__(self):
        return self.inmate

class Case():
    '''
    Generate Cases and assign to Council Districts (CaseID, CouncilDistrict) and randomly distribute them to people
    '''
    def __init__(self, sid):
        
        self.case = {}
        self.case['SubjectIdentification'] = sid
        self.case['CaseID'] = str(uuid.uuid1())
        self.case['CouncilDistrict'] = np.random.choice(list(council_districts.keys()), p = list(council_districts.values()))
        
    @property
    def __dict__(self):
        return self.case

class ServiceOfProcess():
    '''
    Generate serviceofprocess (StayAwayOrderID,  StayAwayRadius,StayAwayRadiusStr, StayAwayUnits)
    Include Location and Beat in generation of serviceofprocess (Coordinates, Lat, Long, Address, City, State)
    '''
    def __init__(self, sid):
        
        self.serviceofprocess = {}
        self.serviceofprocess['SubjectIdentification'] = sid
        self.serviceofprocess['StayAwayOrderID'] = str(uuid.uuid1())
        self.serviceofprocess['StayAwayRadius'] = np.random.choice(list(stay_away_dict.keys()), p = list(stay_away_dict.values()))
        sar = self.serviceofprocess['StayAwayRadius']
        self.serviceofprocess['StayAwayUnits'] = "Yards"
        
        
        self.serviceofprocess['Beat'] = 'Long Beach'
        
        self.beat = self.serviceofprocess['Beat']
        
        self.serviceofprocess['Coordinates'] = generate_random_lat_long(1, long_beach_beat)[0]
        self.serviceofprocess['Lat'] = self.serviceofprocess['Coordinates'][0]
        self.serviceofprocess['Long'] = self.serviceofprocess['Coordinates'][1]
        
        
        self.sdlat = self.serviceofprocess['Lat']
        self.sdlong = self.serviceofprocess['Long']
        
        self.coordinates = f"{self.sdlat},{self.sdlong}"
        self.serviceofprocess['Coordinates'] = self.coordinates


        try:
        
            self.location = locator.reverse(self.coordinates)
            self.address = ""
        
            self.city = ""

            if 'house_number' in self.location.raw['address'].keys():
                self.address += self.location.raw['address']['house_number']+ " "

            if 'road' in self.location.raw['address'].keys():
                self.address += self.location.raw['address']['road']

            if 'town' in self.location.raw['address'].keys():
                self.city = self.location.raw['address']['town']

            if 'city' in self.location.raw['address'].keys():
                self.city = self.location.raw['address']['city']


            self.serviceofprocess['Address'] = self.address

            self.serviceofprocess['City'] = self.city
            self.serviceofprocess['State'] = self.location.raw['address']['state']
            
        except:
            print('this request didnt work')
            
        
        
        
    @property
    def __dict__(self):
        return self.serviceofprocess

# Main methods which create and join dataframes based on classes

def make_df(Enttype, keylist):

    dictlist = []

    for i in keylist:
        data = Enttype(i).__dict__ # right now i have certain dict methods returning a list -
                                    #this is a bit confusing and i would like to find a better way to design

        if isinstance(data, list):
            dictlist.extend(data)

        else:
            dictlist.append(data)

    return pd.DataFrame(dictlist).astype('object')

# def join_rows_probablistically(df1,df2,n,join_p):
#     df1_copy = df1.copy()
#     df2_copy = df2.copy()
#     dictlist = []
#     for i in range(n):
#         has_case = 'Y'
#         df1_sample = df1_copy.sample().to_dict('record')[0]
#         df2_sample = df2_copy.sample().to_dict('record')[0]
        
#         if has_case == 'Y':
#             result = {**df1_sample,**df2_sample}

            
#         else:
#             result = {**df1_sample}
            
#         dictlist.append(result)
#     return pd.DataFrame(dictlist).astype('object')

# Make and join all the data

lbpdf = make_df(GuidesPerson, list(range(500)))
case_df = make_df(Case, list(lbpdf['SubjectIdentification']))
sop_df = make_df(ServiceOfProcess, list(lbpdf['SubjectIdentification']))

# case_sop_df = join_rows_probablistically(case_df, sop_df, 2000, 1)
# full = join_rows_probablistically(lbpdf, case_sop_df, 500, 1)

half = lbpdf.set_index('SubjectIdentification').join(case_df.set_index('SubjectIdentification'))
full = half.join(sop_df.set_index('SubjectIdentification')).reset_index()

date_columns = ['dob']

for col in date_columns:
    full[col] = full[col].astype(np.datetime64).dt.strftime('%Y-%m-%d')
    full.loc[full[col] == 'NaT', col] = np.nan

date_to_datetime_columns = ['ProbationEnd','ProbationStart']
datetime_columns = [k for (k,v) in full.dtypes.items() if v.type == np.datetime64] + date_to_datetime_columns


for col in datetime_columns:
    full[col] = full[col].apply(lambda x: pd.Timestamp(x).tz_localize("America/Los_Angeles").to_pydatetime())

def make_assn_hash(df, col1, col2, name):
    cols = [col1,col2]
    c1nn = df.loc[df[cols].notnull().all(axis=1), col1].astype(str)
    c2nn = df.loc[df[cols].notnull().all(axis=1), col2].astype(str)
    combined_cols =  c1nn + c2nn
    assn_hash = combined_cols.apply(lambda x: hash(x+name))
    return assn_hash

def make_assn_cols(df, fd):
    for k, v in fd['associationDefinitions'].items():
        col_string = f"assn_{k}"
        src, dst = v['src'], v['dst']
        srccol = fd['entityDefinitions'][src]['properties'][0]['column']
        dstcol = fd['entityDefinitions'][dst]['properties'][0]['column']
        df[col_string] = make_assn_hash(df, srccol, dstcol, k)


fl = Flight()
fl.deserialize('guides_demo.yaml')
guides_fd = fl.schema

make_assn_cols(full, guides_fd)

engine = create_engine('postgresql://nicholas@localhost:5432/test')
full.to_sql("guides_demo3", engine)
import os 
import pandas as pd

from thefuzz import process

OUT_DIR = os.path.join('src', '_data', 'viz', 'lcip')
DATA_DIR = os.path.join('data', 'lcip', 'lcip_grant_stats.xlsx')
INSPIRE_DATA = os.path.join('data', 'lcip', 'inspire.xlsx')
WARD_DATA = os.path.join('data', 'leeds_wards.csv')

# Function to fuzzy match and merge dataframes
def fuzzy_merge(df1, df2, key1, key2, threshold=90):
    s = df2[key2].tolist()

    m = df1[key1].apply(lambda x: process.extractOne(x, s, score_cutoff=threshold))
    df1['matches'] = m.apply(lambda x: x[0] if x else None)
    df1['score'] = m.apply(lambda x: x[1] if x else None)

    merged = pd.merge(df1, df2, left_on='matches', right_on=key2, how='left')
    merged.drop(['matches', 'score'], axis=1, inplace=True)
    return merged

if __name__ == "__main__":

    # Process Inspire data

    inspire_data = pd.read_excel(INSPIRE_DATA).drop(columns={'R2','R3','R4'})
    ward_data = pd.read_csv(WARD_DATA)

    wards_applied = inspire_data.loc[inspire_data['THEME']== 'WARDS - APPLICANT BASED']
    wards_received = inspire_data.loc[inspire_data['THEME']== 'WARDS - RECEIVING ACTIVITY']

    applied = (
        fuzzy_merge(ward_data, wards_applied, 'WD21NM', 'METRIC')
        .dropna()
        .drop(columns='WD21NM')
        .rename(columns={
            'WD21CD': 'ward_code',
            'THEME': 'metric',
            'METRIC': 'ward_name',
            'R1': 'value'
        })).to_csv(os.path.join(OUT_DIR, 'inspire', 'applications_by_ward.csv'))
    
    funded = (
        fuzzy_merge(ward_data, wards_received, 'WD21NM', 'METRIC')
        .dropna()
        .drop(columns='WD21NM')
        .rename(columns={
            'WD21CD': 'ward_code',
            'THEME': 'metric',
            'METRIC': 'ward_name',
            'R1': 'value'
        })).to_csv(os.path.join(OUT_DIR, 'inspire', 'funding_received_by_ward.csv'))

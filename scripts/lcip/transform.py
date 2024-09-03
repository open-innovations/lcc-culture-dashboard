import os 
import pandas as pd
from pathlib import Path

from thefuzz import process

OUT_DIR = os.path.join('src', '_data', 'viz', 'lcip')
DATA_DIR = os.path.join('data', 'lcip')
WARD_DATA = os.path.join('data', 'leeds_wards.csv')

diversity_metrics = [
    'AGE (APPLIED)',
    'DISABILITY (APPLIED)',
    'SEX (APPLIED)',
    'GENDER REGISTERED AT BIRTH (APPLIED)',
    'ETHNIC ORIGIN (APPLIED)',
    'SEXUAL ORIENTATION (APPLIED)',
    'RELIGIOUS BELIEF (APPLIED)',
    'CARER (APPLIED)',
    'AGE (FUNDED)',
    'DISABILITY (FUNDED)',
    'SEX (FUNDED)',
    'GENDER REGISTERED AT BIRTH (FUNDED)',
    'ETHNIC ORIGIN (FUNDED)',
    'SEXUAL ORIENTATION (FUNDED)',
    'RELIGIOUS BELIEF (FUNDED)',
    'CARER (FUNDED)'
]

project_files = ['inspire', 'grow_project', 'activate']
revenue_files = ['grow_revenue', 'thrive', 'cultural_anchors']
project_aggregated = pd.DataFrame()
revenue_aggregated = pd.DataFrame()

# Function to fuzzy match and merge dataframes
def fuzzy_merge(df1, df2, key1, key2, threshold=90):
    s = df2[key2].tolist()

    m = df1[key1].apply(lambda x: process.extractOne(x, s, score_cutoff=threshold))
    df1['matches'] = m.apply(lambda x: x[0] if x else None)
    df1['score'] = m.apply(lambda x: x[1] if x else None)

    merged = pd.merge(df1, df2, left_on='matches', right_on=key2, how='left')
    merged.drop(['matches', 'score'], axis=1, inplace=True)
    return merged

def process_wards(ward_data, data, out_path, theme, output_file):
    wards_data = data[data['THEME'] == theme]
    merged_data = (
        fuzzy_merge(ward_data, wards_data, 'WD21NM', 'METRIC')
        .dropna()
        .drop(columns='WD21NM')
        .rename(columns={'WD21CD': 'ward_code', 'THEME': 'metric', 'METRIC': 'ward_name', 'R1 Q1': 'value'})
    )
    merged_data['value'] = merged_data['value'].round(0).astype(int)
    merged_data.to_csv(os.path.join(out_path, output_file), index=False)

def process_diversity_metrics(data, filename_stem):
    applied = data[data['THEME'].str.contains(r'\(APPLIED\)')]
    funded = data[data['THEME'].str.contains(r'\(FUNDED\)')]

    applied.loc[:, 'THEME'] = applied['THEME'].str.replace(r' \(APPLIED\)', '', regex=True)
    funded.loc[:, 'THEME'] = funded['THEME'].str.replace(r' \(FUNDED\)', '', regex=True)

    diversity = pd.merge(
        applied[['THEME', 'METRIC', 'R1 Q1']],
        funded[['THEME', 'METRIC', 'R1 Q1']],
        on=['THEME', 'METRIC'],
        how='outer',
        suffixes=('_APPLIED', '_FUNDED')
    )

    diversity.rename(columns={'THEME': 'METRIC', 'R1 Q1_APPLIED': 'APPLIED', 'R1 Q1_FUNDED': 'FUNDED'}, inplace=True)
    
    return diversity

if __name__ == "__main__":

    ward_data = pd.read_csv(WARD_DATA)

    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".xlsx") or filename.endswith(".xls"):  
            file_path = os.path.join(DATA_DIR, filename)
            filename_stem = Path(filename).stem
            out_path = os.path.join(OUT_DIR, filename_stem)
            try:
                data = pd.read_excel(file_path).drop(columns={'R2 Q2','R3 Q3','R4 Q4'})
                data['THEME'] = data['THEME'].str.rstrip()
                data['METRIC'] = data['METRIC'].str.rstrip()

                # Create datasets per theme
                themes = data['THEME'].unique()
                for theme in themes:
                    theme_df = data[data['THEME'] == theme]
                    theme_df = theme_df.pivot_table(index='THEME', columns='METRIC', values='R1 Q1')
                    theme_df = theme_df.round(0).astype(int)
                    theme_df.columns = theme_df.columns.str.replace(',',' ')
                    theme_filename = theme.replace(" ", "_").replace("/", "_").replace('(', '').replace(')', '').replace('_-_', '_').lower() + '.csv'
                    theme_df.to_csv(os.path.join(out_path, theme_filename), index=True)

                if data['THEME'].isin(diversity_metrics).any():
                    diversity = process_diversity_metrics(data, filename_stem)

                    output_file_name = f"{filename_stem}_diversity.csv"
                    if filename_stem in project_files:
                        output_path = os.path.join(OUT_DIR, 'diversity', 'project', output_file_name)
                    elif filename_stem in revenue_files:
                        output_path = os.path.join(OUT_DIR, 'diversity', 'revenue', output_file_name)

                    if output_path:  
                        diversity.to_csv(output_path, index=False)
                
                process_wards(ward_data, data, out_path, 'WARDS - APPLICANT BASED', 'applications_by_ward.csv')
                process_wards(ward_data, data, out_path, 'WARDS - RECEIVING ACTIVITY', 'received_by_ward.csv')

            except Exception as e:
                print(f"Error reading LCIP data - {filename}: {e}")

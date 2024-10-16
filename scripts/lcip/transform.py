import os 
import pandas as pd
from pathlib import Path

from thefuzz import process

OUT_DIR = os.path.join('src', '_data', 'viz', 'lcip')
DATA_DIR = os.path.join('data', 'lcip')
WARD_DATA = os.path.join('data', 'leeds_wards.csv')

LCIP_DATA = os.path.join('data', 'lcip', 'LCIP GRANT STATS REVISED FINAL Q1 & 2 2024 inc EDI 111024.xlsx')


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
ward_themes = [
    'WARDS - APPLICANT BASED', 
    'WARDS - FUNDED',
    'WARDS - RECEIVING ACTIVITY'
]


def fuzzy_merge(df1, df2, key1, key2, threshold=90):
    s = df2[key2].tolist()

    m = df1[key1].apply(lambda x: process.extractOne(x, s, score_cutoff=threshold))
    df1['matches'] = m.apply(lambda x: x[0] if x else None)
    df1['score'] = m.apply(lambda x: x[1] if x else None)

    merged = pd.merge(df1, df2, left_on='matches', right_on=key2, how='left')
    merged.drop(['matches', 'score'], axis=1, inplace=True)
    return merged

def process_wards(ward_data, data, theme, name, filename):
    wards_data = data[data['THEME'] == theme]
    merged_data = (
        fuzzy_merge(ward_data, wards_data, 'WD21NM', 'METRIC')
        .dropna()
        .drop(columns='WD21NM')
        .rename(columns={'WD21CD': 'ward_code', 'THEME': 'metric', 'METRIC': 'ward_name', 'TOTAL': 'value'})
    )
    merged_data['value'] = merged_data['value'].round(0).astype(int)
    merged_data.to_csv(os.path.join(OUT_DIR, name, filename), index=False)

def process_diversity_metrics(data, out_path, name):
    applied = data[data['THEME'].str.contains(r'- APPLIED')]
    funded = data[data['THEME'].str.contains(r'- FUNDED')]
    applied.loc[:, 'THEME'] = applied['THEME'].str.replace(r'- APPLIED', '', regex=False)
    funded.loc[:, 'THEME'] = funded['THEME'].str.replace(r'- FUNDED', '', regex=False)

    unique_themes = applied['THEME'].unique()

    for theme in unique_themes:
        applied_theme = applied[applied['THEME'] == theme]
        funded_theme = funded[funded['THEME'] == theme]

        diversity_theme = pd.merge(
            applied_theme[['THEME', 'METRIC', 'TOTAL']],
            funded_theme[['THEME', 'METRIC', 'TOTAL']],
            on=['THEME', 'METRIC'],
            how='outer',
            suffixes=('_APPLIED', '_FUNDED')
        )

        diversity_theme = diversity_theme.drop(columns={'THEME'}).dropna()

        diversity_theme['TOTAL_APPLIED'] = diversity_theme['TOTAL_APPLIED'].round(0).astype(int)
        diversity_theme['TOTAL_FUNDED'] = diversity_theme['TOTAL_FUNDED'].round(0).astype(int)

        diversity_theme = diversity_theme.rename(columns={
            'TOTAL_APPLIED': 'APPLIED', 
            'TOTAL_FUNDED': 'FUNDED'
        })

        theme_filename = theme.replace(" ", "_").replace("/", "_").replace('(', '').replace(')', '').replace('_-_', '_').lower().rstrip('_') + '.csv'
        theme_out_path = os.path.join(out_path, 'diversity', name, theme_filename)

        if not diversity_theme.empty:
            os.makedirs(os.path.dirname(theme_out_path), exist_ok=True)
            diversity_theme.to_csv(theme_out_path, index=False)

def clean_name(name):
    name_clean = name.replace(' 2024', '')
    name_clean = (name_clean.upper().rstrip().replace(' ', '_'))
    return name_clean

def clean_sheet(sheet):
    sheet = sheet.dropna(axis='columns', how='all').copy()

    sheet['THEME'] = sheet['THEME'].str.replace(r'\(APPLIED\)', '- APPLIED', regex=True)
    sheet['THEME'] = sheet['THEME'].str.replace(r'\(FUNDED\)', '- FUNDED', regex=True)
    
    period_cols = [col for col in sheet.columns if col.startswith('PERIOD')]
    sheet[period_cols] = sheet[period_cols].apply(pd.to_numeric, errors='coerce')
    
    sheet['TOTAL'] = sheet[period_cols].sum(axis=1)
    sheet = sheet.drop(columns=period_cols)

    sheet.loc[:, 'THEME'] = sheet['THEME'].str.rstrip()
    sheet.loc[:, 'METRIC'] = sheet['METRIC'].str.rstrip()

    return sheet

def clean_theme(theme):
    theme = (theme.replace(" ", "_")
             .replace("/", "_")
             .replace('(', '')
             .replace(')', '')
             .replace('_-_', '_')
             .rstrip()
             .lower() + '.csv')
    return theme

if __name__ == "__main__":

    lcip_data = pd.read_excel(LCIP_DATA, sheet_name=['Inspire 2024', 'Grow Project 2024', 'Activate 2024', 'Grow Revenue 2024', 'Thrive 2024', 'Cultural Anchors 2024'])
    ward_data = pd.read_csv(WARD_DATA)

    project_df = lcip_data['Inspire 2024'][['THEME', 'METRIC']]
    revenue_df = lcip_data['Inspire 2024'][['THEME', 'METRIC']]

    for name, sheet in lcip_data.items():

        project_files = ['INSPIRE', 'GROW_PROJECT', 'ACTIVATE']
        revenue_files = ['GROW_REVENUE', 'THRIVE', 'CULTURAL_ANCHORS']

        name = clean_name(name)

        theme_path = os.path.join(OUT_DIR, name)
        os.makedirs(theme_path, exist_ok=True)

        sheet = clean_sheet(sheet)

        if name in project_files:
            sheet['TOTAL'] = pd.to_numeric(sheet['TOTAL'], errors='coerce')
            project_df = project_df.merge(sheet[['METRIC', 'TOTAL']], on='METRIC', how='left', suffixes=('', f'_{name}'))
            project_df = project_df.rename(columns={'TOTAL': f'TOTAL_{name}'})
        else:
            sheet['TOTAL'] = pd.to_numeric(sheet['TOTAL'], errors='coerce')
            revenue_df = revenue_df.merge(sheet[['METRIC', 'TOTAL']], on='METRIC', how='left', suffixes=('', f'_{name}'))
            revenue_df = revenue_df.rename(columns={'TOTAL': f'TOTAL_{name}'})

        process_diversity_metrics(sheet, OUT_DIR, name)

        themes = sheet['THEME'].unique()
        for theme in themes:
            if theme in ward_themes:
                process_wards(ward_data, sheet, theme, name, f'{clean_theme(theme)}')
            elif theme in diversity_metrics: 
                process_diversity_metrics(sheet, OUT_DIR, name)
            elif not theme in diversity_metrics:
                theme_df = sheet[sheet['THEME'] == theme]
                # theme_df = theme_df.fillna(0)
                theme_df = theme_df.pivot_table(index='THEME', columns='METRIC', values='TOTAL')
                theme_df = theme_df.round(0).astype(int)
                theme_df.columns = theme_df.columns.str.replace(',',' ')
                theme_filename = clean_theme(theme)
                theme_df = theme_df.fillna(0)
                # theme_df = theme_df.loc[~(theme_df == 0).all(axis=1)]
                if not theme_df.empty:
                    theme_df.to_csv(os.path.join(theme_path, theme_filename), index=True)




    project_df = project_df.set_index(['THEME', 'METRIC']).fillna(0)
    revenue_df = revenue_df.set_index(['THEME', 'METRIC']).fillna(0)


    project_df['TOTAL_PROJECT'] = (
        project_df['TOTAL_INSPIRE'].fillna(0) + 
        project_df['TOTAL_GROW_PROJECT'].fillna(0) + 
        project_df['TOTAL_ACTIVATE'].fillna(0)
    )

    project_df.reset_index().to_csv(os.path.join(OUT_DIR, 'project_summary.csv'), index=False)

    revenue_df['TOTAL_REVENUE'] = (
        revenue_df['TOTAL_GROW_REVENUE'].fillna(0) + 
        revenue_df['TOTAL_THRIVE'].fillna(0) + 
        revenue_df['TOTAL_CULTURAL_ANCHORS'].fillna(0)
    )

    revenue_df.reset_index().to_csv(os.path.join(OUT_DIR, 'revenue_summary.csv'), index=False)

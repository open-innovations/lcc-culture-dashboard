import os 
import pandas as pd
from pathlib import Path

from thefuzz import process

OUT_DIR = os.path.join('src', '_data', 'viz', 'lcip')
DATA_DIR = os.path.join('data', 'lcip')
WARD_DATA = os.path.join('data', 'leeds_wards.csv')

LCIP_DATA = os.path.join('data', 'lcip', 'LCIP GRANT STATS REVISED FINAL Q1 & 2 2024 inc EDI 111024.xlsx')


diversity_metrics = [
    'AGE - APPLIED',
    'DISABILITY - APPLIED',
    'SEX - APPLIED',
    'GENDER REGISTERED AT BIRTH - APPLIED',
    'ETHNIC ORIGIN - APPLIED',
    'SEXUAL ORIENTATION - APPLIED',
    'RELIGIOUS BELIEF - APPLIED',
    'CARER - APPLIED',
    'AGE - FUNDED',
    'DISABILITY - FUNDED',
    'SEX - FUNDED',
    'GENDER REGISTERED AT BIRTH - FUNDED',
    'ETHNIC ORIGIN - FUNDED',
    'SEXUAL ORIENTATION - FUNDED',
    'RELIGIOUS BELIEF - FUNDED',
    'CARER - FUNDED'
]

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

        # print(diversity_theme)

        if not diversity_theme.empty:
            os.makedirs(os.path.dirname(theme_out_path), exist_ok=True)
            diversity_theme.to_csv(theme_out_path, index=False)

    
def clean_name(name):
    name_clean = name.replace(' 2024', '')
    name_clean = (name_clean.lower().rstrip().replace(' ', '_'))
    return name_clean

def clean_sheet(sheet):
    sheet = sheet.dropna(axis='columns', how='all').copy()
    sheet = sheet.dropna(axis='rows', how='all').copy()

    sheet['THEME'] = sheet['THEME'].str.replace(r'\(APPLIED\)', '- APPLIED', regex=True)
    sheet['THEME'] = sheet['THEME'].str.replace(r'\(FUNDED\)', '- FUNDED', regex=True)
    
    period_cols = [col for col in sheet.columns if col.startswith('PERIOD')]
    sheet[period_cols] = sheet[period_cols].apply(pd.to_numeric, errors='coerce')
    
    sheet['TOTAL'] = sheet[period_cols].sum(axis=1)
    sheet = sheet.drop(columns=period_cols)

    return sheet

def merge_totals(sheet, name, df):
    sheet['TOTAL'] = pd.to_numeric(sheet['TOTAL'], errors='coerce')
    merged = df.merge(
        sheet[['THEME', 'METRIC', 'TOTAL']], 
        on=['THEME', 'METRIC'], 
        how='left', 
        suffixes=('', f'_{name}')
    )
    merged = merged.rename(columns={'TOTAL': f'total_{name}'})
    return merged

def filter_diversity_metrics(df):
    return df.loc[df['THEME'].isin(diversity_metrics)]

def sum_total_columns(df, columns):
    df['total'] = df[list(columns)].sum(axis=1)
    df = df.drop(columns=list(columns))
    df['total'] = df['total'].round(0).astype(int)
    return df

def applied_funded_merge(applied_df, funded_df):
    merged = pd.merge(
        applied_df[['THEME', 'METRIC', 'total']], 
        funded_df[['THEME', 'METRIC', 'total']],  
        on=['THEME', 'METRIC'],
        how='outer', 
        suffixes=('_APPLIED', '_FUNDED')
    )
    
    merged = merged.rename(columns={
        'total_APPLIED': 'APPLIED',
        'total_FUNDED': 'FUNDED'
    })

    merged['APPLIED'] = merged['APPLIED'].fillna(0).astype(int)
    merged['FUNDED'] = merged['FUNDED'].fillna(0).astype(int)

    return merged

def clean_theme_filename(theme):
    return theme.replace(" ", "_").replace("/", "_").replace('(', '').replace(')', '').replace('_-_', '_').lower().rstrip('_') + '.csv'


if __name__ == "__main__":

    lcip_data = pd.read_excel(LCIP_DATA, sheet_name=['Inspire 2024', 'Grow Project 2024', 'Activate 2024', 'Grow Revenue 2024', 'Thrive 2024', 'Cultural Anchors 2024'])
    ward_data = pd.read_csv(WARD_DATA)

    project_files = ['inspire', 'grow_project', 'activate']
    revenue_files = ['grow_revenue', 'thrive', 'cultural_anchors']

    project_df = lcip_data['Inspire 2024'][['THEME', 'METRIC']]
    revenue_df = lcip_data['Inspire 2024'][['THEME', 'METRIC']]

    for name, sheet in lcip_data.items(): 

        # Clean up the sheet name and data sheets
        name = clean_name(name)
        sheet = clean_sheet(sheet)

        # Summarise and merge totals into project and revenue strands
        if name in project_files:
            project_df = merge_totals(sheet, name, project_df)
        else:
            revenue_df = merge_totals(sheet, name, revenue_df)

    # Create a single total column
    project_df['total'] = project_df[['total_inspire', 'total_grow_project', 'total_activate']].sum(axis=1)
    revenue_df['total'] = revenue_df[['total_grow_revenue', 'total_thrive', 'total_cultural_anchors']].sum(axis=1)

    # Filter only the diversity metrics
    project_df = filter_diversity_metrics(project_df).drop(columns={
        'total_inspire', 'total_grow_project', 'total_activate'
    })
    revenue_df = filter_diversity_metrics(revenue_df).drop(columns={
        'total_grow_revenue', 'total_thrive', 'total_cultural_anchors'
    })

    # Separate the 'applied' and 'funded' data
    applied_project = project_df[project_df['THEME'].str.contains(r'- APPLIED')]
    funded_project = project_df[project_df['THEME'].str.contains(r'- FUNDED')]

    applied_revenue = revenue_df[revenue_df['THEME'].str.contains(r'- APPLIED')]
    funded_revenue = revenue_df[revenue_df['THEME'].str.contains(r'- FUNDED')]

    applied_project.loc[:, 'THEME'] = applied_project['THEME'].str.replace(r'- APPLIED', '', regex=False).str.rstrip()
    funded_project.loc[:, 'THEME'] = funded_project['THEME'].str.replace(r'- FUNDED', '', regex=False).str.rstrip()

    applied_revenue.loc[:, 'THEME'] = applied_revenue['THEME'].str.replace(r'- APPLIED', '', regex=False).str.rstrip()
    funded_revenue.loc[:, 'THEME'] = funded_revenue['THEME'].str.replace(r'- FUNDED', '', regex=False).str.rstrip()

    unique_themes = project_df['THEME'].unique()

    project_diversity = applied_funded_merge(applied_project, funded_project)
    revenue_diversity = applied_funded_merge(applied_revenue, funded_revenue)

    project_diversity = project_diversity.loc[(project_diversity['APPLIED']!=0) & (project_diversity['FUNDED']!=0)]
    revenue_diversity = revenue_diversity.loc[(revenue_diversity['APPLIED']!=0) & (revenue_diversity['FUNDED']!=0)]

    project_diversity['METRIC'] = project_diversity['METRIC'].str.rstrip()
    revenue_diversity['METRIC'] = revenue_diversity['METRIC'].str.rstrip()

    unique_themes = project_df['THEME'].unique()

    unique_themes_project = project_diversity['THEME'].unique()
    unique_themes_revenue = revenue_diversity['THEME'].unique()

    for theme in unique_themes_project:
        project_theme = project_diversity[project_diversity['THEME'] == theme]

        if not project_theme.empty:
            project_theme_filename = clean_theme_filename(theme)
            project_theme.to_csv(os.path.join(OUT_DIR, 'diversity', 'project', f'{theme}.csv'), index=False)

    for theme in unique_themes_revenue:
        revenue_theme = revenue_diversity[revenue_diversity['THEME'] == theme]

        if not revenue_theme.empty:
            revenue_theme_filename = clean_theme_filename(theme)
            revenue_theme.to_csv(os.path.join(OUT_DIR, 'diversity', 'revenue', f'{theme}.csv'), index=False)

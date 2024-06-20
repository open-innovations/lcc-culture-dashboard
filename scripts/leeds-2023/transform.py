
import os
import pandas as pd
import ast

from thefuzz import process

# Load reference data 

SCHOOLS_REF_DATA = os.path.join('data', 'schools.csv')
WARD_REFERENCE = os.path.join('data', 'leeds_wards.csv')
DATA_DIR = os.path.join('src', '_data', 'viz', 'leeds_2023')

# Manual data overrides

UNIQUE_SCHOOLS_OVERRIDE = 228
TOTAL_SCHOOL_ENGAGEMENTS_OVERRIDE=501
TOTAL_EVENTS = 1069
TOTAL_CONFIRMED_VOLUNTEERS = 1008


# Load LEEDS 2023 data

SCHOOLS_DATA = os.path.join('working', 'upstream', 'leeds-2023', 'schools', 'schools_events.csv')
EVENTS_BY_DATE = os.path.join('working', 'upstream', 'leeds-2023', 'events', 'events_by_date.csv')
EVENTS_BY_WARD = os.path.join('working', 'upstream', 'leeds-2023', 'events', 'events_by_ward.csv')
TICKETS_BY_WARD = os.path.join('working', 'upstream', 'leeds-2023','events',  'tickets_by_ward.csv')
TICKETS_BY_DATE = os.path.join('working', 'upstream', 'leeds-2023','events',  'tickets_by_event_date.csv')
VOLUNTEERS_BY_WARD = os.path.join('working', 'upstream', 'leeds-2023', 'volunteers', 'by_ward.csv')
VOLUNTEER_SHIFTS = os.path.join('working', 'upstream', 'leeds-2023', 'volunteers', 'shifts_by_week.csv')
COMBINED_CISION = os.path.join('working', 'upstream', 'leeds-2023', 'media_coverage', 'combined_cision.csv')
COMBINED_HISTORIC = os.path.join('working', 'upstream', 'leeds-2023', 'media_coverage', 'combined_historic.csv')
FACEBOOK_WEEKLY = os.path.join('working', 'upstream', 'leeds-2023', 'social_media', 'facebook_weekly.csv')
INSTAGRAM_WEEKLY = os.path.join('working', 'upstream', 'leeds-2023', 'social_media', 'instagram_weekly.csv')
LINKEDIN_WEEKLY = os.path.join('working', 'upstream', 'leeds-2023', 'social_media', 'linkedin_weekly.csv')
TWITTER_WEEKLY = os.path.join('working', 'upstream', 'leeds-2023', 'social_media', 'twitter_weekly.csv')

def load_schools_data():
    return pd.read_csv(SCHOOLS_DATA, parse_dates=['date']).apply(literal_converter)

def literal_converter(series):
    def convert(value):
        try:
            return ast.literal_eval(value)
        except (SyntaxError, ValueError):
            return value
    return series.apply(convert)

def fuzzy_match_leeds_wards(data, ward_name_col="ward", ward_code_col="ward_code"):
    wards = pd.read_csv(WARD_REFERENCE)
    valid_wards = data[ward_name_col].notna()
    data.loc[valid_wards, 'WD21NM'] = data.loc[valid_wards, ward_name_col].apply(
        lambda x: process.extractOne(x, wards.WD21NM)[0])
    data = pd.merge(left=data, right=wards, how='left', on='WD21NM')
    data = data.drop(columns=[ward_name_col]).rename(columns={'WD21CD': ward_code_col, 'WD21NM': ward_name_col})
    return data

if __name__ == "__main__":

    # PROCESS EVENTS AND TICKETING DATA 

    events_by_date = pd.read_csv(EVENTS_BY_DATE)
    events_by_ward = pd.read_csv(EVENTS_BY_WARD)
    tickets_by_date = pd.read_csv(TICKETS_BY_DATE)
    tickets_by_ward = pd.read_csv(TICKETS_BY_WARD)

    headlines = pd.DataFrame({
        'Total events': TOTAL_EVENTS,
        'Total in person attendances': events_by_ward['in_person'].sum().astype(int),
        'Total online attendances': events_by_ward['online'].sum().astype(int),
        'Total ticket orders': tickets_by_date['tickets'].count(),
        'Total tickets sold': tickets_by_date['tickets'].sum()
    }, index=[0])

    headlines = headlines.melt(var_name='title', value_name='value')

    headlines.to_csv(os.path.join(DATA_DIR, 'events_ticketing_headlines.csv'), index=False)


    # PROCESS CHILDREN AND YOUNG PEOPLE

    # Load data
    data = load_schools_data()
    all_schools = pd.read_csv(SCHOOLS_REF_DATA, usecols=['school_name', 'ward_name', 'ward_code']).set_index('school_name')
    leeds_wards = pd.read_csv(WARD_REFERENCE)
    
    # Count summary statistics
    summary = {}
    summary['Schools in Leeds'] = len(all_schools)
    summary['Schools not assigned to ward'] = len(all_schools[all_schools.ward_name.isna()])
    summary['Total pupil engagements'] = data.pupil_count.sum().astype(int)
    summary['Total school engagements'] = TOTAL_SCHOOL_ENGAGEMENTS_OVERRIDE
    summary['Unique schools'] = UNIQUE_SCHOOLS_OVERRIDE
    summary['Percentage of Leeds schools engaged'] = str(round((summary['Unique schools'] / summary['Schools in Leeds'] * 100),2)) + '%'
    summary['Date build'] = pd.Timestamp.today().floor('D').strftime('%Y-%m-%d')
    summary['Earliest date'] = data.date.min().strftime('%Y-%m-%d')

    # Write engagements by week
    pupil_engagements = data.groupby('date').pupil_count.sum().resample('W-FRI').sum().astype(int)
    school_engagements = data.groupby('date').school_count.sum().resample('W-FRI').sum()
    cumulative_pupil_engagements = pupil_engagements.cumsum()
    cumulative_school_engagements = school_engagements.cumsum()
    engagements_by_week = pd.DataFrame({
        'pupil_engagements': pupil_engagements,
        'cumulative_pupil_engagements': cumulative_pupil_engagements,
        'school_engagements': school_engagements,
        'cumulative_school_engagements': cumulative_school_engagements,
    })
    engagements_by_week.to_csv(os.path.join(DATA_DIR, 'engagements_by_week.csv'))

    # Write school engagement counts
    schools_counts = data.schools.explode().value_counts().to_frame().reset_index()
    schools_counts.columns = ['school_name', 'count_of_engagements']
    schools_counts = schools_counts.merge(
        right=all_schools,
        left_on='school_name', 
        right_on='school_name',
        how='left' 
    )
    schools_counts.to_csv(os.path.join(DATA_DIR, 'school_engagement_counts.csv'), index=False)

    # Write engagements by ward
    ward_stats = leeds_wards.merge(
        schools_counts.reset_index(),
        how='left',
        left_on='WD21CD',
        right_on='ward_code',
    )

    pupils_per_ward = data[['pupil_count', 'wards']].explode('wards').rename(columns={
            'wards': 'ward_name',
        })
    pupils_per_ward = fuzzy_match_leeds_wards(pupils_per_ward, ward_name_col='ward_name')

    ward_group = ward_stats.groupby(['WD21CD', 'WD21NM'])
    engagements_by_ward = pd.DataFrame({
        'schools_engaged': ward_group.count_of_engagements.count(),
        'total_engagements': ward_group.count_of_engagements.sum(),
        'count_of_schools': all_schools.reset_index().groupby(['ward_code', 'ward_name']).school_name.count(),
        'pupil_engagements': pupils_per_ward.groupby(['ward_code', 'ward_name']).pupil_count.sum(),
    }).fillna(0).astype(int)

    summary['Engagements with schools not assigned to ward'] = schools_counts[schools_counts.ward_code.isna()].count_of_engagements.sum().astype(int)
    summary['Engagements with pupils not assigned to ward'] = (data.pupil_count.sum() - engagements_by_ward.pupil_engagements.sum()).astype(int)

    engagements_by_ward.index.names = ['ward_code', 'ward']
    engagements_by_ward['percent_of_schools_in_ward_engaged'] = (engagements_by_ward.schools_engaged / engagements_by_ward.count_of_schools * 100).astype(int)

    engagements_by_ward.to_csv(os.path.join(DATA_DIR, 'engagements_by_ward.csv'))

    # Write summary CSV
    summary = pd.DataFrame.from_dict(summary, orient="index", columns=['value']).sort_index()
    summary = summary.reset_index().rename(columns={'index': 'title'})
    summary.to_csv(os.path.join(DATA_DIR, 'schools_headlines.csv'), index=False)


    # PROCESS VOLUNTEER DATA

    volunteers_by_ward = pd.read_csv(VOLUNTEERS_BY_WARD)
    volunteer_shifts_by_week = pd.read_csv(VOLUNTEER_SHIFTS)

    volunteers_by_ward.to_csv(os.path.join(DATA_DIR, 'volunteers_by_ward.csv'), index=False)
    

    volunteer_headlines = pd.DataFrame({
        'Total confirmed volunteers': TOTAL_CONFIRMED_VOLUNTEERS,
        'Total volunteer shifts completed': volunteer_shifts_by_week.volunteer_shifts.sum(),
        'Total volunteer hours completed': volunteer_shifts_by_week.volunteer_hours.sum(),
    }, index=[0])

    volunteer_headlines = volunteer_headlines.melt(var_name='title', value_name='value')
    volunteer_headlines.to_csv(os.path.join(DATA_DIR, 'volunteer_headlines.csv'), index=False)

    # PROCESS MEDIA COVERAGE

    MEDIA_START_DATE = '2021-01-01'
    MEDIA_END_DATE = '2024-01-31'

    cision_data = pd.read_csv(os.path.join(
        COMBINED_CISION), parse_dates=['news_date'])
    historic_data = pd.read_csv(os.path.join(
        COMBINED_HISTORIC), parse_dates=['news_date'])

    data = pd.concat([cision_data, historic_data]).sort_values('news_date')
    data = data[data['news_date'].between(MEDIA_START_DATE, MEDIA_END_DATE)]

    data['medium'] = data['medium'].replace(
        {'Newspaper': 'Print', 'Magazine': 'Print', 'Broadcat': 'Broadcast', 'Pdf': 'Online', 'Online ': 'Online', 'Onine': 'Online', 'Newletter': 'Newsletter'})
    medium_count = pd.DataFrame({'count': data.groupby(
        ['medium'])['news_headline'].count()}).sort_values('count', ascending=False)
    medium_count.to_csv(os.path.join(DATA_DIR, 'medium_count.csv'))

    REGION_TAGS = ['International', 'National', 'Regional', 'Local', 'Unknown']
    by_region = data.filter(['news_date', 'custom_tags', 'news_headline'])
    by_region.news_date = by_region.news_date.dt.to_period('M')
    by_region = by_region.set_index('news_date')
    by_region = by_region.custom_tags \
        .str.split(";").explode() \
        .str.strip() \
        .fillna('Unknown') \
        .to_frame('region')
    by_region = by_region[by_region.region.isin(REGION_TAGS)]
    pre_check = by_region.value_counts().sum()
    by_region['count'] = 1
    by_region = by_region.groupby(['news_date', 'region']) \
        .count().reset_index() \
        .pivot(index="news_date", columns="region", values="count") \
        .fillna(0) \
        .astype(int)
    by_region['Total'] = by_region.sum(axis=1)
    by_region.index.names = ['month']

    assert (by_region.Total.sum() == pre_check)
    by_region.to_csv(os.path.join(DATA_DIR, 'monthly_count.csv'))

    # Summary Stats
    uv_max = int(data['uv'].max())
    reach_max = int(data['audience_reach'].max())
    total_audience_reach = int(data.audience_reach.sum())
    total_unique_views = int(data.uv.sum())

    # Create a DataFrame
    stats = pd.DataFrame({
        'title': [
            'Total media', 
            'UV Max', 
            'Reach', 
            'Total media - Local',
            'Total media - Regional',
            'Total media - National',
            'Total media - International',
            'Total media - Unknown',
            'Total audience reach',
            'Total unique views',
            'Total estimated circulation',
            'Total editorial articles'
        ],
        'value': [
            int(data['news_headline'].count()),
            uv_max,
            reach_max,
            int(by_region.Local.sum()),
            int(by_region.Regional.sum()),
            int(by_region.National.sum()),
            int(by_region.International.sum()),
            int(by_region.Unknown.sum()),
            total_audience_reach,
            total_unique_views,
            total_audience_reach + total_unique_views,
            2172
        ]
    })

    stats.to_csv(os.path.join(DATA_DIR, 'media_headlines.csv'), index=False)

    # PROCESS SOCIAL ANALYTICS

    twitter = pd.read_csv(TWITTER_WEEKLY)
    instagram = pd.read_csv(INSTAGRAM_WEEKLY)
    facebook = pd.read_csv(FACEBOOK_WEEKLY)
    linkedin = pd.read_csv(LINKEDIN_WEEKLY)

    twitter_data = {
        'Audience last': twitter['audience_last'].sum(),
        'Total engagements': twitter['engagements_total'].sum(),
        'Total audience gained': twitter['audience_gained_total'].sum(),
        'Total impressions': twitter['impressions_total'].sum()
    }

    instagram_data = {
        'Audience last': instagram['audience_last'].sum(),
        'Total engagements': instagram['engagements_total'].sum(),
        'Total audience gained': instagram['audience_gained_total'].sum(),
        'Total impressions': instagram['impressions_total'].sum()
    }

    facebook_data = {
        'Audience last': facebook['audience_last'].sum(),
        'Total engagements': facebook['engagements_total'].sum(),
        'Total audience gained': facebook['audience_gained_total'].sum(),
        'Total impressions': facebook['impressions_total'].sum()
    }

    linkedin_data = {
        'Audience last': linkedin['audience_last'].sum(),
        'Total engagements': linkedin['engagements_total'].sum(),
        'Total audience gained': linkedin['audience_gained_total'].sum(),
        'Total impressions': linkedin['impressions_total'].sum()
    }

    # Create a summary DataFrame
    summary_data = {
        'title': ['Audience last', 'Total engagements', 'Total audience gained', 'Total impressions'],
        'twitter': [twitter_data['Audience last'], twitter_data['Total engagements'], twitter_data['Total audience gained'], twitter_data['Total impressions']],
        'instagram': [instagram_data['Audience last'], instagram_data['Total engagements'], instagram_data['Total audience gained'], instagram_data['Total impressions']],
        'facebook': [facebook_data['Audience last'], facebook_data['Total engagements'], facebook_data['Total audience gained'], facebook_data['Total impressions']],
        'linkedin': [linkedin_data['Audience last'], linkedin_data['Total engagements'], linkedin_data['Total audience gained'], linkedin_data['Total impressions']]
    }

    summary_df = pd.DataFrame(summary_data)
    summary_df['total'] = summary_df[['twitter', 'instagram', 'facebook', 'linkedin']].sum(axis=1)

    # Save the DataFrame to a CSV file
    summary_csv_path = os.path.join(DATA_DIR, 'social_media_headlines.csv')
    summary_df.to_csv(summary_csv_path, index=False)
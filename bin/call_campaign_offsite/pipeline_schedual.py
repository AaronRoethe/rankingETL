# from FileLoad import Final_Load
import pandas as pd
import numpy as np
from datetime import date, timedelta, datetime
from pipeline_check_missing import pull_list
from etc_function import next_business_day, Next_N_BD, date_list_split, daily_piv
from data_config import table_drops, assignment_map

today = date.today()
tomorrow = next_business_day(today)
D2 = next_business_day(tomorrow)
B10 = Next_N_BD(today, 10)

FivDay = today + timedelta(days=7)
test = next_business_day(FivDay)
# df, test = Final_Load()


### Create static two week sprint ###
def static_schedual():
    dt = pd.DataFrame(
            {'startdate'    :B10,
                'Number'    :range(10)} )
    dt['startdate'] = pd.to_datetime(dt['startdate']) 
    return dt

def Load_Assignment():
    Cluster = table_drops('pull', 'NA','Assignment_Map.csv' )
    ### at the begining of new cylce remove cut this section
    Cluster['Daily_Groups'] = pd.to_datetime(Cluster['Daily_Groups'], format='%m/%d/%Y')
    start = Cluster[Cluster['Daily_Groups'] >= tomorrow.strftime('%m/%d/%Y')]
    end =  Cluster[Cluster['Daily_Groups'] < tomorrow.strftime('%m/%d/%Y')]
    Cluster = start.append(end).reset_index(drop=True).drop_duplicates(subset='PhoneNumber').sort_values('Daily_Groups').reset_index(drop=True)
    Cluster['Daily_Groups'] = pd.to_datetime(Cluster['Daily_Groups'], format='%m/%d/%Y').dt.date
    ### end
    Cluster = Cluster.join(pd.get_dummies(Cluster['Daily_Groups']))
    return Cluster

def sort(i):
    df = Load_Assignment()
    df0 = df[df[i] == 1]['PhoneNumber']
    return df0

def Cluster(df, Add_Cluster):
    df_local = df
    filter0 = df_local['PhoneNumber'].isin(sort(Add_Cluster).squeeze())
    df_local['Daily_Groups'] = np.where(filter0, Add_Cluster, df_local['Daily_Groups'])
    return df_local

def Daily_Maping(df):
    f = df
    load = Load_Assignment()
    names = list(load['Daily_Groups'].unique())
    for i in names:
        f = Cluster(f,i)
    return f, names

### Create file with assigned categories to ORG
def Assign_Map(df):
    skills = df['Skill'].unique()
    df_clean = df.drop_duplicates('PhoneNumber')
    df_key = pd.DataFrame()
    B10 = Next_N_BD(today, 10)
    num1 , num2 = date_list_split(B10, 2)
    def assign_skill(sk, j, BusDay):
        df_skill = df_clean[df_clean['Skill'] == sk].reset_index(drop = True)
        if j == 5:
            df_skill = df_skill[df_skill['audit_sort'] <= 2].reset_index(drop = True)
        elif j == 10:
            df_skill = df_skill[df_skill['audit_sort'] > 2].reset_index(drop = True)
        else:
            print('error')
        #### INPUT BY DAY ####
        Sprint = j
        ######################
        df_len = len(df_skill.index)
        group_size = df_len // Sprint 
        ## What day for what number ##
        listDay = BusDay * group_size
        listDay.sort()
        ## Create Same len list of letters as len of df
        Daily_Priority = pd.DataFrame(listDay, columns=['Daily_Groups'])
        add_back = df_len - len(Daily_Priority)
        Daily_Priority = Daily_Priority.append(Daily_Priority.iloc[[-1]*add_back]).reset_index(drop=True)
        df_skill['Daily_Groups'] = Daily_Priority['Daily_Groups']
        return df_skill[['PhoneNumber', 'Skill','Daily_Groups']]
    def assign_audit(sk):
        D5_1 = assign_skill(sk, 5, list(num1))
        D5_2 = assign_skill(sk, 5, list(num2))
        D10  = assign_skill(sk, 10, B10)
        final = D5_1.append(D5_2).append(D10)
        return final
    ## Add together all skills with uniquely broken out sprints
    for i in skills:
            df_key = df_key.append(assign_audit(i))
    df_key['NewID'] = 0
    assignment_map('push', df_key, str(tomorrow + '.csv'))
    table_drops('push', df_key, 'Assignment_Map.csv')
    return daily_piv(df_key)

    ## Sprint Schedulual Day
def Map_categories(df, Day, test):
    if test == 1:
        df['Daily_Priority'] = 0
        df['Daily_Groups'] = 0
        df['NewID'] = 0
        return df
    else:
        df, names = Daily_Maping(df)
        df['NewID'] = 0
        filter1 = df['Daily_Groups'] == 0
        df['NewID'] = np.where(filter1, 1, df['NewID'])
        df['Daily_Groups'] = df['Daily_Groups'].replace(0, D2)
        df['OutreachID'] = df['OutreachID'].astype(int)
        filter0 = df['OutreachID'].isin(pull_list().squeeze())
        df['Daily_Groups'] = np.where(filter0, tomorrow, df['Daily_Groups'])
        ####################################
        Sprint = len(names)
        ### Map and Sort
        Sprint_schedual = list(range(0,Sprint))
        Category = names
        Sprint_schedual = Sprint_schedual[-Day:] + Sprint_schedual
        Daily_sort = dict(zip(Category,Sprint_schedual))
        df['Daily_Priority'] = df['Daily_Groups'].map(Daily_sort)
        return df

if __name__ == "__main__":
    print("Clusters")
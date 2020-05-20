
#missing features: fix levels of breathing

import datetime
from typing import Dict, Any, List, Iterable
from weasyprint import HTML
import time
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from google.cloud import storage
import numpy as np 

from helpers.filemanager import getJsonData, MailgunClient, blobDownloader


def daily_overview ():
    '''add descr'''
    print('Starting to download data')

    data = getJsonData(days_ago=7, env='PROD') #all patients

    print("Success in retrieving from API")

    path = "/tmp/"
    bucket = 'syncvr-dlc'
    print("bucket is {}".format(bucket))

    blobDownloader(bucket, 'branding/FitterVandaag.png', '/tmp/FitterVandaagLogo.png')
    blobDownloader(bucket, 'branding/style.css', '/tmp/style.css')

    for patient in data['data']:
        html_out, outfile = __corona_report__(data=patient, keys=coronaDict, html_email_template = html_email_template)
        convert_to_pdf(html_out, path + outfile) #add some return bool if success

        if MailgunClient().send_mail(
            subject="Daily Usage Update", text= "SyncVR update", html="", to_addresses = patient.get('contactEmails','freek@syncvr.tech'), attachment = outfile, path=path):
            print("Successfully sent daily report of {}!".format(outfile))
        else:
            print("Sending daily report failed!")



def __corona_report__(data: Dict[str, Any], keys: Dict[Any, Any], html_email_template: str, max_sessions: int = 100, appname: str = 'tech.syncvr.fysio', lang: str = 'dutch') -> str:
    '''add description'''

    patient_html: str = ""
    table_html = ""
    date_html = dateTransformer(time.time(), ms=False)

    #print(data['patientId'])

    #patient_html += __title_row__([keys['appname'][appname][lang]])

    duration_list = []
    date_list = []
    game_list = []
    
    action_list = []
    action_name_list = []
    action_gamename_list = []
    action_date_list = []
    
    table_html += __summary_row__([keys['date'][lang] + ": " + dateTransformer(data['results'][appname]['firstResultStartTime'])," Headset ID: {}".format(data['results'][appname]['data'][len(data['results'][appname]['data']) - 1]['headsetId'])], header='h3')


    print('Begin loop over sessions')

    for num,session in enumerate(data['results'][appname]['data']):
        
        #print(num)
        
        duration_list.extend([session['duration']])
        date_list.extend([dateTransformer(session['start_time'])])
        game_list.extend([keys['exercise_code'][session['exercise_code']]['name'][lang]])

        if num < max_sessions: #report only last max_sessions

            patient_html += __header_row__([dateTransformer(session['start_time']),keys['exercise_code'][session['exercise_code']]['name'][lang]])

            patient_html += __data_row__([keys['difficulty_level']['name'][lang],
                                          keys['difficulty_level']['levels'][lang][session['difficulty_level']]])

            patient_html += __data_row__([keys['duration']['name'][lang], str(datetime.timedelta(seconds=session['duration']))])
                                          #,keys['duration']['unit'][lang]])

            for i, action in enumerate(session['score']):
                #print(action)
                patient_html += __data_row__([keys['exercise_code'][session['exercise_code']]['scores'][lang][action],
                                              str(session['score'][action])])
                                   
                action_name_list.extend([keys['exercise_code'][session['exercise_code']]['scores'][lang][action]])
                action_list.extend([str(session['score'][action])])
                #replace the str(i) with something more reliable. especially for i > 9
                action_gamename_list.extend([keys['exercise_code'][session['exercise_code']]['name'][lang]+str(i)])
                action_date_list.extend([dateTransformer(session['start_time'])+str(i)])
                

    print("Completed first loop")


    table = pd.DataFrame({keys['duration']['name'][lang]:duration_list, 'Date':date_list,'Exercise':game_list})
    table = table.groupby(['Date','Exercise']).sum().reset_index()
        
    action_table = pd.DataFrame({"Action_name":action_name_list,'Action':action_list,'Exercise':action_gamename_list, 'Date':action_date_list})
    
    
    for e in range(len(action_table)):
        #this breaks when days>10
        action_table.Exercise[e] = action_table.Exercise[e][:len(action_table.Exercise[e])-1]
        action_table.Date[e] = action_table.Date[e][:len(action_table.Date[e])-1]
    
    action_table = action_table.groupby(['Date','Exercise','Action_name']).sum().reset_index()
    
    
    exercise_list = table.Exercise.unique().tolist()
    
    for exer in exercise_list:
        

        date_array=np.array(table.T.loc['Date',table.T.iloc[1]==exer]).tolist() 
        dur_array=np.array(table.T.loc[keys['duration']['name'][lang],table.T.iloc[1]==exer]) 
        subheaddata_array = set(np.array(action_table.T.loc['Action_name',action_table.Exercise==exer]))

        subdata_array = action_table.loc[action_table.Exercise==exer,['Date','Action_name','Action']]
        subdata_array = subdata_array.pivot(index='Action_name', columns='Date', values='Action')

        header = [exer]
        data_list = [keys['duration']['name'][lang]]

        data_list.extend([str(datetime.timedelta(seconds=e)) for e in dur_array])
        header.extend(date_array)


        table_html += __header_row__(header)
        table_html += __data_row__(data_list)



        for act in subheaddata_array:

            subdata_list = [act]
            subdata_data = np.array(subdata_array[subdata_array.index==act]).tolist()
            subdata_list.extend([str(e) for sublist in subdata_data for e in sublist])


            table_html += __data_row__(subdata_list)        


    barFigure('Date',keys['duration']['name'][lang],'Exercise',table,'/tmp/fig.png')

    print("Created figure")

    html_out = html_email_template.format(date_html[4:10], "fig.png", table_html, patient_html)

    outfile = data['results'][appname]['data'][len(data['results'][appname]['data'])-1]['headsetId'] + "_" + str(datetime.datetime.now().date()) + '.pdf'
    print("Create HTML report {}".format(outfile))

    return html_out,outfile




def barFigure(x,y,hue,data,filename):

    sns.set_context(rc={"lines.linewidth": 2.5,'lines.markersize': 12, 'font.size': 16 })

    fig, ax = plt.subplots(figsize=(12,8))
    fig=sns.barplot(x = x, y = y, hue=hue,  data = data)
    ax.set_xlabel("", fontsize = 16)
    ax.set_ylabel("Seconds")
    ax.legend(loc='upper left')
    sns.despine()
    plt.savefig(filename)



def dateTransformer(timestamp: int, ms: bool = True) -> str:
    'input is timestamp, ms if milliseconds,  output is date'
    if ms:
        timestamp /= 1000
    else:
        print('{} is not treated as milliseconds'.format(timestamp))

    date = time.ctime(timestamp).split()

    date.pop(3)  # remove time

    date = str(date[0] + " " + date[1] + " " + date[2] + " " + date[3]) #could remove weekday

    return date


def convert_to_pdf(body_html: str, outfile: str):
    #make it return a bool if it went smooth


    return HTML(string=body_html, base_url="/tmp/").write_pdf(outfile, stylesheets=["/tmp/style.css"])


def __title_row__(data: List[str]) -> str:
    html: str = "<tr>"
    for s in data:
        html += "<h1>" + s + " Update </h1>"

    html += "</tr>"
    return html


def __data_row__(data: List[str]) -> str:
    html: str = "<tr>"
    for s in data:
        html += "<td>" + s + "</td>"

    html += "</tr>"
    return html


def __header_row__(data: List[str]) -> str:
    html: str = "<tr>"
    for s in data:
        html += "<th>" + s + "</th>"

    html += "</tr>"
    return html


def __subheader_row__(data: List[str]) -> str:
    html: str = "<tr class='border' >"
    for s in data:
        html += "<th> <em>" + s + "</em></th>"

    html += "</tr>"
    return html

def __summary_row__(data: List[str], header: str) -> str:

    html: str = "<tr class='border' >"

    header_start = "<"+header+">"
    header_end = "</"+header+">"


    for s in data:
        html += header_start + s + header_end

    html += "</tr>"

    return html

coronaDict= {'exercise_code':{'breathing':{'name':{'english':'Breathing','dutch':'Ademhaling'}},
    'sorting':{'name':{'english':'Sorting','dutch':'Sorteren'},'scores':{'dutch':{'sorting_objects_total':'Objecten totaal','sorting_objects_missed':'Objecten gemist',
                                                                        'sorting_objects_wrong':'Objecten verkeerd gesorteerd','sorting_objects_correct':'objecten goed gesorteerd'},
               'english':{'sorting_objects_total':'Objects total','sorting_objects_missed':'Objects missed',
                                                                        'sorting_objects_wrong':'Objects sorted wrongly','sorting_objects_correct':'Object sorted correctly'}}},
  'fireflies':{'name':{'english':'Fireflies','dutch':'Vuurvliegjes'},'scores':{'dutch':{'fireflies_total':'Vuurvliegjes totaal','fireflies_missed':'Vuurvliegjes gemist',
                                                                        'fireflies_wrong':'Vuurvliegjes verkeerde hand','fireflies_correct':'Vuurvliegjes goede hand'},
               'english':{'fireflies_total':'Fireflies total','fireflies_missed':'Fireflies missed',
                                                                        'fireflies_wrong':'Fireflies wrong hand','fireflies_correct':'Fireflies correct hand'}}},
'head-dodging':{'name':{'english':'Beach ball squats', 'dutch':'Strandbal squats'}, 'scores':{'dutch':{'dodge_total_objects':'Objecten totaal',
                                                                                                        'dodge_objects_dodged': 'Objecten ontweken', 'dodge_objects_hit':'Objecten geraakt', 'dodge_objects_total':'Objecten totaal', 'dodge_objects_success':'Objecten gelukt', 'dodge_objects_failed':'Objecten mislukt'},
                                                                                                         'english':{'dodge_total_objects':'Objects total','dodge_objects_dodged':'Objects dodged','dodge_objects_hit':'Objects hit'}}},
    'dodging':{'name':{'english':'Beach ball squats', 'dutch':'Strandbal squats'}, 'scores':{'dutch':{'dodge_total_objects':'Objecten totaal','dodge_objects_dodged': 'Objecten ontweken', 'dodge_objects_hit':'Objecten geraakt', 'dodge_objects_total':'Objecten totaal', 'dodge_objects_success':'Objecten gelukt', 'dodge_objects_failed':'Objecten mislukt'},
                                                                                                         'english':{'dodge_total_objects':'Objects total','dodge_objects_dodged':'Objects dodged','dodge_objects_hit':'Objects hit'}}},
    'goal-keeping':{'name':{'english':'Goalkeeping','dutch':'Keepen'},'scores':{'dutch':{'goalkeeping_balls_total':'Ballen totaal',
'goalkeeping_balls_saved':'Ballen tegengehouden',
    'goalkeeping_balls_missed':'Ballen doorgelaten'},'english':{'goalkeeping_balls_total':'Balls total',
'goalkeeping_balls_saved':'Balls saved',
    'goalkeeping_balls_missed':'Balls missed'}}},
              'fruit-picking':{'name':{'english':'Fruit picking', 'dutch':'Fruit plukken'},'scores':{'dutch':{'apples_collected':'Appels verzameld',
'bananas_collected':'Bananen verzameld',
'strawberries_collected':'Aardbeien verzameld'}, 'english':{'apples_collected':'Apples collected',
'bananas_collected':'Bananas collected',
'strawberries_collected':'Strawberries collected'}}}}, 'difficulty_level':{'name':{'english':'Difficulty level', 'dutch':'Moeilijkheidsgraad'},'levels':{'dutch':{1:'Heel Makkelijk', 2: 'Makkelijk',3: 'Gemiddeld', 4: 'Moeilijk',5:'Heel Moeilijk'},
    'english':{1:'Very easy',2: 'Easy', 3: 'Average',4: 'Difficult', 5:'Very difficult'}}},
            'duration':{'name':{'english':'Duration','dutch':'Duur'},'unit':{'dutch':'uren:minuten:seconden','english':'hours:minutes:seconds'}},'appname':{'tech.syncvr.fysio':{'dutch':'Fitter Vandaag', 'english':'Fitter Today'}},'date':{'english':'First session on','dutch':'Eerste sessie op'}, 'equipment':{'english':'Equipment used: ', 'dutch':'Gebruikt materiaal: '}}





html_email_template: str = """
<html>
	<head>
		<style type="text/css">
		    table {{
		        border-collapse: collapse;
		        width: 100%;
				border-spacing: 0 15px;
    		}}

		    tr.border {{
		        border-top: 1px solid #ccc;
		    }}

		    th {{
		        text-align: left;
		        background-color: #3c6fb7;
		       color: white;
		    }}
		    td {{
		        text-align: left;
		        border: 1px solid black;
		    }}
		    h1 {{
		        color: #3c6fb7;
                font-size:14; 
		    }}
		    h3 {{
		        color: #3c6fb7;
		    }}
		    h2 {{
		        color: #3c6fb7;
		    }}


		</style>
	</head>
	<body>
    <img src="FitterVandaagLogo.png" style="float: right; width: 15%">
    <h1>FitterVandaag update {}</h1> </br>
    </br>
    </br>
    <img src={} style="float: center; width: 66%">

	    <table>
            {}
        </table>
        <table>
            {}
        </table>
	</body>
</html>
"""

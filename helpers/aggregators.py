

#missing features:
# headset id and first session both oin the pdf and as filename
# add chart to show activity over time
# add logo?

import datetime
from typing import Dict, Any, List, Iterable
from weasyprint import HTML
import time
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

from helpers.filemanager import getJsonData, MailgunClient, blobDownloader


def daily_overview ():
    '''add descr'''

    data = getJsonData(days_ago=7, env='PROD') #all patients

    path = "/tmp/"
    
    blobDownloader('test-bucket', 'FitterVandaagLogo.png', '/tmp/FitterVandaagLogo.png')

    for patient in data['data']:
        html_out, outfile = __corona_report__(data=patient, keys=coronaDict, html_email_template = html_email_template)
        convert_to_pdf(html_out, path + outfile) #add some return bool if success

        if MailgunClient().send_mail(
            subject="Daily Usage Update", text= "SyncVR update", html="", to_addresses = patient['contactEmails'], attachment = outfile, path=path):
            print("Successfully sent daily report of {}!".format(outfile))
        else:
            print("Sending daily report failed!")

            
    

def __corona_report__(data: Dict[str, Any], keys: Dict[Any, Any], html_email_template: str, max_sessions: int = 100, appname: str = 'tech.syncvr.fysio', lang: str = 'dutch') -> str:
    '''add description'''

    patient_html: str = ""
    
    headset_html: str = __summary_row__([keys['equipment'][lang]],header='h3')
    
    #print(data['patientId'])

    #patient_html += __title_row__([keys['appname'][appname][lang]])

    patient_html += __summary_row__([keys['date'][lang]+ ": " +dateTransformer(data['results'][appname]['firstResultStartTime'])],header='h2')

    duration_list = []
    date_list = []
    game_list = []
    
    for num,session in enumerate(data['results'][appname]['data']):
        
        duration_list.extend([session['duration']])
        date_list.extend([dateTransformer(session['start_time'])])
        game_list.extend([keys['exercise_code'][session['exercise_code']]['name'][lang]])
        
        if num < max_sessions: #report only last max_sessions
        
            patient_html += __header_row__([dateTransformer(session['start_time']),keys['exercise_code'][session['exercise_code']]['name'][lang]])

            patient_html += __data_row__([keys['difficulty_level']['name'][lang],
                                          keys['difficulty_level']['levels'][lang][session['difficulty_level']]])

            patient_html += __data_row__([keys['duration']['name'][lang], str(datetime.timedelta(seconds=session['duration']))])
                                          #,keys['duration']['unit'][lang]])

            for action in session['score']:
                patient_html += __data_row__([keys['exercise_code'][session['exercise_code']]['scores'][lang][action],
                                              str(session['score'][action])])
                
    for num, session in enumerate(data['results'][appname]['data']):
        if num < max_sessions:
            headset_html += __summary_row__([dateTransformer(session['start_time']) + " Headset: {}".format(session['headsetHumanReadableName']) + " (ID: {})".format(session['headsetId'])], header='p')        
        
        
    table = pd.DataFrame({keys['duration']['name'][lang]:duration_list, 'Date':date_list,'Exercise':game_list})
    table = table.groupby(['Date','Exercise']).sum().reset_index()
    

    barFigure('Date',keys['duration']['name'][lang],'Exercise',table,'/tmp/fig.png')
    
    html_out = html_email_template.format("fig.png",patient_html, headset_html)
    
    
    outfile = data['patientId'][:5] + "_" + str(datetime.datetime.now().date()) + '.pdf' #headset not unique to patient. start time not unique as filename. patient+date unique combination

    return html_out, outfile

def barFigure(x,y,hue,data,filename):
    
    sns.set_context(rc={"lines.linewidth": 2.5,'lines.markersize': 12, 'font.size': 16 })
    
    fig, ax = plt.subplots(figsize=(8,8))
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
    
    
    return HTML(string=body_html, base_url="/tmp/").write_pdf(outfile, stylesheets=["helpers/style.css"])


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
                                                                                                        'dodge_objects_dodged': 'Objecten ontweken', 'dodge_objects_hit':'Objecten geraakt'},
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
    <h1> Fitter Vandaag Update </h1> </br>
    <img src={} style="float: center; width: 66%">

	    <table>
            {}
        </table>
        {}
	</body>
</html>
"""






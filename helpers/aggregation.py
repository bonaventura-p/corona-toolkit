from google.cloud import firestore
import datetime
from typing import Dict, Any, List, Iterable
from weasyprint import HTML
from helpers.mailgun import MailgunClient
import requests
import time



db = firestore.Client()

#import subprovess
#subprocess.call(['/pathto/VR/keys/genv-setup.sh'])

def daily_overview ():

    now: datetime.datetime = datetime.datetime.now()
    yesterday: datetime.datetime = now - datetime.timedelta(days=1)

    headsets: List[Dict[str, Any]] = __get_headset_data__(yesterday, now)
    report: str = __corona_report__(headsets) #make one for each customer/device

    outfile = 'PhysioReport ' + str(now.date()) #name specific

    if MailgunClient().send_mail(
        "Daily Usage Update",
        "",
        convert_to_pdf(report,outfile) #do you need to tmp the location????,
        #to_addresses #specific
    ):
        print("Successfully sent daily report!")
    else:
        print("Sending daily report failed!")




def __get_headset_data__(start_time: datetime.datetime, end_time: datetime.datetime) -> List[Dict[str, Any]]:
    headsets: List[Dict[str, Any]] = []

    # get all headsets
    for headset in db.collection("headsets").stream():
        # obtain headset customer and email?
        headset_customer = __headset_customer__(headset)

        #EXPLAIN IN THE DRAWING
        headset_email = __headset_email__(headset)


        headset_sessions: Dict[str, Any] = {
            "customer": headset_customer,
            "email": headset_email,
            "headset": headset.id,
            "apps": {}
        }


        # ONLY PHYSIO APP?
        for app in db.document("usageSessions", headset.id).collections():
            query: firestore.Query = db.collection("usageSessions", headset.id, app.id)\
                                        .where("sessionStart", ">=", start_time)\
                                        .where("sessionStart", "<", end_time)
            headset_sessions["apps"][app.id]: List[firestore.DocumentSnapshot] = []
            for session in query.stream():
                headset_sessions["apps"][app.id].append(session)

        headsets.append(headset_sessions)

    return headsets #this is all customers device together in one list

def headset_email(headset: firestore.DocumentSnapshot) -> str:
    try:
        return headset.get("customer").get().get("emailAccount")
    except KeyError:
        return ""

def __headset_customer__(headset: firestore.DocumentSnapshot) -> str:
    try:
        return headset.get("customer").get().get("companyName")
    except KeyError:
        return ""


def __corona_report__(data: List[Dict[str, Any]]) -> str:
    # get list of unique customers
    customers: List[str] = list(set([headset["customer"] for headset in data]))

    body_html: str = ""
    for customer in customers:
        # get list of headsets for this customer
        customer_headsets: List[Dict[str, Any]] = [headset for headset in data if headset["customer"] == customer]
        customer_html: str = __header_row__([customer, "num headsets", str(len(customer_headsets)), ""])

        customer_apps: List[str] = []
        for headset in customer_headsets:
            customer_apps.extend(headset["apps"].keys())

        for app in set(customer_apps):
            app_data: List[firestore.DocumentSnapshot] = []
            for headset in customer_headsets:
                app_data.extend(headset["apps"].get(app, []))

            if len(app_data) == 0:
                continue
            customer_html += __data_row__(["", app, "", ""])

            #FIX AGGREGATOR
            aggregated: Dict[str, Any] = __get_aggregator__(app_data, app).aggregate()
            for k2, v2 in aggregated.items():
                customer_html += __data_row__(["", "", k2, str(v2)])

        body_html += customer_html + "<tr><td><br></td></tr>"

        html_out = html_email_template.format(body_html)
        convert_to_pdf(html_out, 'test.pdf')
    return something


body_html = customer_html + "<tr><td><br></td></tr>"
html_out = html_email_template.format(body_html)

outfile = 'Report ' + customer + str(end_time.date()) + '.pdf'
convert_to_pdf(html_out, outfile)


def convert_to_pdf(body_html: str,outfile: str):
    return HTML(string=body_html).write_pdf(outfile, stylesheets=["style.css"])


#FIX AGGREGATOR
def __get_aggregator__ (query_stream: Iterable[firestore.DocumentSnapshot], app_name: str) -> SessionAggregator:
    if app_name == "tech.syncvr.painreduction":
        return SessionAggregatorTechSyncvrPainreduction(query_stream)
    else:
        return SessionAggregator(query_stream)


html_email_template: str = """
<html>
	<head>
		<style type="text/css">
		    table {{
		        border-collapse: collapse;
		        width: 100%;
				border-spacing: 10px 0;
    		}}

		    tr.border {{
		        border-top: 1px solid #ccc;
		    }}

		    th {{
		        text-align: left;    
		    }}
		</style>	
	</head>
	<body>
	    <table>
            {}
        </table>
	</body>
</html>
"""


def __data_row__(data: List[str]) -> str:
    html: str = "<tr>"
    for s in data:
        html += "<td>" + s + "</td>"

    html += "</tr>"
    return html

def __subheader_row__(data: List[str]) -> str:
    html: str = "<tr class='border'>"
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
import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS,cross_origin
import logging
import requests
import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
from sqlite3 import Error
from datetime import datetime
import secrets

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor


#configuration of scheduler
executors = {
    'default': ProcessPoolExecutor(50)
}

job_defaults = {
    'coalesce': False,
    'max_instances': 50,
    'misfire_grace_time': 5*60
}

#scheduler to run the function in asynchronous mode in background
sched = BackgroundScheduler(daemon=True, executors=executors, job_defaults=job_defaults)
sched.start()


app = Flask(__name__)

#logger to store logs in file detailed_log.log
logging.basicConfig(filename='detailed_log.log', level=logging.INFO, format='%(asctime)-15s %(message)s')

app.logger.info('$$$$$$$$$$$$$$$$$$$$$$ Flask Server Started $$$$$$$$$$$$$$$$$$$$$$$')

#Initial API key which user can use to call API
initial_key = "8qf6KFBzZYqgPw"
#dictionary to store remaining quota of all API keys
key_quota = {}
#Initial quota of 100 is assigned
key_quota[initial_key] = 100

#function to create SQLite database and table to store videos
def db_init():
    try:
        connection = sqlite3.connect("video_data.db")
        c = connection.cursor()
        c.execute("create table videos(videoId text NOT NULL PRIMARY KEY, title text, description text, publishTime TIMESTAMP, thumbnailUrl text)")
        connection.commit()
        connection.close()
    except Exception as e:
        print(e)
    
#function will run on start of the flask app
db_init()
    

#credentials and variables require to fetch videos from youtube
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,developerKey="AIzaSyCbTVzlUSuyiSWQURLdULOJebZN79MbMqc")

#function to use youtube api to fetch the data. This function will fetch max 10 videos. We can modify this according to 
#requirements
def youtubeSearch(query, max_results=10,order="relevance", token=None, location=None, location_radius=None):
    app.logger.info("@@@@@@@@@@@@@@@@@@@@@@@@@@@querying")
    search_response = youtube.search().list(
    q=query,
    type="video",
    pageToken=token,
    order = order,
    part="id,snippet",
    maxResults=max_results,
    location=location,
    locationRadius=location_radius).execute()
    return search_response

#function that will run in the background in asynchronous mode to fetch the data from youtube and store it in the Database
def querycont_vid(qr):
    app.logger.info('inside status')
    app.logger.info("@@@@@@@@@@@@@@@@@@@@@@@@@@@ :%s " + qr)
    response = youtubeSearch(qr)
    for res in response["items"]:
        videoId = res["id"]["videoId"]
        title= res["snippet"]["title"]
        title = title.lower()
        description = res["snippet"]["description"]
        description = description.lower()
        publishTime = datetime.strptime(res["snippet"]["publishTime"], '%Y-%m-%dT%H:%M:%SZ')
        thumbnailUrl = res["snippet"]["thumbnails"]["default"]["url"]
        try:
            connection = sqlite3.connect("video_data.db")
            c = connection.cursor()
            c.execute("insert into videos values (?, ?, ?, ?, ?)", (videoId, title, description, publishTime, thumbnailUrl))
            connection.commit()
            connection.close()
        except Exception as e:
            print(e)
        
    return response

#Scheduler will run this function after every 1000 second. we caan modify this 1000seconds to 10 seconds
#I have kept 1000 seconds because if I keep it as 10 seconds it will finish my all free google youtube api quota
#predefined search query is cricket. we will fetch and store videos regarding cricket
sched.add_job(querycont_vid, 'interval', seconds = 1000, args=["crciket"])


#We will run this function once as the flask app starts so that it will load the data and store it in db
#predefined search query is cricket
querycont_vid("cricket")
  
    
#entry api call
@app.route('/',methods=['GET','POST'])
@cross_origin()
def homepage():
    app.logger.info('inside rfm container')
    return """<h1>Welcome FamPay!</h1>"""


#function to validate api key
def validate_user(auth_key):
    if auth_key in key_quota and key_quota[auth_key] != 0:
        key_quota[auth_key] -= 1
        return True
    else:
        return False


#GET API which returns the stored video data in a paginated response sorted in descending order of published datetime
@app.route('/get_all',methods=['GET','POST'])
@cross_origin()
def query_all():
    app.logger.info('inside all')
    #validating api key
    if not validate_user(request.headers.get('auth_key')):
        app.logger.info("authentication failed")
        return json.dumps(
                    {
                        "message": "ACCESS DENIED",
                        "additional_info": "Authorisation Failed, use the right authentication token!"
                    }
                )
    data = request.get_json()   
    lt = str(data["limit"])   
    off = str(data["offset"])
    connection = sqlite3.connect("video_data.db")
    c = connection.cursor()
    c.execute("select * from videos order by publishTime DESC Limit '" +lt+"' OFFSET '" + off + "' ;")
    res = c.fetchall()
    connection.commit()
    connection.close()
    dic = {}
    #returning results in the form of dictionary
    dic["all"] = res
    return dic

#search API to search the stored videos using their title and description
@app.route('/search',methods=['GET','POST'])
@cross_origin()
def srch():
    app.logger.info('inside all')
    
    if not validate_user(request.headers.get('auth_key')):
        app.logger.info("authentication failed")
        return json.dumps(
                    {
                        "message": "ACCESS DENIED",
                        "additional_info": "Authorisation Failed, use the right authentication token!"
                    }
                )
    data = request.get_json()   
    srch_str = str(data["search_str"])   
    qry = "select * from videos "

    #constructing query to extract rows matching the search string
    srch_str = srch_str.split()
    if len(srch_str):
        qry += " where "
    for i in range(len(srch_str)):
        x = srch_str[i]
        qry += " videos.title like '%"+x+"%'  or " 

    for i in range(len(srch_str)):
        x = srch_str[i]
        if i == len(srch_str)-1:
            qry += " videos.description like '%"+x+"%' " 
        else:
            qry += " videos.description like '%"+x+"%' or " 

    connection = sqlite3.connect("video_data.db")
    c = connection.cursor()
    c.execute(qry)
    res = c.fetchall()
    connection.commit()
    connection.close()
    dic = {}
    #returning results in the form of dictionary
    dic["all"] = res
    return dic


#API to check quota status of API key
@app.route('/quota_status',methods=['GET','POST'])
@cross_origin()
def quot_stat():
    app.logger.info('inside quota')
    return key_quota

#API for supplying multiple API keys so that if quota is exhausted 
#on one, it can generate another key and will use that key
@app.route('/gen_key',methods=['GET','POST'])
@cross_origin()
def key_gen():
    app.logger.info('inside gen key')
    new_key = secrets.token_urlsafe(10)
    key_quota[new_key] = 100
    dic = {}
    dic["new_key"] = new_key
    return dic



if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False, port = 5022)
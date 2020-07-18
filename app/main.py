from fastapi import FastAPI
import requests
import logging
import base64
import time
import json
import pickle
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
logging.info('App Started')
app = FastAPI()

with open('/config/cameras.json') as f:
  cameradata = json.load(f)

with open('/config/settings.json') as f:
  settings = json.load(f)

sssUrl = settings["sssUrl"]
deepstackUrl = settings["deepstackUrl"]
username = settings["username"]
password = settings["password"]
#detection_labels= ['car', 'person']
detection_labels=settings["detect_labels"]
min_sizex=int(settings["min_sizex"])
min_sizey=int(settings["min_sizey"])


def save_cookies(requests_cookiejar, filename):
    with open(filename, 'wb') as f:
        pickle.dump(requests_cookiejar, f)

def load_cookies(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)

# Create a session with synology 
url = f"{sssUrl}/webapi/auth.cgi?api=SYNO.API.Auth&method=Login&version=1&account={username}&passwd={password}&session=SurveillanceStation"

#  Save cookies
r = requests.get(url)
save_cookies(r.cookies, 'cookie')



@app.get("/{camera_id}")
async def read_item(camera_id):
    start = time.time()
    url = f"{sssUrl}/webapi/entry.cgi?camStm=1&version=2&cameraId={camera_id}&api=%22SYNO.SurveillanceStation.Camera%22&method=GetSnapshot"
    triggerurl = cameradata[f"{camera_id}"]["triggerUrl"]
    cameraname = cameradata[f"{camera_id}"]["name"]
 
    response = requests.request("GET", url, cookies=load_cookies('cookie'))
    logging.debug('Requested snapshot')
    if response.status_code == 200:
        with open(f"tmp/{camera_id}.jpg", 'wb') as f:
            f.write(response.content)
            logging.debug('Snapshot downloaded')

    image_data = open(f"tmp/{camera_id}.jpg","rb").read()

    response = requests.post(f"{deepstackUrl}/v1/vision/detection",files={"image":image_data},timeout=10).json()

    i = 0
    for object in response["predictions"]:
        confidence = round(100 * object["confidence"])
        label = object["label"]
        sizex=int(object["x_max"])-int(object["x_min"])
        sizey=int(object["y_max"])-int(object["y_min"])
        logging.debug(f"  {label} ({confidence}%)   {sizex}x{sizey}")
        if label in detection_labels and \
           sizex>min_sizex and \
           sizey>min_sizey:

            payload = {}
            response = requests.request("GET", triggerurl, data = payload)
            end = time.time()
            runtime = round(end - start, 1)
            logging.info(f"{confidence}% sure we found a {label} - triggering {cameraname} - took {runtime} seconds")
            return ("triggering camera because something was found")
        i += 1


    end = time.time()
    runtime = round(end - start, 1)     
    logging.info(f"{cameraname} triggered - nothing found - took {runtime} seconds") 
    return (f"{cameraname} triggered - nothing found")

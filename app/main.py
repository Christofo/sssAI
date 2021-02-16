from fastapi import FastAPI
from PIL import Image, ImageDraw

import requests
import logging
import base64
import time
import json
import pickle
import time
import os

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
logging.info('App Started')
app = FastAPI()

with open('/config/cameras.json') as f:
  cameradata = json.load(f)

with open('/config/settings.json') as f:
  settings = json.load(f)

sssUrl = settings["sssUrl"]
deepstackUrl = settings["deepstackUrl"]
homebridgeWebhookUrl = settings["homebridgeWebhookUrl"]
username = settings["username"]
password = settings["password"]
#detection_labels= ['car', 'person']
detection_labels=settings["detect_labels"]
timeout=int(settings["timeout"])
min_sizex=int(settings["min_sizex"])
min_sizey=int(settings["min_sizey"])
min_confidence=int(settings["min_confidence"])


if "triggerInterval" in settings:
    trigger_interval = settings["triggerInterval"]
else:
    # If no trigger interval set then make it 60s (i.e. don't send another event from the triggered camera for at least 60s to stop flooding event notifications
    trigger_interval = 60 
if "captureDir" in settings:
    capture_dir = settings["captureDir"]

def save_cookies(requests_cookiejar, filename):
    with open(filename, 'wb') as f:
        pickle.dump(requests_cookiejar, f)

def load_cookies(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)


# Create a session with synology 
url = f"{sssUrl}/webapi/auth.cgi?api=SYNO.API.Auth&method=Login&version=1&account={username}&passwd={password}&session=SurveillanceStation"

#  Save cookies
logging.info('Session login: ' + url)
r = requests.get(url)
save_cookies(r.cookies, 'cookie')

# Dictionary to save last trigger times for camera to stop flooding the capability
last_trigger_fn = f"/tmp/last.dict";
def save_last_trigger(last_trigger):
    with open(last_trigger_fn, 'wb') as f:
        pickle.dump(last_trigger, f)

def load_last_trigger():
    if os.path.exists(last_trigger_fn):
        with open(last_trigger_fn, 'rb') as f:
            return pickle.load(f)
    else:
        return {}

@app.get("/{camera_id}")
async def read_item(camera_id):
    start = time.time()
    cameraname = cameradata[f"{camera_id}"]["name"]
    predictions = None
    last_trigger = load_last_trigger()

    # Check we are outside the trigger interval for this camera
    if camera_id in last_trigger:
        t = last_trigger[camera_id]
        logging.info(f"Found last camera time for {camera_id} was {t}")
        if (start - t) < trigger_interval:
            msg = f"Skipping detection on camera {camera_id} since it was only triggered {start - t}s ago"
            logging.info(msg)
            return (msg)
        else:
            logging.info(f"Processing event on camera (last trigger was {start-t}s ago)")
    else:
        logging.info(f"No last camera time for {camera_id}")

    url = f"{sssUrl}/webapi/entry.cgi?camStm=1&version=2&cameraId={camera_id}&api=%22SYNO.SurveillanceStation.Camera%22&method=GetSnapshot"
    triggerurl = cameradata[f"{camera_id}"]["triggerUrl"]
    if "homekitAccId" in cameradata[f"{camera_id}"]:
        homekit_acc_id = cameradata[f"{camera_id}"]["homekitAccId"]
 
    response = requests.request("GET", url, cookies=load_cookies('cookie'))
    logging.debug('Requested snapshot: ' + url)
    if response.status_code == 200:
        with open(f"tmp/{camera_id}.jpg", 'wb') as f:
            f.write(response.content)
            logging.debug('Snapshot downloaded')
    
    snapshot_file = f"tmp/{camera_id}.jpg"
    image_data = open(snapshot_file,"rb").read()
    logging.info('Requesting detection from DeepStack...');
    s = time.perf_counter()
    response = requests.post(f"{deepstackUrl}/v1/vision/detection",files={"image":image_data},timeout=timeout).json()

    e = time.perf_counter() 
    logging.debug(f'Got result: {json.dumps(response, indent=2)}. Time: {e-s}s');
    if not response["success"]:
        return ("Error calling Deepstack: " + response["error"]);
    
    labels = ''
    predictions = response["predictions"]
    for object in predictions:
        label = object["label"]
        if label != 'person':
            labels = labels + label + ' ';
    
    i = 0
    found = False

    for object in response["predictions"]:
        confidence = round(100 * object["confidence"])
        label = object["label"]
        sizex=int(object["x_max"])-int(object["x_min"])
        sizey=int(object["y_max"])-int(object["y_min"])
        logging.debug(f"  {label} ({confidence}%)   {sizex}x{sizey}")

        if not found and label in detection_labels and \
           sizex>min_sizex and \
           sizey>min_sizey and \
           confidence>min_confidence:

            payload = {}
            response = requests.request("GET", triggerurl, data = payload)
            end = time.time()
            runtime = round(end - start, 1)
            logging.info(f"{confidence}% sure we found a {label} - triggering {cameraname} - took {runtime} seconds")

            found = True
            last_trigger[camera_id] = time.time()
            save_last_trigger(last_trigger)
            logging.debug(f"Saving last camera time for {camera_id} as {last_trigger[camera_id]}")

            if homebridgeWebhookUrl is not None and homekit_acc_id is not None:
                hb = requests.get(f"{homebridgeWebhookUrl}/?accessoryId={homekit_acc_id}&state=true");
                logging.debug(f"Sent message to homebridge webhook: {hb.status_code}");
            else:
                logging.debug(f"Skipping HomeBridge Webhook since no webhookUrl or accessory Id");
        i += 1
    
    end = time.time()
    runtime = round(end - start, 1)    
    if found:
        save_image(predictions, cameraname, snapshot_file )
        return ("triggering camera because something was found - took {runtime} seconds")
    else:
        logging.info(f"{cameraname} triggered - nothing found - took {runtime} seconds") 
        return (f"{cameraname} triggered - nothing found")

def save_image(predictions, camera_name, snapshot_file):
    start = time.time()
    logging.debug(f"Saving new image file....");
    im = Image.open(snapshot_file)
    draw = ImageDraw.Draw(im)
    for object in predictions:
        confidence = round(100 * object["confidence"])
        label = f"{object['label']} ({confidence}%)"
        draw.rectangle((object["x_min"], object["y_min"], object["x_max"], object["y_max"]), outline=(255, 230, 66), width=2);
        draw.text((object["x_min"]+10, object["y_min"]+10), f"{label}", fill=(255,230,66))
    fn = f"{capture_dir}/{camera_name}-{start}.jpg";
    im.save(f"{fn}", quality=100);
    im.close()
    end = time.time()
    runtime = round(end - start, 1)    
    logging.debug(f"Saved captured and annotated image: {fn} in {runtime} seconds.");

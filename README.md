# sssAI
AI based motion detection for Synology Surveillance Station - For instructions on use see https://blog.cadams.me - Wiki coming soon!

Features:
* Uses https://deepstack.cc/ for object recognition
* Use the native DS Cam app for mobile notifications
* HomeKit integration (via HomeBridge and Homebridge Webhooks & Camera-ffmpeg plugins)
* Captured image with border-box annotations saved for review


## Performance 
* DS920+ (20GB RAM) - Deepstack set to "low" - ~2 seconds for image recognition 
* DS918+ (12GB RAM) - Deepstack set to "medium" - ~4 seconds for image recognition
* DS713+ (4GB RAM) - Deepstack set to "low" - ~9 seconds for image recognition 


## Running using docker-compose

If you want to run the containers in a docker host separate from your Synology
device, you can use the `docker-compose.yml` file.

1. Clone this repository on your docker host
1. Create the required directories (`mkdir -p ./data/captures ./data/deepstack`)
1. Create `settings.json` and `cameras.json` (see `*.example` files)
1. Optionally edit `docker-compose.yml` to configure your time zone and network ports.
1. Start the services (`docker-compose up -d`)
1. Optionally tail the log files (`docker-compose logs -tf sssai`)

On the first time you run the service

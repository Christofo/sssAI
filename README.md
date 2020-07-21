# sssAI
AI based motion detection for Synology Surveillance Station (based on work done by Christofo/sssAi).

This fork adds:
* HomeKit integration (via HomeBridge and Homebridge Webooks & Camera-ffmpeg plugins)
* Captured image with border box annotations
* Trigger Interval per camera 

# HomeKit
The HomeKit integration presents as a normal motion alert for that camera that has been added to HomeBridge (via Camera-ffmpeg). You need to add:
                    "motion": true,
                    "switches": true
to the camera definition in HomeBridge, and add the appropriate Webhook based switches with Homebridge Webooks plugin. 

When you setup the webhook plugin you need at add the URL to settings.json via the parameter 'homebridgeWebhookUrl (e.g. "http://192.1.1.67:51828")

# Border Box Annotations
If you include 'captureDir' as a setting in the config.json, then the images that are captured will be saved to that directory with the AI meta-data overlaid (label name, and confidence). For example: Person (98%). 

You should map a volume to the docker image that is on your NAS.

## Trigger Interval 
The trigger interval (defaults to 60s) allows the AI to be triggered after an interval after a successful match. This lowers the number of notifications for one "event" and also reduces the CPU impact to the Synology NAS.

If you want to configure up or down from the 60 second default, use 'triggerInterval' setting in the settings.json file (in seconds).

## To do
* Investigate getting a link into DS-Cam to take you straight there.
* Make the Synology Notification Alert optional (you can do this on the Synology directly in the alert config, but need to add to the code)

## Other
* I am using a DS-918+ with 12GB RAM and it takes around 4s to do the DeepStack AI object matching


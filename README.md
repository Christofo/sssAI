# Check out [SynoAI](https://github.com/djdd87/SynoAI) - I no longer maintain sssAI

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


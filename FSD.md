<!-- Functional Specification Document -->
# Project Name: Ultimate Pi Soud Box
## 1. Hardware Requirements
- Raspberry Pi Zero 2w
- Adafruit I2S Audio DAC
- 1.3 inch OLED Display (SH1106) (port=1, address=0x3C) (128x64 pixels)
- Rotary Encoder with Push Button (17, 22, max_steps=2) Button(27)
## 2. Software Requirements
- Raspbian OS
- Python 3.x
- Yt-DLP (YouTube Downloader Library)
## 3. System Architecture
- There Wiill be predefined Menu Components will be in the main file. which can later be increased or decreased as per the requirement. The main file will be responsible for handling the user interface and interactions, while separate modules will handle specific functionalities such as music playback, YouTube streaming, and system settings.
- This should be stored in a menu.json for easy access and modification. 
- each component will have its own module that will handle the specific functionality related to that component.
## 4. Menu Components
    "My Music",
    "Youtube Online",
    "Connect Phone",
    "Internet Radio",
    "MyIP",
    "BT Settings",
    "System Volume",
    "ShutDown"
## 5. Functionalities
### 5.1 My Music
- This component will allow users to play music stored locally on the Raspberry Pi. It will support various audio formats and provide basic playback controls (play, pause, stop, next, previous).
- Users can navigate through their music library using the rotary encoder and select songs to play.
- need to implement a feature to display the currently playing song on the OLED display, along with options to manage playlists and organize music files.
- The component will also include a feature to shuffle and repeat songs, as well as a search function to quickly find specific tracks in the music library.
- The OLED Display Will show the current song title, artist - in Scrolling text if it exceeds the display width, and There will be a progress bar to show the current playback position of the song.
- There Will be a bar graph floating randomly on around the corners
- There will be a display of current bitrate  and volume tile and signal strength of WIfi if connected.
### 5.2 Youtube Online
- This component will enable users to stream music directly from YouTube. It will utilize the Yt-DLP library to fetch and play audio from YouTube videos.
- Users can search for songs or playlists and select them for playback. 
- The system will also provide options to manage the YouTube streaming experience, such as adjusting playback quality and handling buffering issues.
- The component will also include a feature to save favorite YouTube songs or playlists for quick access in the future.
- This component will be able to view sqlite3 database to get songlist with their ID and other metadata, and then use that ID to fetch the song from YouTube and play it.
### 5.3 Connect Phone
- This component will allow users to connect their smartphones to the Raspberry Pi via Bluetooth. Once connected, users can stream music from their phones to the Raspberry Pi's audio output.
- From DBus, we can get the list of paired devices and display them on the OLED display. And currently playing song information can also be fetched and displayed on the OLED display. 
- must include previous and next song controls.
### 5.4 Internet Radio
- This component will allow users to listen to internet radio stations directly from the Raspberry Pi.
- Users can browse and select from a list of available radio stations.
- Load the list from CSV file and display it on the OLED display. Users can select a station to start streaming.
- The system will provide options to adjust the volume and manage the playback experience.
### 5.5 MyIP
- This component will display the current IP address of the Raspberry Pi on the OLED display.
-  It will also provide options to refresh the IP address and display additional network information if needed.
-  If Network is not connected, it will show "No Network" on the OLED display.
-  and show current available WiFi networks and allow users to connect to a network by selecting it from the list and entering the password with the rotary encoder.
### 5.6 BT Settings
- This component will allow users to configure and manage the Bluetooth settings on the Raspberry Pi.
- Users can enable or disable Bluetooth, manage paired devices, and adjust Bluetooth visibility settings.
### 5.7 System Volume
- This component will allow users to adjust the system volume of the Raspberry Pi. It will provide options to increase, decrease, or mute the volume.
### 5.8 ShutDown
- This component will allow users to safely shut down the Raspberry Pi. 
### 5.9 DLNA/UPnP Support
- This component will enable users to stream music from DLNA/UPnP compatible devices on the same network. Users can browse and select music from their DLNA/UPnP devices and play it through the Raspberry Pi's audio output.
- Like local music, same UI will be used to stream music from DLNA/UPnP devices, and the currently playing song information will be displayed on the OLED display.
- This component will also include options to manage the DLNA/UPnP streaming experience, such as adjusting playback quality and handling buffering issues.
## 6. User Interface
- The user interface will be designed to be simple and intuitive, allowing users to easily navigate through the menu and access the various functionalities. The OLED display will provide clear visual feedback, and the rotary encoder will be used for navigation and selection.
- The interface will also include visual indicators for the currently selected menu item and the currently playing song, as well as any relevant information such as the song title, artist, and album art (if available).
## 7. Future Enhancements  
- Implementation of a web interface for remote control and management of the Ultimate Pi Sound Box from a smartphone or computer. 
## 8. General Notes
- The system will be designed to be modular and extensible, allowing for easy addition of new features and functionalities in the future.
- The OLED display will must have scrolling text support to accommodate longer song titles and menu items.
- The OLED Diasplay Must Show Current Time in Big at center and the current date in small at the bottom when nothing is playing.
```
_________________________________________________________________________
|                        192.168.1.100               |||| <-Small to big|
|                                                                       |
|                                                                       |
|                                                                       |
|                                                                       |
|                |   |-----|       |     |   |     |                    |
|                |   |     |   0   |     |   |     |                    |
|                |   |     |       |     |   |     |                    |
|                |   ------|   0   +-----|   +-----|                    |
|                |   ______|             |         |                    |
|                                                                       |
|                                                                       |
|                                                                       |
|                          31-03-2026                                   |
|                                                                       |
|                                                                       |
|                                                                       |
|_______________________________________________________________________|
```
for more info on OLED display config refer to 
[Volumio Community](https://community.volumio.com/t/plugin-mpd-oled-installation-configuration-plugin/44823)
[mpd_oled GitHub Repository](https://github.com/antiprism/mpd_oled)
- Make a separate directory for each component to keep the code organized and modular. Each directory will contain the necessary files and modules related to that specific component, allowing for easier maintenance and future enhancements. And just the final main file will be outside the directory and after writing the code make a README file where usage and detailed explanation will be there also requirements and installation steps will be there.
- Make a progress.md file where the progress of the project will be updated regularly, and any challenges or issues faced during development will be documented along with their solutions. This will help in tracking the development process and provide insights for future improvements.

----
# ISSUES
- the last line in OLED Display overlapping each other, need to find a way to prevent that. - **Closed**
- after placing songs in [app.config.music_dir](/home/infinity/Desktop/v2/data/music) its still showing
                "Local playback module"
                "is not wired yet."
                "Place songs under"
                str(app.config.music_dir)
            "Long press to exit" 
            Where also the lst line is overlapping with the previous line, need to find a way to fix it. - **Closed**
- Internet Radio is not working properly, need to find a way to fix it. - **Closed**
- For the screen saver, |||| <-Small to big is not working properly, where I want to show it as increasing in size from small in height (these pipes) - **Closed**
- Also implement WEB interface for remote control and management of the Ultimate Pi Sound Box from a smartphone or computer using Flask or FastAPI in localhost. where I can access it from the browser after connecting to the same network and entering the IP address of the Raspberry Pi in the browser. - **Closed**
- For Clock screen saver thing Volume and date is overlapping each other, need to find a way to prevent that. - **Closed**
- Scrolling text is not working properly, need to find a way to implement it correctly. - Horizontal scrolling not working when the text is bigger than the display width. - **Closed**
- No place in menu for DLNA/UPnP Support, need to find a way to add it in the menu and implement it. - **Closed**
  - DLNA/UPnP discovery, browsing, and basic playback wiring added in the component.
  - V2 for web interface: Need to be interactive, colorful, modern looking, where I can see the current song playing and fetch the every list like music list, radio station list, YouTube playlist and also have the option to play/pause/next/previous song from the web interface. - **Closed**
- Need to shift the local music directory path to "/home/infinity/Music" - **PRIORITY HIGH** - **Closed**

"""Get user input and run the bioreactor."""
import PySimpleGUI as sg
import humanize
import datetime
import time
import threading
import RPi.GPIO as GPIO

# Create a list of dictionaries to keep track of which GPIO pins are for which
# chamber
GPIO_PINS = [
    {
        "add": 3,
        "remove": 5
    },
    {
        "add": 7,
        "remove": 8
    },
    {
        "add": 10,
        "remove": 12
    },
    {
        "add": 11,
        "remove": 13
    },
    {
        "add": 18,
        "remove": 19
    },
    {
        "add": 21,
        "remove": 22
    },
    {
        "add": 23,
        "remove": 24
    },
    {
        "add": 31,
        "remove": 32
    }
]

def main():
    """Top level function."""
    # Initialize some variables that are going to keep track of state
    chambers = []
    for i in range(8):
        chambers.append({
            "chamber_id": i + 1,
            "is_in_use": False,
            "last_changed": datetime.datetime.now(),
            "media_in_chamber": 0,
            "status": "Unused"
        })
    shutdown = {}
    shutdown["settings"] = False

    # Load the GUI that can input the user settings
    get_user_settings(chambers, shutdown)

    # Load the monitoring window if the user didn't cancel
    if not shutdown["settings"]:
        # Set up the GPIO pins
        GPIO.setmode(GPIO.BOARD)
        for chamber in GPIO_PINS:
            GPIO.setup(chamber["add"], GPIO.OUT)
            GPIO.setup(chamber["remove"], GPIO.OUT)

        # Define a new start time and make the chambers time accurate
        start_time = datetime.datetime.now()
        for i in range(8):
            chambers[i]["last_changed"] = datetime.datetime.now()
        get_monitoring_window(chambers, start_time)

def get_user_settings(chambers, shutdown):
    """Get the user input in a graphical format."""
    # Set the font and the theme of the GUI
    default_font = 'Roboto 20'
    sg.theme('LightGray1')

    # Define the layout of the starting window
    start_layout = [[sg.Text(text = "Hello from Vessegen!", font='Roboto 40', text_color='red', pad=((0,0), (120, 20)))],
                    [sg.Text(text = "Select 'Get Started' below to begin.", font=default_font, pad=(0,10))],
                    [sg.Button("Get Started", font=default_font), sg.Cancel(font=default_font)]]
    
    # Define the layout to allow the user to select the chambers that will be in
    # use
    chamber_layout = [[sg.Text(text = "Which chambers will you be using?", font='Roboto 30', pad=((0,0), (120, 20)))],
                      [sg.Checkbox('Select All', default=False, font=default_font, key='selectallchamber', enable_events=True)],
                      [sg.Checkbox('Chamber 1', default=False, font=default_font, key='chamber1', enable_events=True), sg.Checkbox('Chamber 2', default=False, font=default_font, key='chamber2', enable_events=True)],
                      [sg.Checkbox('Chamber 3', default=False, font=default_font, key='chamber3', enable_events=True), sg.Checkbox('Chamber 4', default=False, font=default_font, key='chamber4', enable_events=True)],
                      [sg.Checkbox('Chamber 5', default=False, font=default_font, key='chamber5', enable_events=True), sg.Checkbox('Chamber 6', default=False, font=default_font, key='chamber6', enable_events=True)],
                      [sg.Checkbox('Chamber 7', default=False, font=default_font, key='chamber7', enable_events=True), sg.Checkbox('Chamber 8', default=False, font=default_font, key='chamber8', enable_events=True)],
                      [sg.Button("Submit Chambers", font=default_font, pad=(5,20)), sg.Cancel(font=default_font, pad=(5,20), key='Cancel1')]]
    
    # Currently unused, but allows the user to assign subsettings for each chamber.
    # Because we are just going to allow the user to click a button to change the media,
    # we don't need this functionality.
    same_settings_layout = [[sg.Text(text = "Will the chambers be using the same settings?", font='Roboto 30', pad=((0, 0),(60, 20)))],
                      [sg.Radio('Yes', 'samesettings', key='samesettingsyes', font=default_font, default=False)], [sg.Radio('No', 'samesettings', font=default_font, default=False)],
                      [sg.Button("Next", font=default_font, pad=(5,20), key='samesettingsnext'), sg.Cancel(font=default_font, pad=(5,20), key='Cancel2')]]
    
    # Allows the user to specify how long the experiment will run
    same_settings_time = [[sg.Text(text = "How long should the experiment run for?", font='Roboto 30', pad=(0,20))],
                      [sg.InputText(size=(2,2), font=default_font, default_text='0'), sg.Text(text = "weeks,", font=default_font), sg.InputText(size=(2,2), font=default_font, default_text='0'), sg.Text(text = "days,", font=default_font), sg.InputText(size=(2,2), font=default_font, default_text='0'), sg.Text(text = "hours", font=default_font)],
                      [sg.Button("Next", font=default_font, pad=(5,20), key='samesettingstimenext'), sg.Cancel(font=default_font, pad=(5,20), key='Cancel3')]]
    
    # If we were doing automated media changes, this would allow the user to specify
    # the time between media changes for each chamber.
    same_settings_media = [[sg.Text(text = "How much time should there be between media changes?", font='Roboto 30', pad=(0,20))],
                      [sg.InputText(size=(2,2), font=default_font, default_text='0'), sg.Text(text = "days,", font=default_font), sg.InputText(size=(2,2), font=default_font, default_text='0'), sg.Text(text = "hours", font=default_font)],
                      [sg.Button("Next", font=default_font, pad=(5,20), key='samesettingsmedianext'), sg.Cancel(font=default_font, pad=(5,20), key='Cancel4')]]

    # Put the various layouts into a list so we can call them
    layout = [[sg.Column(start_layout, key='-STARTCOL-', element_justification='center'),
               sg.Column(chamber_layout, visible=False, key='-CHAMBERCOL-', element_justification='center'),
               sg.Column(same_settings_layout, visible=False, key='-SAMESETTINGSCOL-', element_justification='center'),
               sg.Column(same_settings_time, visible=False, key='-SAMESETTINGSTIME-', element_justification='center'),
               sg.Column(same_settings_media, visible=False, key='-SAMESETTINGSMEDIA-', element_justification='center')]]
    
    # Initialize the window
    window = sg.Window("Vessegen Bioreactor Software", layout, element_justification='center', size=(1024,600))
    
    # Start in the starting window column
    current_layout = '-STARTCOL-'

    # Loop until the user closes the window (or submits the settings)
    while True:
        # Read the user input from the GUI
        event, values = window.read()

        # If the user has selected "Cancel" or closed the window, then exit the
        # program
        if event in ('Cancel', 'Cancel1', 'Cancel2', 'Cancel3', None, sg.WIN_CLOSED):
            shutdown["settings"] = True
            break
        
        # If the user has selected Get Started, then take them to where they can
        # select the chambers
        elif event == 'Get Started':
            window[current_layout].update(visible=False)
            current_layout = '-CHAMBERCOL-'
            window[current_layout].update(visible=True)

        # If the user has selected "Select All", then select all the chambers
        elif (event == 'selectallchamber' and values['selectallchamber'] == True):
            window['chamber1'].update(True)
            window['chamber2'].update(True)
            window['chamber3'].update(True)
            window['chamber4'].update(True)
            window['chamber5'].update(True)
            window['chamber6'].update(True)
            window['chamber7'].update(True)
            window['chamber8'].update(True)
            for i in range (8):
                chambers[i]["is_in_use"] = True
                chambers[i]["status"] = "Running"
        
        # If the user unselected "Select All", then deselect all the chambers
        elif (event == 'selectallchamber' and values['selectallchamber'] == False):
            window['chamber1'].update(False)
            window['chamber2'].update(False)
            window['chamber3'].update(False)
            window['chamber4'].update(False)
            window['chamber5'].update(False)
            window['chamber6'].update(False)
            window['chamber7'].update(False)
            window['chamber8'].update(False)
            for i in range(8):
                chambers[i]["is_in_use"] = False
                chambers[i]["status"] = "Unused"

        # If the user has selected a chamber, then set it as in use 
        elif event in ('chamber1', 'chamber2', 'chamber3', 'chamber4', 'chamber5', 'chamber6', 'chamber7', 'chamber8'):
            if values['selectallchamber'] == True:
                window['selectallchamber'].update(False)
            chambers[int(event[7]) - 1]["is_in_use"] = not chambers[int(event[7]) - 1]["is_in_use"]
            if chambers[int(event[7]) - 1]["is_in_use"]:
                chambers[int(event[7]) - 1]["status"] = "Running"
            else:
                chambers[int(event[7]) - 1]["status"] = "Unused"
        
        # If the user submits their chamber selection, then move to the monitoring
        # page
        elif event == 'Submit Chambers':
            break
    
    window.close()

def get_monitoring_window(chambers, start_time):
    """Display information for the chambers and allow user control."""
    # Set the font and the theme of the GUI
    default_font = 'Roboto 12'
    sg.theme('LightGray1')

    # Define the layout of the monitoring window, however this must be done after
    # the settings have been defined.
    chamber_frames = []
    chambers_one_through_four = []
    for i in range(4):
        if chambers[i]['is_in_use']:
            chambers_one_through_four.append(sg.Frame("Chamber " + str(chambers[i]['chamber_id']),
                                           [
                                            [sg.Text(text = "Status: " + chambers[i]["status"], font='Roboto 12', key='-CHAMBER' + str(chambers[i]['chamber_id']) + '-STATUS-')],
                                            [sg.Text(text = "Last Changed: " + humanize.naturaltime(datetime.datetime.now() - chambers[i]["last_changed"]), font='Roboto 12', key='-CHAMBER' + str(chambers[i]['chamber_id']) + '-LASTCHANGE-')],
                                            [sg.Text(text = "Media in Reservoir: " + str(chambers[i]["media_in_chamber"]) + " mL", font='Roboto 12', key='-CHAMBER' + str(chambers[i]['chamber_id']) + '-MEDIARES-')],
                                            [sg.Button("Add Media to Reservoir", font=default_font, key='-CHAMBER' + str(chambers[i]['chamber_id']) + '-ADDMEDIA-')],
                                            [sg.Button("Change Media", font=default_font, key='-CHAMBER' + str(chambers[i]['chamber_id']) + '-CHANGEMEDIA-')]
                                           ], font='Roboto 20', element_justification='center', title_color="red", size=(240,200)))
        else:
            chambers_one_through_four.append(sg.Frame("Chamber " + str(chambers[i]['chamber_id']),
                                           [
                                            [sg.Text(text = "Status: " + chambers[i]["status"], font='Roboto 12', key='-CHAMBER' + str(chambers[i]['chamber_id']) + '-STATUS-')]
                                           ], font='Roboto 20', element_justification='center', title_color="red", size=(240,200)))
    chamber_frames.append(chambers_one_through_four)
    chambers_five_through_eight = []
    for i in range(4, 8):
        if chambers[i]['is_in_use']:
            chambers_five_through_eight.append(sg.Frame("Chamber " + str(chambers[i]['chamber_id']),
                                           [
                                            [sg.Text(text = "Status: " + chambers[i]["status"], font='Roboto 12', key='-CHAMBER' + str(chambers[i]['chamber_id']) + '-STATUS-')],
                                            [sg.Text(text = "Last Change: " + humanize.naturaltime(datetime.datetime.now() - chambers[i]["last_changed"]), font='Roboto 12', key='-CHAMBER' + str(chambers[i]['chamber_id']) + '-LASTCHANGE-')],
                                            [sg.Text(text = "Media in Reservoir: " + str(chambers[i]["media_in_chamber"]) + " mL", font='Roboto 12', key='-CHAMBER' + str(chambers[i]['chamber_id']) + '-MEDIARES-')],
                                            [sg.Button("Add Media to Reservoir", font=default_font, key='-CHAMBER' + str(chambers[i]["chamber_id"]) + '-ADDMEDIA-')],
                                            [sg.Button("Change Media", font=default_font, key='-CHAMBER' + str(chambers[i]["chamber_id"]) + '-CHANGEMEDIA-')]
                                           ], font='Roboto 20', element_justification='center', title_color="red", size=(240,200)))
        else:
            chambers_five_through_eight.append(sg.Frame("Chamber " + str(chambers[i]['chamber_id']),
                                           [
                                            [sg.Text(text = "Status: " + chambers[i]["status"], font='Roboto 12', key='-CHAMBER' + str(chambers[i]['chamber_id']) + '-STATUS-')]
                                           ], font='Roboto 20', element_justification='center', title_color="red", size=(240,200)))
    chamber_frames.append(chambers_five_through_eight)

    # Create a small little running indicator
    led_spot = sg.Graph((20,20), (0,0), (20,20), key="-LED-SPOT-", enable_events=True)
    
    # Define the layout of the window
    layout = [
        [sg.Text(text = "System Status and Control", font='Roboto 30', pad=(0,5))],
        chamber_frames,
        [led_spot, sg.Text(text = "System running for: " + humanize.naturaldelta(datetime.datetime.now() - start_time), font='Roboto 18', pad=(0,5), key='-RUNTIME-')],
        [sg.Button("Add Media to All Reservoirs", font='Roboto 15', pad=(5,5)), sg.Button("Change Media in All Chambers", font='Roboto 15', pad=(5,5)), sg.Button("Finish", font='Roboto 15', pad=(5,5))]
    ]

    # Initialize the window
    window = sg.Window("Vessegen Bioreactor Software", layout, element_justification='center', size=(1024,600), finalize=True)

    # Draw the LED
    led = led_spot.draw_circle((10,10), 9, fill_color='white', line_color="black", line_width=1)
    led_color = "white"
    # Loop until the user closes the window
    while True:
        # Read the user input from the GUI
        event, values = window.read(timeout=1000)
        
        # Update the monitor
        led_color = "green" if led_color == "white" else "white"
        window["-LED-SPOT-"].Widget.itemconfig(led, fill=led_color)
        update_monitor(window, chambers, start_time)

        # If the user has selected "Cancel" or closed the window, then exit the
        # program
        if event in ('Cancel', 'Finish', None, sg.WIN_CLOSED):
            break   
        
        # If the user has selected Add Media to All Reservoirs, then add the media
        # specified by the user to all of the chambers
        elif event == 'Add Media to All Reservoirs':
            add_media_to_all_reservoirs(chambers)      
        
        # If the user has selected Change Media in All Reservoirs, then start changing
        # the media in all of the chambers
        elif event == 'Change Media in All Chambers':
            for i in range(8):
                if chambers[i]['is_in_use']:
                    update_monitor(window, chambers, start_time)
                    change_media_in_single_reservoir(window, chambers, i)

        elif event in [f"-CHAMBER{i}-ADDMEDIA-" for i in range(1, 9)]:
            add_media_to_single_reservoir(chambers, int(event[8]) - 1)

        elif event in [f"-CHAMBER{i}-CHANGEMEDIA-" for i in range(1, 9)]:
            change_media_in_single_reservoir(window, chambers, int(event[8]) - 1)

    window.close()

def update_monitor(window, chambers, start_time):
    """Update the window with information from the chambers."""
    # Update the stuff
    window['-RUNTIME-'].update("System running for: " + humanize.naturaldelta(datetime.datetime.now() - start_time))
    for i in range(8):
        if chambers[i]['is_in_use']:
            window['-CHAMBER' + str(chambers[i]['chamber_id']) + '-LASTCHANGE-'].update("Last Change: " + humanize.naturaltime(datetime.datetime.now() - chambers[i]["last_changed"]))
            window['-CHAMBER' + str(chambers[i]['chamber_id']) + '-MEDIARES-'].update("Media in Reservoir: " + str(chambers[i]["media_in_chamber"]) + " mL")
    window.refresh()

def add_media_to_single_reservoir(chambers, chamber_id):
    """Add the media specified by the user to the specified chamber."""
    layout = [
        [sg.Text(text = "How much media did you add to Chamber " + str(chamber_id + 1) + "?", font='Roboto 20', pad=(0,20))],
        [sg.InputText(size=(3,2), font='Roboto 20', default_text='', key="-MEDIAVAL-"), sg.Text(text = "mL", font='Roboto 20')],
        [sg.Button("Submit", font='Roboto 15', pad=(5,20)), sg.Button("Clear Media", font='Roboto 15', pad=(5,20)), sg.Cancel(font='Roboto 15', pad=(5,20))],
        [sg.Text(text = "Note: include any volume of extra additives added to the media.", font='Roboto 10', pad=(0,20))]
    ]
    popup_window = sg.Window("Vessegen Bioreactor Software", layout, element_justification='center')

    # Read the user input from the GUI
    event, values = popup_window.read(timeout=100000)

    # If the user has selected "Cancel" or closed the window, then exit the
    # program
    if event in ('Cancel', 'Finish', None, sg.WIN_CLOSED):
        pass
    
    # If the user has selected Add Media to All Reservoirs, then add the media
    # specified by the user to all of the chambers
    elif event == 'Submit':
        # Get the user input and update the chamber information
        if values["-MEDIAVAL-"] != "":
            chambers[chamber_id]['media_in_chamber'] += int(values["-MEDIAVAL-"])

    elif event == 'Clear Media':
        chambers[chamber_id]['media_in_chamber'] = 0

    popup_window.close()

def add_media_to_all_reservoirs(chambers):
    """Add the media specified by the user to all chambers."""
    layout = [
        [sg.Text(text = "How much media did you add to all the Chambers?", font='Roboto 20', pad=(0,20))],
        [sg.InputText(size=(3,2), font='Roboto 20', default_text='', key="-MEDIAVAL-"), sg.Text(text = "mL", font='Roboto 20')],
        [sg.Button("Submit", font='Roboto 15', pad=(5,20)), sg.Button("Clear Media", font='Roboto 15', pad=(5,20)), sg.Cancel(font='Roboto 15', pad=(5,20))],
        [sg.Text(text = "Note: include any volume of extra additives added to the media.", font='Roboto 10', pad=(0,20))]
    ]
    popup_window = sg.Window("Vessegen Bioreactor Software", layout, element_justification='center')

    # Read the user input from the GUI
    event, values = popup_window.read(timeout=100000)

    # If the user has selected "Cancel" or closed the window, then exit the
    # program
    if event in ('Cancel', 'Finish', None, sg.WIN_CLOSED):
        pass
    
    # If the user has selected Add Media to All Reservoirs, then add the media
    # specified by the user to all of the chambers
    elif event == 'Submit':
        # Get the user input and update the chamber information
        if values["-MEDIAVAL-"]!= "":
            for i in range(8):
                if chambers[i]['is_in_use']:
                    chambers[i]['media_in_chamber'] += int(values["-MEDIAVAL-"])

    elif event == 'Clear Media':
        for i in range(8):
            if chambers[i]['is_in_use']:
                chambers[i]['media_in_chamber'] = 0

    popup_window.close()

def change_media_in_single_reservoir(window, chambers, chamber_id):
    """Change the media in the specified chamber."""
    if chambers[chamber_id]["media_in_chamber"] < 30:
        layout = [
            [sg.Text(text = "Are you sure there is enough media in Chamber " + str(chamber_id + 1) + "?", font='Roboto 20', pad=(0,20))],
            [sg.Text(text = "Note: if there is enough media, make sure the value recorded is accurate.", font='Roboto 15', pad=(0,20))],
            [sg.Button("OK", font='Roboto 15', pad=(5,20))]
        ]
        popup_window = sg.Window("Vessegen Bioreactor Software", layout, element_justification='center')

        # Read the user input from the GUI
        event, values = popup_window.read(timeout=10000)

        # If the user has selected "Cancel" or closed the window, then exit the
        # program
        if event in ('Cancel', 'Finish', None, 'OK', sg.WIN_CLOSED):
            pass

        popup_window.close()
    else:
        # Inform the user that we are removing media
        chambers[chamber_id]["status"] = "Removing media..."
        window["-CHAMBER" + str(chamber_id + 1) + "-STATUS-"].update("Status: " + chambers[chamber_id]["status"])
        window.refresh()

        # Send the signal to remove the media and wait
        GPIO.output(GPIO_PINS[chamber_id]["remove"], GPIO.HIGH)
        time.sleep(5)
        GPIO.output(GPIO_PINS[chamber_id]["remove"], GPIO.LOW)
        time.sleep(0.1)

        # Inform the user that we are adding media
        chambers[chamber_id]["status"] = "Adding media..."
        window["-CHAMBER" + str(chamber_id + 1) + "-STATUS-"].update("Status: " + chambers[chamber_id]["status"])
        window.refresh()

        # Calculate the time it will take to add the media, send the signal, and wait
        GPIO.output(GPIO_PINS[chamber_id]["add"], GPIO.HIGH)
        time_to_add_media = 5
        time.sleep(time_to_add_media)
        GPIO.output(GPIO_PINS[chamber_id]["add"], GPIO.LOW)
        time.sleep(0.1)

        # Inform the user that we are running, decrement the media removed
        chambers[chamber_id]["status"] = "Running"
        chambers[chamber_id]["last_changed"] = datetime.datetime.now()
        chambers[chamber_id]["media_in_chamber"] -= 30
        window["-CHAMBER" + str(chamber_id + 1) + "-STATUS-"].update("Status: " + chambers[chamber_id]["status"])
        window.refresh()

if __name__ == "__main__":
    main()
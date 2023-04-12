"""Get user input and run the bioreactor."""
import time
import datetime
import PySimpleGUI as sg
import humanize
import RPi.GPIO as GPIO  # pylint: disable=consider-using-from-import
import vessegen

# Initialize a structure to keep track of chambers
chambers = []
for n in range(8):
    chambers.append({
        "chamber_id": n + 1,
        "is_in_use": False,
        "last_changed": None,
        "media_in_chamber": 0,
        "status": "Unused"
    })

# Initialize a shutdown dictionary to control shutdown if desired
shutdown = {
    "main": False,
    "settings": False
}


def reset_chambers():
    """Reset the chambers if requested."""
    for chamber in chambers:
        chamber["is_in_use"] = False
        chamber["last_changed"] = None
        chamber["media_in_chamber"] = 0
        chamber["status"] = "Unused"


def get_user_settings():
    """Get the user input in a graphical format."""
    # Set the font and the theme of the GUI
    default_font = 'Roboto 20'
    sg.theme('LightGray1')

    # Define the layout of the starting window
    start_layout = [[sg.Text(text="Hello from Vessegen!", font='Roboto 40',
                             text_color='red', pad=((0, 0), (120, 20)))],
                    [sg.Text(text="Select 'Get Started' below to begin.",
                             font=default_font, pad=(0, 10))],
                    [sg.Button("Get Started", font=default_font),
                     sg.Button("Close", font=default_font)]]

    # Define the layout to allow the user to select the chambers that will be
    # in use
    chamber_layout = [[sg.Text(text="Which chambers will you be using?",
                               font='Roboto 30', pad=((0, 0), (120, 20)))],
                      [sg.Checkbox('Select All', default=False,
                                   font=default_font, key='selectallchamber',
                                   enable_events=True)],
                      [sg.Checkbox('Chamber 1', default=False,
                                   font=default_font, key='chamber1',
                                   enable_events=True),
                       sg.Checkbox('Chamber 2', default=False,
                                   font=default_font, key='chamber2',
                                   enable_events=True)],
                      [sg.Checkbox('Chamber 3', default=False,
                                   font=default_font, key='chamber3',
                                   enable_events=True),
                       sg.Checkbox('Chamber 4', default=False,
                                   font=default_font, key='chamber4',
                                   enable_events=True)],
                      [sg.Checkbox('Chamber 5', default=False,
                                   font=default_font, key='chamber5',
                                   enable_events=True),
                       sg.Checkbox('Chamber 6', default=False,
                                   font=default_font, key='chamber6',
                                   enable_events=True)],
                      [sg.Checkbox('Chamber 7', default=False,
                                   font=default_font, key='chamber7',
                                   enable_events=True),
                       sg.Checkbox('Chamber 8', default=False,
                                   font=default_font, key='chamber8',
                                   enable_events=True)],
                      [sg.Button("Submit Chambers", font=default_font,
                                 pad=(5, 20)),
                       sg.Cancel(font=default_font, pad=(5, 20),
                                 key='Cancel1')]]

    # Currently unused, but allows the user to assign subsettings for each
    # chamber. Because we are just going to allow the user to click a button to
    # change the media, we don't need this functionality.
    # same_settings_layout = [[sg.Text(text="Will the chambers be using the\
    #                                  same settings?", font='Roboto 30',
    #                                  pad=((0, 0),(60, 20)))],
    #                   [sg.Radio('Yes', 'samesettings', key='samesettingsyes',
    #                             font=default_font, default=False)],
    #                             [sg.Radio('No', 'samesettings',
    #                                       font=default_font, default=False)],
    #                   [sg.Button("Next", font=default_font, pad=(5,20),
    #                              key='samesettingsnext'),
    #                              sg.Cancel(font=default_font, pad=(5,20),
    #                                        key='Cancel2')]]

    # Allows the user to specify how long the experiment will run
    # same_settings_time = [[sg.Text(text="How long should the experiment \
    #                                run for?", font='Roboto 30', pad=(0,20))],
    #                       [sg.InputText(size=(2,2), font=default_font,
    #                                       default_text='0'),
    #                       sg.Text(text="weeks,", font=default_font),
    #                       sg.InputText(size=(2,2), font=default_font,
    #                                       default_text='0'),
    #                       sg.Text(text="days,", font=default_font),
    #                       sg.InputText(size=(2,2), font=default_font,
    #                                       default_text='0'),
    #                       sg.Text(text="hours", font=default_font)],
    #                      [sg.Button("Next", font=default_font, pad=(5,20),
    #                                 key='samesettingstimenext'),
    #                       sg.Cancel(font=default_font, pad=(5,20),
    #                                 key='Cancel3')]]

    # If we were doing automated media changes, this would allow the user to
    # specify the time between media changes for each chamber.
    # same_settings_media = [[sg.Text(text="How much time should there be \
    #                                 between media changes?",font='Roboto 30',
    #                                 pad=(0,20))],
    #                        [sg.InputText(size=(2,2), font=default_font,
    #                                        default_text='0'),
    #                         sg.Text(text="days,", font=default_font),
    #                         sg.InputText(size=(2,2), font=default_font,
    #                                      default_text='0'),
    #                         sg.Text(text="hours", font=default_font)],
    #                        [sg.Button("Next", font=default_font, pad=(5,20),
    #                                   key='samesettingsmedianext'),
    #                         sg.Cancel(font=default_font, pad=(5,20),
    #                                   key='Cancel4')]]

    # Put the various layouts into a list so we can call them
    layout = [[sg.Column(start_layout, key='-STARTCOL-',
                         element_justification='center'),
               sg.Column(chamber_layout, visible=False, key='-CHAMBERCOL-',
                         element_justification='center')]]

    # Initialize the window
    window = sg.Window("Vessegen Bioreactor Software", layout,
                       element_justification='center', size=(1024, 595),
                       icon=vessegen.ICON_PATH)

    # Start in the starting window column
    current_layout = '-STARTCOL-'

    # Loop until the user closes the window (or submits the settings)
    while True:
        # Read the user input from the GUI
        event, values = window.read()

        # If the user has selected "Cancel" or closed the window, then exit the
        # program
        if event in ('Cancel1', 'Cancel2', 'Cancel3'):
            shutdown["settings"] = True
            break
        if event in ('Close', None, sg.WIN_CLOSED):
            shutdown["main"] = True
            shutdown["settings"] = True
            break

        # If the user has selected Get Started, then take them to where they
        # can select the chambers
        if event == 'Get Started':
            window[current_layout].update(visible=False)
            current_layout = '-CHAMBERCOL-'
            window[current_layout].update(visible=True)

        # If the user has selected "Select All", then select all the chambers
        elif (event == 'selectallchamber' and
              values['selectallchamber']):
            window['chamber1'].update(True)
            window['chamber2'].update(True)
            window['chamber3'].update(True)
            window['chamber4'].update(True)
            window['chamber5'].update(True)
            window['chamber6'].update(True)
            window['chamber7'].update(True)
            window['chamber8'].update(True)
            for j in range(8):
                chambers[j]["is_in_use"] = True
                chambers[j]["status"] = "Running"

        # If the user unselected "Select All", then deselect all the chambers
        elif (event == 'selectallchamber' and
              not values['selectallchamber']):
            window['chamber1'].update(False)
            window['chamber2'].update(False)
            window['chamber3'].update(False)
            window['chamber4'].update(False)
            window['chamber5'].update(False)
            window['chamber6'].update(False)
            window['chamber7'].update(False)
            window['chamber8'].update(False)
            for j in range(8):
                chambers[j]["is_in_use"] = False
                chambers[j]["status"] = "Unused"

        # If the user has selected a chamber, then set it as in use
        elif event in ('chamber1', 'chamber2', 'chamber3', 'chamber4',
                       'chamber5', 'chamber6', 'chamber7', 'chamber8'):
            if values['selectallchamber']:
                window['selectallchamber'].update(False)
            chambers[int(event[7]) - 1]["is_in_use"] =\
                not chambers[int(event[7]) - 1]["is_in_use"]
            chambers[int(event[7]) - 1]["status"] = "Running" if\
                chambers[int(event[7]) - 1]["is_in_use"] else "Unused"

        # If the user submits their chamber selection, then move to the
        # monitoring page
        elif event == 'Submit Chambers':
            break

    window.close()


def start_monitoring_window(start_time):
    """Display information for the chambers and allow user control."""
    # Set the font and the theme of the GUI
    default_font = 'Roboto 12'
    sg.theme('LightGray1')

    # Define the layout of the monitoring window, however this must be done
    # after the settings have been defined.
    chamber_frames = []
    row1 = []
    row2 = []
    for i in range(4):
        if chambers[i]['is_in_use']:
            row1.append(sg.Frame("Chamber " + str(chambers[i]['chamber_id']),
                        [[sg.Text(text="Status: " + chambers[i]["status"],
                                  font='Roboto 12', key='-CHAMBER' +
                                  str(chambers[i]['chamber_id']) +
                                  '-STATUS-')],
                         [sg.Text(text="Last Changed: " +
                                  humanize.naturaltime(
                                    datetime.datetime.now() - chambers[i]
                                    ["last_changed"]),
                                  font='Roboto 12', key='-CHAMBER' +
                                  str(chambers[i]['chamber_id']) +
                                  '-LASTCHANGE-')],
                         [sg.Text(text="Media in Reservoir: " +
                                  str(chambers[i]["media_in_chamber"]) +
                                  " mL", font='Roboto 12', key='-CHAMBER' +
                                  str(chambers[i]['chamber_id']) +
                                  '-MEDIARES-')],
                         [sg.Button("Add Media to Reservoir",
                                    font=default_font, key='-CHAMBER' +
                                    str(chambers[i]['chamber_id']) +
                                    '-ADDMEDIA-')],
                         [sg.Button("Change Media", font=default_font,
                                    key='-CHAMBER' +
                                    str(chambers[i]['chamber_id']) +
                                    '-CHANGEMEDIA-')]], font='Roboto 20',
                                 element_justification='center',
                                 title_color="red", size=(240, 200)))
        else:
            row1.append(sg.Frame("Chamber " + str(chambers[i]['chamber_id']),
                                 [[sg.Text(text="Status: " +
                                           chambers[i]["status"],
                                           font='Roboto 12', key='-CHAMBER' +
                                           str(chambers[i]['chamber_id']) +
                                           '-STATUS-')]], font='Roboto 20',
                                 element_justification='center',
                                 title_color="red", size=(240, 200)))
        if chambers[i]['is_in_use']:
            row2.append(sg.Frame("Chamber " + str(chambers[i]['chamber_id']),
                                 [[sg.Text(text="Status: " +
                                           chambers[i]["status"],
                                           font='Roboto 12', key='-CHAMBER' +
                                           str(chambers[i]['chamber_id']) +
                                           '-STATUS-')],
                                  [sg.Text(text="Last Change: " +
                                           humanize.naturaltime(
                                            datetime.datetime.now() -
                                            chambers[i]["last_changed"]),
                                           font='Roboto 12', key='-CHAMBER' +
                                           str(chambers[i]['chamber_id']) +
                                           '-LASTCHANGE-')],
                                  [sg.Text(text="Media in Reservoir: " +
                                           str(chambers[i]["media_in_chamber"])
                                           + " mL", font='Roboto 12',
                                           key='-CHAMBER' +
                                           str(chambers[i]['chamber_id']) +
                                           '-MEDIARES-')],
                                  [sg.Button("Add Media to Reservoir",
                                             font=default_font, key='-CHAMBER'
                                             + str(chambers[i]["chamber_id"]) +
                                             '-ADDMEDIA-')],
                                  [sg.Button("Change Media", font=default_font,
                                             key='-CHAMBER' +
                                             str(chambers[i]["chamber_id"]) +
                                             '-CHANGEMEDIA-')]],
                                 font='Roboto 20',
                                 element_justification='center',
                                 title_color="red", size=(240, 200)))
        else:
            row2.append(sg.Frame("Chamber " + str(chambers[i]['chamber_id']),
                                 [[sg.Text(text="Status: " +
                                           chambers[i]["status"],
                                           font='Roboto 12', key='-CHAMBER' +
                                           str(chambers[i]['chamber_id']) +
                                           '-STATUS-')]], font='Roboto 20',
                                 element_justification='center',
                                 title_color="red", size=(240, 200)))
    chamber_frames.append(row1)
    chamber_frames.append(row2)

    # Create a small little running indicator
    led_spot = sg.Graph((20, 20), (0, 0), (20, 20), key="-LED-SPOT-",
                        enable_events=True)

    # Define the layout of the window
    layout = [
        [sg.Text(text="System Status and Control", font='Roboto 30',
                 pad=(0, 5))], chamber_frames,
        [led_spot, sg.Text(text="System running for: " +
                           humanize.naturaldelta(datetime.datetime.now() -
                                                 start_time),
                           font='Roboto 18', pad=(0, 5), key='-RUNTIME-')],
        [sg.Button("Add Media to All Reservoirs", font='Roboto 15',
                   pad=(5, 5)),
         sg.Button("Change Media in All Chambers", font='Roboto 15',
                   pad=(5, 5)),
         sg.Button("Finish", font='Roboto 15', pad=(5, 5))]
    ]

    # Initialize the window
    window = sg.Window("Vessegen Bioreactor Software", layout,
                       element_justification='center', size=(1024, 595),
                       finalize=True, icon=vessegen.ICON_PATH)

    # Draw the LED
    led = led_spot.draw_circle((10, 10), 9, fill_color='white',
                               line_color="black", line_width=1)
    led_color = "white"

    # Loop until the user closes the window
    while True:
        # Read the user input from the GUI
        event, _ = window.read(timeout=1000)

        # Update the monitor
        led_color = "green" if led_color == "white" else "white"
        window["-LED-SPOT-"].Widget.itemconfig(led, fill=led_color)
        update_monitor(window, start_time)

        # If the user has selected "Cancel" or closed the window, then exit the
        # program
        if event in ('Cancel', 'Finish', None, sg.WIN_CLOSED):
            break

        # If the user has selected Add Media to All Reservoirs, then add the
        # media specified by the user to all of the chambers
        if event == 'Add Media to All Reservoirs':
            add_media_to_all_reservoirs(led, led_color, window, start_time)

        # If the user has selected Change Media in All Reservoirs, then start
        # changing the media in all of the chambers
        elif event == 'Change Media in All Chambers':
            change_media_in_all_chambers(led, led_color, start_time, window)

        elif event in [f"-CHAMBER{i}-ADDMEDIA-" for i in range(1, 9)]:
            add_media_to_single_reservoir(int(event[8]) - 1, led, led_color,
                                          window, start_time)

        elif event in [f"-CHAMBER{i}-CHANGEMEDIA-" for i in range(1, 9)]:
            change_media_in_single_chamber(led, led_color, start_time, window,
                                           int(event[8]) - 1)

    window.close()


def update_monitor(window, start_time):
    """Update the window with information from the chambers."""
    # Update the stuff
    window['-RUNTIME-'].update("System running for: " +
                               humanize.naturaldelta(datetime.datetime.now() -
                                                     start_time))
    for i in range(8):
        if chambers[i]['is_in_use']:
            window['-CHAMBER' + str(chambers[i]['chamber_id']) +
                   '-LASTCHANGE-'].update("Last Change: " +
                                          humanize.naturaltime(
                                           datetime.datetime.now() -
                                           chambers[i]["last_changed"]))
            window['-CHAMBER' + str(chambers[i]['chamber_id']) +
                   '-MEDIARES-'].update("Media in Reservoir: " +
                                        str(round(
                                            chambers[i]["media_in_chamber"],
                                            1)) + " mL")
    window.refresh()


def add_media_to_single_reservoir(chamber_id, led, led_color, window,
                                  start_time):
    """Add the media specified by the user to the specified chamber."""
    layout = [
        [sg.Text(text="How much media did you add to Chamber " +
                 str(chamber_id + 1) + "?", font='Roboto 20', pad=(0, 20))],
        [sg.Text(text="0", key="-MEDIAVAL-", font='Roboto 20', pad=(0, 20)),
         sg.Text(text=" mL", font='Roboto 20', pad=(0, 20))],
        [sg.Button("-0.1", font='Roboto 15', pad=(5, 5)),
         sg.Button("+0.1", font='Roboto 15', pad=(5, 5))],
        [sg.Button("-1", font='Roboto 15', pad=(5, 5)),
         sg.Button("+1", font='Roboto 15', pad=(5, 5))],
        [sg.Button("-5", font='Roboto 15', pad=(5, 5)),
         sg.Button("+5", font='Roboto 15', pad=(5, 5))],
        [sg.Button("-10", font='Roboto 15', pad=(5, 5)),
         sg.Button("+10", font='Roboto 15', pad=(5, 5))],
        [sg.Button("Set to Zero", font='Roboto 15', pad=(5, 20)),
         sg.Button("Empty Resevoir", font='Roboto 15', pad=(5, 20)),
         sg.Button("Submit", font='Roboto 15', pad=(5, 20)),
         sg.Cancel(font='Roboto 15', pad=(5, 20))],
        [sg.Text(text="Note: include any volume of extra additives added \
                 to the media.", font='Roboto 10', pad=(0, 20))]
    ]
    popup_window = sg.Window("Vessegen Bioreactor Software", layout,
                             element_justification='center', finalize=True,
                             icon=vessegen.ICON_PATH)

    media_to_add = 0
    while True:
        if media_to_add == 0:
            media_to_add = round(media_to_add, 0)
            popup_window['-MEDIAVAL-'].update(str(media_to_add))
            popup_window.refresh()

        # Read the user input from the GUI
        event, _ = popup_window.read(timeout=1000)

        # Update the monitor
        led_color = "green" if led_color == "white" else "white"
        window["-LED-SPOT-"].Widget.itemconfig(led, fill=led_color)
        update_monitor(window, start_time)

        # If the user has selected "Cancel" or closed the window, then exit the
        # program
        if event in ('Cancel', 'Finish', None, sg.WIN_CLOSED):
            break

        # If the user clicks one of the buttons to add or remove media, keep
        # track of it
        if event in ('-0.1', '+0.1', '-1', '+1', '-5', '+5', '-10', '+10'):
            media_to_add = round(media_to_add + float(event), 1)
            popup_window['-MEDIAVAL-'].update(str(media_to_add))
            popup_window.refresh()

        # If the user has selected Add Media to All Reservoirs, then add the
        # media specified by the user to all of the chambers
        elif event == 'Submit':
            # Get the user input and update the chamber information
            chambers[chamber_id]['media_in_chamber'] += media_to_add

        if event == 'Set to Zero':
            media_to_add = 0
            popup_window['-MEDIAVAL-'].update(str(media_to_add))
            popup_window.refresh()

        elif event == 'Empty Resevoir':
            chambers[chamber_id]['media_in_chamber'] = 0
            break

    popup_window.close()


def add_media_to_all_reservoirs(led, led_color, window, start_time):
    """Add the media specified by the user to all chambers."""
    layout = [
        [sg.Text(text="How much media did you add to all the Chambers?",
                 font='Roboto 20', pad=(0, 20))],
        [sg.Text(text="0", key="-MEDIAVAL-", font='Roboto 20', pad=(0, 20)),
         sg.Text(text=" mL", font='Roboto 20', pad=(0, 20))],
        [sg.Button("-0.1", font='Roboto 15', pad=(5, 5)),
         sg.Button("+0.1", font='Roboto 15', pad=(5, 5))],
        [sg.Button("-1", font='Roboto 15', pad=(5, 5)),
         sg.Button("+1", font='Roboto 15', pad=(5, 5))],
        [sg.Button("-5", font='Roboto 15', pad=(5, 5)),
         sg.Button("+5", font='Roboto 15', pad=(5, 5))],
        [sg.Button("-10", font='Roboto 15', pad=(5, 5)),
         sg.Button("+10", font='Roboto 15', pad=(5, 5))],
        [sg.Button("Set to Zero", font='Roboto 15', pad=(5, 20)),
         sg.Button("Empty Resevoir", font='Roboto 15', pad=(5, 20)),
         sg.Button("Submit", font='Roboto 15', pad=(5, 20)),
         sg.Cancel(font='Roboto 15', pad=(5, 20))],
        [sg.Text(text="Note: include any volume of extra additives \
                 added to the media.", font='Roboto 10', pad=(0, 20))]
    ]
    popup_window = sg.Window("Vessegen Bioreactor Software", layout,
                             element_justification='center', finalize=True,
                             icon=vessegen.ICON_PATH)

    media_to_add = 0
    while True:
        if media_to_add == 0:
            media_to_add = round(media_to_add, 0)
            popup_window['-MEDIAVAL-'].update(str(media_to_add))
            popup_window.refresh()

        # Read the user input from the GUI
        event, _ = popup_window.read(timeout=1000)

        # Update the monitor
        led_color = "green" if led_color == "white" else "white"
        window["-LED-SPOT-"].Widget.itemconfig(led, fill=led_color)
        update_monitor(window, start_time)

        # If the user has selected "Cancel" or closed the window, then exit the
        # program
        if event in ('Cancel', 'Finish', None, sg.WIN_CLOSED):
            break

        # If the user clicks one of the buttons to add or remove media, keep
        # track of it
        if event in ('-0.1', '+0.1', '-1', '+1', '-5', '+5', '-10', '+10'):
            media_to_add = round(media_to_add + float(event), 1)
            popup_window['-MEDIAVAL-'].update(str(media_to_add))
            popup_window.refresh()

        # If the user has selected Add Media to All Reservoirs, then add the
        # media specified by the user to all of the chambers
        elif event == 'Submit':
            # Get the user input and update the chamber information
            for chamber_id in range(8):
                if chambers[chamber_id]['status'] != 'Unused':
                    chambers[chamber_id]['media_in_chamber'] +=\
                        round(media_to_add, 1)
            break

        if event == 'Set to Zero':
            media_to_add = 0
            popup_window['-MEDIAVAL-'].update(str(media_to_add))
            popup_window.refresh()

        elif event == 'Empty Resevoir':
            for chamber_id in range(8):
                if chambers[chamber_id]['status'] != 'Unused':
                    chambers[chamber_id]['media_in_chamber'] = 0
            break

    popup_window.close()


def change_media_in_single_chamber(led, led_color, start_time, window,
                                   chamber_id):
    """Change the media in the specified chamber."""
    if chambers[chamber_id]["media_in_chamber"] < 30:
        layout = [
            [sg.Text(text="Are you sure there is enough media in Chamber " +
                     str(chamber_id + 1) + "?", font='Roboto 20',
                     pad=(0, 20))],
            [sg.Text(text="Note: if there is enough media, make sure the \
                     value recorded is accurate.", font='Roboto 15',
                     pad=(0, 20))],
            [sg.Button("OK", font='Roboto 15', pad=(5, 20))]
        ]
        popup_window = sg.Window("Vessegen Bioreactor Software", layout,
                                 element_justification='center',
                                 finalize=True, icon=vessegen.ICON_PATH)

        while True:
            # Read the user input from the GUI
            event, _ = popup_window.read(timeout=1000)

            # Update the monitor
            led_color = "green" if led_color == "white" else "white"
            window["-LED-SPOT-"].Widget.itemconfig(led, fill=led_color)
            update_monitor(window, start_time)

            # If the user has selected "Cancel" or closed the window, then exit
            # the program
            if event in ('Cancel', 'Finish', None, 'OK', sg.WIN_CLOSED):
                pass

            popup_window.close()
    else:
        # Inform the user that we are removing media
        chambers[chamber_id]["status"] = "Removing media..."
        window["-CHAMBER" + str(chamber_id + 1) +
               "-STATUS-"].update("Status: " + chambers[chamber_id]["status"])
        window.refresh()

        # Send the signal to remove the media and wait
        time_to_remove_media = 5

        # pylint: disable=no-member
        GPIO.output(vessegen.GPIO_PINS[chamber_id]["remove"], GPIO.HIGH)

        for _ in range(int(time_to_remove_media)):
            led_color = "green" if led_color == "white" else "white"
            window["-LED-SPOT-"].Widget.itemconfig(led, fill=led_color)
            update_monitor(window, start_time)
            time.sleep(1)

        # pylint: disable=no-member
        GPIO.output(vessegen.GPIO_PINS[chamber_id]["remove"], GPIO.LOW)
        time.sleep(0.1)

        # Inform the user that we are adding media
        chambers[chamber_id]["status"] = "Adding media..."
        window["-CHAMBER" + str(chamber_id + 1) +
               "-STATUS-"].update("Status: " + chambers[chamber_id]["status"])
        window.refresh()

        # Calculate the time it will take to add the media, send the signal,
        # and wait
        time_to_add_media = 5

        # pylint: disable=no-member
        GPIO.output(vessegen.GPIO_PINS[chamber_id]["add"], GPIO.HIGH)

        for _ in range(int(time_to_add_media)):
            led_color = "green" if led_color == "white" else "white"
            window["-LED-SPOT-"].Widget.itemconfig(led, fill=led_color)
            update_monitor(window, start_time)
            time.sleep(1)

        # pylint: disable=no-member
        GPIO.output(vessegen.GPIO_PINS[chamber_id]["add"], GPIO.LOW)
        time.sleep(0.1)

        # Inform the user that we are running, decrement the media removed
        chambers[chamber_id]["status"] = "Running"
        chambers[chamber_id]["last_changed"] = datetime.datetime.now()
        chambers[chamber_id]["media_in_chamber"] =\
            round(chambers[chamber_id]["media_in_chamber"] - 30, 1)
        window["-CHAMBER" + str(chamber_id + 1) +
               "-STATUS-"].update("Status: " + chambers[chamber_id]["status"])
        window.refresh()


def change_media_in_all_chambers(led, led_color, start_time, window):
    """Change the media in all of the used chambers."""
    # For all of the chambers in use, change the media
    for i in range(8):
        if chambers[i]['is_in_use']:
            change_media_in_single_chamber(led,
                                           led_color, start_time, window, i)


def main():
    """Top level function."""
    while not shutdown['main']:
        # Reset the chambers
        reset_chambers()

        # Reset shutdown variable
        shutdown['settings'] = False

        # Load the GUI that can input the user settings
        get_user_settings()

        # If the user cancels, pass the current iteration
        if shutdown["settings"]:
            continue

        # Define a new start time and make the chambers time accurate
        start_time = datetime.datetime.now()
        for i in range(8):
            chambers[i]["last_changed"] = datetime.datetime.now()

        # Get the monitoring window
        start_monitoring_window(start_time)


if __name__ == "__main__":
    main()

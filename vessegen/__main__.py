"""Get user input and run the bioreactor."""
import time
import datetime
import PySimpleGUI as sg
import humanize
import atexit
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
    "settings": False,
}


def reset_chambers():
    """Reset the chambers if requested.

    This is useful since the software is set up to run on a loop until told to
    stop, meaning there may be multiple trials run in between stopping the
    software. Thus, the chambers need to be reset in between trials.
    """
    for chamber in chambers:
        chamber["is_in_use"] = False
        chamber["last_changed"] = None
        chamber["media_in_chamber"] = 0
        chamber["status"] = "Unused"
        GPIO.output(vessegen.GPIO_PINS[chamber["chamber_id"] - 1]["remove"],
                    GPIO.LOW)
        GPIO.output(vessegen.GPIO_PINS[chamber["chamber_id"] - 1]["add"],
                    GPIO.LOW)


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
    # in use. Really, this just makes a bunch of checkboxes.
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

        # If the user selects close from the start page or closes the window,
        # exit the entire program
        if event in ('Close', None, sg.WIN_CLOSED):
            shutdown["main"] = True
            shutdown["settings"] = True
            break

        # If the user has selected one of the subwindow cancel buttons, send
        # them back to the starting screen
        if event in ('Cancel1', 'Cancel2', 'Cancel3'):
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
            # Update all the checkboxes in the window
            window['chamber1'].update(True)
            window['chamber2'].update(True)
            window['chamber3'].update(True)
            window['chamber4'].update(True)
            window['chamber5'].update(True)
            window['chamber6'].update(True)
            window['chamber7'].update(True)
            window['chamber8'].update(True)

            # Update the data structure containing information on the chambers
            for j in range(8):
                chambers[j]["is_in_use"] = True
                chambers[j]["status"] = "Running"

        # If the user unselected "Select All", then deselect all the chambers
        elif (event == 'selectallchamber' and
              not values['selectallchamber']):
            # Update all the checkboxes in the window
            window['chamber1'].update(False)
            window['chamber2'].update(False)
            window['chamber3'].update(False)
            window['chamber4'].update(False)
            window['chamber5'].update(False)
            window['chamber6'].update(False)
            window['chamber7'].update(False)
            window['chamber8'].update(False)

            # Update the data structure containing information on the chambers
            for j in range(8):
                chambers[j]["is_in_use"] = False
                chambers[j]["status"] = "Unused"

        # If the user has selected a single chamber, then set it as in use if
        # it wasn't and as unused if it was in use
        elif event in ('chamber1', 'chamber2', 'chamber3', 'chamber4',
                       'chamber5', 'chamber6', 'chamber7', 'chamber8'):
            # See if the select all box was checked, unchecking it if so
            if values['selectallchamber']:
                window['selectallchamber'].update(False)

            # Set the chamber to the opposite of is_in_use as it was
            chambers[int(event[7]) - 1]["is_in_use"] =\
                not chambers[int(event[7]) - 1]["is_in_use"]

            # Make sure the status correlates to its is_in_use (this is just
            # a "fancy" one line if else statement)
            chambers[int(event[7]) - 1]["status"] = "Running" if\
                chambers[int(event[7]) - 1]["is_in_use"] else "Unused"

        # If the user submits their chamber selection, then move to the
        # monitoring page
        elif event == 'Submit Chambers':
            break

    # Close the window
    window.close()


def start_monitoring_window(start_time):
    """Display information for the chambers and allow user control."""
    # Set the font and the theme of the GUI
    default_font = 'Roboto 12'
    sg.theme('LightGray1')

    # Define the layout of the monitoring window, however this must be done
    # after the settings have been defined.
    chamber_frames = []

    # The monitoring window has two rows, the top row has 1, 3, 5, 7 and the
    # bottom has 2, 4, 6, 8. Go through and see which chambers are in use.
    # If a chamber is in use, then add a GUI element to its row. If it isn't in
    # use, then add a GUI element that says it isn't in use to its row.
    row1 = []
    row2 = []
    for i in range(0, 8, 2):
        j = i + 1
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
        if chambers[j]['is_in_use']:
            row2.append(sg.Frame("Chamber " + str(chambers[j]['chamber_id']),
                                 [[sg.Text(text="Status: " +
                                           chambers[j]["status"],
                                           font='Roboto 12', key='-CHAMBER' +
                                           str(chambers[j]['chamber_id']) +
                                           '-STATUS-')],
                                  [sg.Text(text="Last Change: " +
                                           humanize.naturaltime(
                                            datetime.datetime.now() -
                                            chambers[j]["last_changed"]),
                                           font='Roboto 12', key='-CHAMBER' +
                                           str(chambers[j]['chamber_id']) +
                                           '-LASTCHANGE-')],
                                  [sg.Text(text="Media in Reservoir: " +
                                           str(chambers[j]["media_in_chamber"])
                                           + " mL", font='Roboto 12',
                                           key='-CHAMBER' +
                                           str(chambers[j]['chamber_id']) +
                                           '-MEDIARES-')],
                                  [sg.Button("Add Media to Reservoir",
                                             font=default_font, key='-CHAMBER'
                                             + str(chambers[j]["chamber_id"]) +
                                             '-ADDMEDIA-')],
                                  [sg.Button("Change Media", font=default_font,
                                             key='-CHAMBER' +
                                             str(chambers[j]["chamber_id"]) +
                                             '-CHANGEMEDIA-')]],
                                 font='Roboto 20',
                                 element_justification='center',
                                 title_color="red", size=(240, 200)))
        else:
            row2.append(sg.Frame("Chamber " + str(chambers[j]['chamber_id']),
                                 [[sg.Text(text="Status: " +
                                           chambers[j]["status"],
                                           font='Roboto 12', key='-CHAMBER' +
                                           str(chambers[j]['chamber_id']) +
                                           '-STATUS-')]], font='Roboto 20',
                                 element_justification='center',
                                 title_color="red", size=(240, 200)))

    # Then, just add the two rows to the overall structure
    chamber_frames.append(row1)
    chamber_frames.append(row2)

    # Create a small spot for a little running blinking indicator
    led_spot = sg.Graph((20, 20), (0, 0), (20, 20), key="-LED-SPOT-",
                        enable_events=True)

    # Define the layout of the window
    layout = [
        [sg.Text(text="System Status and Control", font='Roboto 30',
                 pad=(0, 5))],
        chamber_frames,
        [led_spot, sg.Text(text="System running for: " +
                           humanize.naturaldelta(datetime.datetime.now() -
                                                 start_time),
                           font='Roboto 18', pad=(0, 5), key='-RUNTIME-')],
        [sg.Button("Add Media to All Reservoirs", font='Roboto 15',
                   pad=(5, 5)),
         sg.Button("Change Media in All Chambers", font='Roboto 15',
                   pad=(5, 5)),
         sg.Button("Finish", font='Roboto 15', pad=(5, 5))]]

    # Initialize the window
    window = sg.Window("Vessegen Bioreactor Software", layout,
                       element_justification='center', size=(1024, 595),
                       finalize=True, icon=vessegen.ICON_PATH)

    # Draw the LED blinking indicator, storing it as a dictionary to keep track
    # of it and its color
    led = {
        "obj": led_spot.draw_circle((10, 10), 9, fill_color='white',
                                    line_color="black", line_width=1),
        "color": "white",
        "last_updated": time.time()
    }

    # Loop until the user closes the window
    while True:
        # Read the user input from the GUI
        event, _ = window.read(timeout=100)

        # First, the monitor should check if it needs to update itself
        update_monitor(window, led, start_time)

        # If the user has selected "Cancel", "Finished", orclosed the window,
        # then exit the program
        if event in ('Cancel', 'Finish', None, sg.WIN_CLOSED):
            break

        # If the user has selected to add media to all reservoirs, then add the
        # media specified by the user to all of the chambers
        if event == 'Add Media to All Reservoirs':
            add_media_to_all_reservoirs(window, led, start_time)

        # If the user has selected to add media to a single reservoir, then add
        # the media specified to that single chamber
        elif event in [f"-CHAMBER{i}-ADDMEDIA-" for i in range(1, 9)]:
            add_media_to_single_reservoir(int(event[8]) - 1,
                                          window, led, start_time)

        # If the user has selected to change media in all chambers, then start
        # changing the media in all of the chambers
        elif event == 'Change Media in All Chambers':
            change_media_in_all_chambers(window, led, start_time)

        # If the user has selected change media in a single chamber, then start
        # changing the media in that chamber
        elif event in [f"-CHAMBER{i}-CHANGEMEDIA-" for i in range(1, 9)]:
            change_media_in_single_chamber(int(event[8]) - 1,
                                           window, led, start_time)

    # Once appropriate, close the window
    window.close()


def update_monitor(window, led, start_time):
    """Update the window with information from the chambers."""
    if time.time() > led["last_updated"] + 1:
        # Blink the LED
        led["color"] = "green" if led["color"] == "white" else "white"
        window["-LED-SPOT-"].Widget.itemconfig(led["obj"], fill=led["color"])

        # Update the text shown on the window
        window['-RUNTIME-'].update("System running for: " +
                                   humanize.naturaldelta(datetime.
                                                         datetime.now() -
                                                         start_time))
        for i in range(8):
            if chambers[i]['is_in_use']:
                window["-CHAMBER" + str(chambers[i]["chamber_id"]) +
                       "-STATUS-"].update("Status: " + chambers[i]["status"])
                window['-CHAMBER' + str(chambers[i]['chamber_id']) +
                       '-LASTCHANGE-'].update("Last Change: " +
                                              humanize.naturaltime(
                                                datetime.datetime.now() -
                                                chambers[i]["last_changed"]))
                window['-CHAMBER' + str(chambers[i]['chamber_id']) +
                       '-MEDIARES-'].update("Media in Reservoir: " +
                                            str(round(
                                                chambers[i]
                                                ["media_in_chamber"],
                                                1)) + " mL")
        window.refresh()
        led["last_updated"] = time.time()


def add_media_to_single_reservoir(chamber_id, window, led, start_time):
    """Add the media specified by the user to the specified reservoir.

    Note, this function takes in the led indicator information as well as the
    parent window so that it can keep updating the parent window while it
    waits for the user to be finished with this screen.
    """
    # Specify the layout for prompting the user for the media to add, including
    # built in buttons
    layout = [
        [sg.Text(text="How much media did you add to reservoir " +
                 str(chamber_id + 1) + "?", font='Roboto 20', pad=(0, 20))],
        [sg.Text(text="0", key="-MEDIAVAL-", font='Roboto 20', pad=(0, 20)),
         sg.Text(text=" mL", font='Roboto 20', pad=(0, 20))],
        [sg.Button("-0.1", button_color='DarkRed', font='Roboto 15', pad=(5, 5)),
         sg.Button("+0.1", button_color='DarkRed', font='Roboto 15', pad=(5, 5))],
        [sg.Button("-1", button_color='DarkRed', font='Roboto 15', pad=(5, 5)),
         sg.Button("+1", button_color='DarkRed', font='Roboto 15', pad=(5, 5))],
        [sg.Button("-5", button_color='DarkRed', font='Roboto 15', pad=(5, 5)),
         sg.Button("+5", button_color='DarkRed', font='Roboto 15', pad=(5, 5))],
        [sg.Button("-10", button_color='DarkRed', font='Roboto 15', pad=(5, 5)),
         sg.Button("+10", button_color='DarkRed', font='Roboto 15', pad=(5, 5))],
        [sg.Button("Set to Zero", font='Roboto 15', pad=(5, 20)),
         sg.Button("Empty Resevoir", font='Roboto 15', pad=(5, 20)),
         sg.Button("Submit", font='Roboto 15', pad=(5, 20)),
         sg.Cancel(font='Roboto 15', pad=(5, 20))],
        [sg.Text(text="Note: include any volume of extra additives added " +
                 "to the media.", font='Roboto 10', pad=(0, 20))]
    ]

    # Start the "popup" window
    popup_window = sg.Window("Vessegen Bioreactor Software", layout,
                             element_justification='center', finalize=True,
                             icon=vessegen.ICON_PATH)

    # Initially, the media to add is zero
    media_to_add = 0
    while True:
        # Check if the media is 0.0, and if so round it to zero decimal places.
        # This is just for formatting.
        if media_to_add == 0.0:
            media_to_add = round(media_to_add, 0)
            popup_window['-MEDIAVAL-'].update(str(media_to_add))
            popup_window.refresh()

        # Read the user input from the GUI
        event, _ = popup_window.read(timeout=100)

        # First, the monitor should check if it needs to update itself
        update_monitor(window, led, start_time)

        # If the user has selected "Cancel" or closed the window, then exit the
        # popup window
        if event in ('Cancel', 'Finish', None, sg.WIN_CLOSED):
            break

        # If the user clicks one of the buttons to add or remove media, keep
        # track of it
        if event in ('-0.1', '+0.1', '-1', '+1', '-5', '+5', '-10', '+10'):
            media_to_add = round(media_to_add + float(event), 1)
            popup_window['-MEDIAVAL-'].update(str(media_to_add))
            popup_window.refresh()

        # Once the user submits, add the media to the correct reservoir and
        # update the chamber information
        elif event == 'Submit':
            chambers[chamber_id]['media_in_chamber'] =\
                max(media_to_add + chambers[chamber_id]['media_in_chamber'], 0)
            break

        # If the user wishes to reset the counter and display, do so
        if event == 'Set to Zero':
            media_to_add = 0
            popup_window['-MEDIAVAL-'].update(str(media_to_add))
            popup_window.refresh()

        # If the user would like to empty that specific reservoir, do so
        elif event == 'Empty Resevoir':
            chambers[chamber_id]['media_in_chamber'] = 0
            break

    # Once done, close the popup window
    popup_window.close()


def add_media_to_all_reservoirs(window, led, start_time):
    """Add the media specified by the user to all reservoirs.

    Note, this function takes in the led indicator information as well as the
    parent window so that it can keep updating the parent window while it
    waits for the user to be finished with this screen.
    """
    # Specify the layout for prompting the user for the media to add, including
    # built in buttons
    layout = [
        [sg.Text(text="How much media did you add to all the reservoirs?",
                 font='Roboto 20', pad=(0, 20))],
        [sg.Text(text="0", key="-MEDIAVAL-", font='Roboto 20', pad=(0, 20)),
         sg.Text(text=" mL", font='Roboto 20', pad=(0, 20))],
        [sg.Button("-0.1", button_color='DarkRed', font='Roboto 15', pad=(5, 5)),
         sg.Button("+0.1", button_color='DarkRed', font='Roboto 15', pad=(5, 5))],
        [sg.Button("-1", button_color='DarkRed', font='Roboto 15', pad=(5, 5)),
         sg.Button("+1", button_color='DarkRed', font='Roboto 15', pad=(5, 5))],
        [sg.Button("-5", button_color='DarkRed', font='Roboto 15', pad=(5, 5)),
         sg.Button("+5", button_color='DarkRed', font='Roboto 15', pad=(5, 5))],
        [sg.Button("-10", button_color='DarkRed', font='Roboto 15', pad=(5, 5)),
         sg.Button("+10", button_color='DarkRed', font='Roboto 15', pad=(5, 5))],
        [sg.Button("Set to Zero", font='Roboto 15', pad=(5, 20)),
         sg.Button("Empty Resevoir", font='Roboto 15', pad=(5, 20)),
         sg.Button("Submit", font='Roboto 15', pad=(5, 20)),
         sg.Cancel(font='Roboto 15', pad=(5, 20))],
        [sg.Text(text="Note: include any volume of extra additives " +
                 "added to the media.", font='Roboto 10', pad=(0, 20))]
    ]

    # Launch the "popup" window
    popup_window = sg.Window("Vessegen Bioreactor Software", layout,
                             element_justification='center', finalize=True,
                             icon=vessegen.ICON_PATH)

    # Initially, the media to add is zero
    media_to_add = 0
    while True:
        # Check if the media is 0.0, and if so round it to zero decimal places.
        # This is just for formatting.
        if media_to_add == 0:
            media_to_add = round(media_to_add, 0)
            popup_window['-MEDIAVAL-'].update(str(media_to_add))
            popup_window.refresh()

        # Read the user input from the GUI
        event, _ = popup_window.read(timeout=100)

        # First, the monitor should check if it needs to update itself
        update_monitor(window, led, start_time)

        # If the user has selected "Cancel" or closed the window, then exit the
        # popup window
        if event in ('Cancel', 'Finish', None, sg.WIN_CLOSED):
            break

        # If the user clicks one of the buttons to add or remove media, keep
        # track of it
        if event in ('-0.1', '+0.1', '-1', '+1', '-5', '+5', '-10', '+10'):
            media_to_add = round(media_to_add + float(event), 1)
            popup_window['-MEDIAVAL-'].update(str(media_to_add))
            popup_window.refresh()

        # If the user submits, then add the media to all of the reservoirs
        # for the chambers that are in use
        elif event == 'Submit':
            # Get the user input and update the chamber information
            for chamber_id in range(8):
                if chambers[chamber_id]['status'] != 'Unused':
                    chambers[chamber_id]['media_in_chamber'] =\
                        max(media_to_add + chambers[chamber_id]
                            ['media_in_chamber'], 0)
            break

        # If the user wishes to reset the counter and display, do so
        if event == 'Set to Zero':
            media_to_add = 0
            popup_window['-MEDIAVAL-'].update(str(media_to_add))
            popup_window.refresh()

        # If the user would like to empty all of the reservoirs, do so
        elif event == 'Empty Resevoir':
            for chamber_id in range(8):
                if chambers[chamber_id]['status'] != 'Unused':
                    chambers[chamber_id]['media_in_chamber'] = 0
            break

    # Close the popup window when the user is finished
    popup_window.close()


def change_media_in_single_chamber(chamber_id, window, led, start_time):
    """Change the media in the specified chamber.

    Note, this function takes in the led indicator information as well as the
    parent window so that it can keep updating the parent window while it
    waits for the user to be finished with this screen.
    """
    # First, make sure that we think there is enough media to complete a media
    # change
    if chambers[chamber_id]["media_in_chamber"] < vessegen.MEDIA_VOL:
        layout = [
            [sg.Text(text="Are you sure there is enough media in Reservoir " +
                     str(chamber_id + 1) + "?", font='Roboto 20',
                     pad=(0, 20))],
            [sg.Text(text="There should be at least " +
                     str(vessegen.MEDIA_VOL) +
                     "mL in the reservoir.", font='Roboto 20',
                     pad=(0, 20))],
            [sg.Text(text="Note: if there is enough media, make sure the " +
                     "value noted by the software is accurate.",
                     font='Roboto 15', pad=(0, 20))],
            [sg.Button("OK", font='Roboto 15', pad=(5, 20))]
        ]

        # If there isn't enough media in the reservoir, alert the user
        popup_window = sg.Window("Vessegen Bioreactor Software", layout,
                                 element_justification='center',
                                 finalize=True, icon=vessegen.ICON_PATH)

        while True:
            # Read the user input from the GUI
            event, _ = popup_window.read(timeout=100)

            # First, the monitor should check if it needs to update itself
            update_monitor(window, led, start_time)

            # If the user has selected "OK", "Cancel", or closed the window,
            # then exit the popup window
            if event in ('Cancel', None, 'OK', sg.WIN_CLOSED):
                break

        # Close the popup window
        popup_window.close()
    else:
        # Inform the user that we are calculating time (update GUI)
        chambers[chamber_id]["status"] = "Calculating time..."

        # Check if the monitor needs to be updated
        update_monitor(window, led, start_time)

        # Determine the time it will take to remove the media
        time_to_remove, _ = calculate_media_change_time(vessegen.MEDIA_VOL,
                                                        window, led,
                                                        start_time)
        # HARD CODE FOR NOW
        time_to_remove = 80

        # Inform the user that we are removing media (update GUI)
        chambers[chamber_id]["status"] = "Removing media..."

        # Send the signal to remove the media and wait
        # pylint: disable=no-member
        GPIO.output(vessegen.GPIO_PINS[chamber_id]["remove"], GPIO.HIGH)
        started = time.time()
        while True:
            update_monitor(window, led, start_time)
            if time.time() > started + time_to_remove:
                break
            time.sleep(0.05)

        # Send the close signal and wait a brief moment to ensure closure
        # pylint: disable=no-member
        GPIO.output(vessegen.GPIO_PINS[chamber_id]["remove"], GPIO.LOW)
        time.sleep(0.1)

        # Inform the user that we are calculating time (update GUI)
        chambers[chamber_id]["status"] = "Calculating time..."

        # Check if the monitor needs to be updated
        update_monitor(window, led, start_time)

        # Calculate the time it will take to add the media as well as the
        # volume we estimate to be removed
        time_to_add, vol = calculate_media_change_time(chambers[chamber_id]
                                                       ["media_in_chamber"],
                                                       window, led,
                                                       start_time, True)
        # HARD CODE FOR NOW
        time_to_add = 20

        # Inform the user that we are adding media (update GUI)
        chambers[chamber_id]["status"] = "Adding media..."

        # Send the signal to remove the media and wait
        # pylint: disable=no-member
        GPIO.output(vessegen.GPIO_PINS[chamber_id]["add"], GPIO.HIGH)
        started = time.time()

        while True:
            update_monitor(window, led, start_time)
            if time.time() > started + time_to_add:
                break
            time.sleep(0.05)

        # Send the close signal
        # pylint: disable=no-member
        GPIO.output(vessegen.GPIO_PINS[chamber_id]["add"], GPIO.LOW)

        # Inform the user that we are running again, decrement the media
        # removed from the reservoir
        chambers[chamber_id]["status"] = "Running"
        chambers[chamber_id]["last_changed"] = datetime.datetime.now()
        chambers[chamber_id]["media_in_chamber"] =\
            round(max(chambers[chamber_id]["media_in_chamber"] - vol, 0), 1)
        update_monitor(window, led, start_time)


def change_media_in_all_chambers(window, led, start_time):
    """Change the media in all of the used chambers."""
    # For all of the chambers in use, change the media
    for i in range(8):
        if chambers[i]['is_in_use']:
            change_media_in_single_chamber(i, window, led, start_time)


def calculate_media_change_time(media_in_res,
                                window, led, start_time, add=False):
    """Calculate the estimated time to complete a media change.

    This function defaults to removing media (add is False). To calculate time
    for adding media, simply set add to True.

    Note, this function takes in the led indicator information as well as the
    parent window so that it can keep updating the parent window while it
    waits for the user to be finished with this screen.
    """
    # The diameters of the tubes change depending on if it is the adding or
    # removing solenoid.
    diameter = 1.0 if add else 0.5

    # Initially, the time to complete is zero as is the volume added
    time_to_complete = 0
    volume_added = 0

    # Specify a small time step
    time_step = 1

    # Work with a copy
    bulk = media_in_res

    # Approximate the time to complete by iterating over small time steps and
    # estimating the volume added for that small time step
    while volume_added < vessegen.MEDIA_VOL:
        update_monitor(window, led, start_time)
        vol_step = bulk*((diameter/2)*(diameter/2))*time_step
        time_to_complete += time_step
        volume_added += max(vol_step, 0.0001)
        bulk -= vol_step

    # Add a margin of error
    time_to_complete = 5

    # Once estimated, return the time
    return time_to_complete, volume_added


def chamber_wash_screen():
    """Display the screen that can control a chamber wash."""
    prompt = [
            [sg.Text(text="Would you like to do a wash cycle?",
                     font='Roboto 30', pad=((0, 0), (120, 20)))],
            [sg.Button("Yes", font='Roboto 20', pad=(5, 20)),
             sg.Button("No", font='Roboto 20', pad=(5, 20))]
        ]
    
    confirm_empty = [
            [sg.Text(text="Please make sure the waste is empty.",
                     font='Roboto 30', pad=((0, 0), (120, 20)))],
            [sg.Button("Ok", font='Roboto 20', pad=(5, 20), key='OK1'),
             sg.Button("Cancel", font='Roboto 20', pad=(5, 20), key='CANCEL1')]
        ]
    
    confirm_added = [
            [sg.Text(text="Add the wash media to reservoirs that were used.",
                     font='Roboto 30', pad=((0, 0), (120, 20)))],
            [sg.Button("Ok", font='Roboto 20', pad=(5, 20), key='OK2'),
             sg.Button("Cancel", font='Roboto 20', pad=(5, 20), key='CANCEL2')]
        ]
    
    running_screen = [
        [sg.Text(text="Wash cycle running, please wait...",
                     font='Roboto 30', pad=((0, 0), (120, 20)))]
    ]

    wash_complete = [
        [sg.Text(text="Wash cycle complete!",
                     font='Roboto 30', pad=((0, 0), (120, 20)))],
        [sg.Button("Ok", font='Roboto 20', pad=(5, 20), key='OK3')]
    ]

    layout = [[sg.Column(prompt, key='-PROMPT-',
                         element_justification='center'),
               sg.Column(confirm_empty, visible=False, key='-CONFIRM-EMPTY-',
                         element_justification='center'),
               sg.Column(confirm_added, visible=False, key='-CONFIRM-ADDED-',
                         element_justification='center'),
               sg.Column(running_screen, visible=False, key='-RUNNING-',
                         element_justification='center'),
               sg.Column(wash_complete, visible=False, key='-COMPLETE-',
                         element_justification='center')]]

    # If there isn't enough media in the reservoir, alert the user
    window = sg.Window("Vessegen Bioreactor Software", layout,
                                element_justification='center',
                                finalize=True, icon=vessegen.ICON_PATH,
                                size=(1024, 595))
    
    # Start in the prompt
    current_layout = '-PROMPT-'

    while True:
        # Read the user input from the GUI
        event, _ = window.read()

        if event in ('No', 'CANCEL1', 'CANCEL2', 'OK3', None, sg.WIN_CLOSED):
            break

        elif event in ('Yes'):
            window[current_layout].update(visible=False)
            current_layout = '-CONFIRM-EMPTY-'
            window[current_layout].update(visible=True)

        elif event in ('OK1'):
            window[current_layout].update(visible=False)
            current_layout = '-CONFIRM-ADDED-'
            window[current_layout].update(visible=True)

        elif event in ('OK2'):
            window[current_layout].update(visible=False)
            current_layout = '-RUNNING-'
            window[current_layout].update(visible=True)
            wash_chambers()
            window[current_layout].update(visible=False)
            current_layout = '-COMPLETE-'
            window[current_layout].update(visible=True)


    window.close()


def wash_chambers():
    """Wash the chambers in use."""
    pass


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

        # Prompt the user if they would like to do a wash cycle
        chamber_wash_screen()


atexit.register(reset_chambers)


if __name__ == "__main__":
    main()

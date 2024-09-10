""" 
Initial run of the Experiment Class Refactor base class

Specific experiments are implemented as sub classes that overload a load_stimulus and present_stimulus method

Running each experiment:
obj = VisualP300({parameters})
obj.run()
"""

from abc import abstractmethod
from typing import Callable
from psychopy import prefs
from psychopy.visual.rift import Rift
#change the pref libraty to PTB and set the latency mode to high precision
prefs.hardware['audioLib'] = 'PTB'
prefs.hardware['audioLatencyMode'] = 3

from time import time
import random

import numpy as np
from pandas import DataFrame
from psychopy import visual, event

from eegnb import generate_save_fn


class BaseExperiment:

    def __init__(self, exp_name, duration, eeg, save_fn, n_trials: int, iti: float, soa: float, jitter: float,
                 use_vr=False):
        """ Initializer for the Base Experiment Class

        Args:
            n_trials (int): Number of trials/stimulus
            iti (float): Inter-trial interval
            soa (float): Stimulus on arrival
            jitter (float): Random delay between stimulus
            use_vr (bool): Use VR for displaying stimulus
        """

        self.exp_name = exp_name
        self.instruction_text = """\nWelcome to the {} experiment!\nStay still, focus on the centre of the screen, and try not to blink. \nThis block will run for %s seconds.\n
        Press spacebar to continue. \n""".format(self.exp_name)
        self.duration = duration
        self.eeg = eeg
        self.save_fn = save_fn
        self.n_trials = n_trials
        self.iti = iti
        self.soa = soa
        self.jitter = jitter
        self.use_vr = use_vr
        if use_vr:
            self.rift: Rift = visual.Rift(monoscopic=True, headLocked=True)
            self.all_vr_controllers = ['Xbox', 'LeftTouch', 'RightTouch']

    @abstractmethod
    def load_stimulus(self):
        """ 
        Method that loads the stimulus for the specific experiment, overwritten by the specific experiment
        Returns the stimulus object in the form of [{stim1},{stim2},...]
        Throws error if not overwritten in the specific experiment
        """
        raise NotImplementedError

    @abstractmethod
    def present_stimulus(self, idx : int):
        """
        Method that presents the stimulus for the specific experiment, overwritten by the specific experiment
        Displays the stimulus on the screen
        Pushes EEG Sample if EEG is enabled
        Throws error if not overwritten in the specific experiment

        idx : Trial index for the current trial
        """
        raise NotImplementedError

    def setup(self, instructions=True):

        # Initializing the record duration and the marker names
        self.record_duration = np.float32(self.duration)
        self.markernames = [1, 2]
        
        # Setting up the trial and parameter list
        self.parameter = np.random.binomial(1, 0.5, self.n_trials)
        self.trials = DataFrame(dict(parameter=self.parameter, timestamp=np.zeros(self.n_trials)))

        # Setting up Graphics 
        self.window = (
            visual.Rift(monoscopic=True, headLocked=True) if self.use_vr
            else visual.Window([1600, 900], monitor="testMonitor", units="deg", fullscr=False))
        
        # Loading the stimulus from the specific experiment, throws an error if not overwritten in the specific experiment
        self.stim = self.load_stimulus()
        
        # Show Instruction Screen if not skipped by the user
        if instructions:
            self.show_instructions()

        # Checking for EEG to setup the EEG stream
        if self.eeg:
             # If no save_fn passed, generate a new unnamed save file
            if self.save_fn is None:  
                # Generating a random int for the filename
                random_id = random.randint(1000,10000)
                # Generating save function
                experiment_directory = self.name.replace(' ', '_')
                self.save_fn = generate_save_fn(self.eeg.device_name, experiment_directory, random_id, random_id, "unnamed")

                print(
                    f"No path for a save file was passed to the experiment. Saving data to {self.save_fn}"
                )
    
    def show_instructions(self):
        """ 
        Method that shows the instructions for the specific Experiment
        In the usual case it is not overwritten, the instruction text can be overwritten by the specific experiment
        No parameters accepted, can be skipped through passing a False while running the Experiment
        """

        # Splitting instruction text into lines
        self.instruction_text = self.instruction_text % self.duration

        # Disabling the cursor during display of instructions
        self.window.mouseVisible = False

        # clear/reset any old key/controller events
        self.__clear_user_input()

        # Waiting for the user to press the spacebar or controller button or trigger to start the experiment
        while not self.__user_input('start'):
            # Displaying the instructions on the screen
            text = visual.TextStim(win=self.window, text=self.instruction_text, color=[-1, -1, -1])
            self.__draw(lambda: self.__draw_instructions(text))

            # Enabling the cursor again
            self.window.mouseVisible = True

    def __user_input(self, input_type):
        if input_type is 'start':
            key_list = 'spacebar'
            if self.use_vr:
                vr_buttons = ['A', 'X']
                vr_trigger_thresh = 0.0
        elif input_type is 'cancel':
            key_list = 'escape'
            if self.use_vr:
                vr_buttons = ['B', 'Y']

        if len(event.getKeys(keyList=key_list)) > 0:
            return True
        if self.use_vr:
            for vr_controller in self.all_vr_controllers:
                if self.get_vr_input(vr_controller, vr_buttons, vr_trigger_thresh):
                    return True
        return False

    def get_vr_input(self, vr_controller, buttons, trigger_thresh):
        """
        Method that returns True if the user presses the corresponding vr controller input
        Args:
            vr_controller: 'Xbox', 'LeftTouch' or 'RightTouch'
            buttons: None, 'A', 'B', 'X' or 'Y'
            trigger_thresh: From 0.0 to 1.0.

        Returns:

        """
        triggered = False
        if trigger_thresh:
            for x in self.rift.getIndexTriggerValues(vr_controller):
                if x > trigger_thresh:
                    triggered = True

        button_pressed, tsec = self.rift.getButtons(buttons, vr_controller, 'released')

        if triggered or button_pressed:
            return True

        return False

    def __draw_instructions(self, text):
        text.draw()
        self.window.flip()

    def __draw(self, present_stimulus: Callable):
        """
        Set the current eye position and projection for all given stimulus,
        then draw all stimulus and flip the window/buffer
         """
        if self.use_vr:
            tracking_state = self.window.getTrackingState()
            self.window.calcEyePoses(tracking_state.headPose.thePose)
            self.window.setDefaultView()
        present_stimulus()

    def __clear_user_input(self):
        event.getKeys()
        self.clear_vr_input()

    def clear_vr_input(self):
        """
        Clears/resets input events from vr controllers
        """
        if self.use_vr:
            self.rift.updateInputState()

    def run(self, instructions=True):
        """ Do the present operation for a bunch of experiments """

        def iti_with_jitter():
            return self.iti + np.random.rand() * self.jitter

        # Setup the experiment, alternatively could get rid of this line, something to think about
        self.setup(instructions)

        print("Wait for the EEG-stream to start...")

        # Start EEG Stream, wait for signal to settle, and then pull timestamp for start point
        if self.eeg:
            self.eeg.start(self.save_fn, duration=self.record_duration + 5)

        print("EEG Stream started")

        # Run trial until a key is pressed or experiment duration has expired.
        start = time()
        current_trial = current_trial_end = -1
        current_trial_begin = None

        # Current trial being rendered
        rendering_trial = -1

        # Clear/reset user input buffer
        self.__clear_user_input()

        while not self.__user_input('cancel') and (time() - start) < self.record_duration:

            current_experiment_seconds = time() - start
            # Do not present stimulus until current trial begins(Adhere to inter-trial interval).
            if current_trial_end < current_experiment_seconds:
                current_trial += 1
                current_trial_begin = current_experiment_seconds + iti_with_jitter()
                current_trial_end = current_trial_begin + self.soa

            # Do not present stimulus after trial has ended(stimulus on arrival interval).
            elif current_trial_begin < current_experiment_seconds:

                # if current trial number changed get new choice of image.
                if rendering_trial < current_trial:
                    # Some form of presenting the stimulus - sometimes order changed in lower files like ssvep
                    # Stimulus presentation overwritten by specific experiment
                    self.__draw(lambda: self.present_stimulus(current_trial, current_trial))
                    rendering_trial = current_trial
            else:
                self.__draw(lambda: self.window.flip())

        # Clearing the screen for the next trial
        event.clearEvents()

        # Closing the EEG stream
        if self.eeg:
            self.eeg.stop()

        # Closing the window
        self.window.close()

    @property
    def name(self) -> str:
        """ This experiment's name """
        return self.exp_name


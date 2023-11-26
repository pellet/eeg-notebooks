from time import time

import numpy as np
from pandas import DataFrame
from psychopy import visual
from pylsl import StreamInfo, StreamOutlet
from typing import Optional
from eegnb.experiments import Experiment
from eegnb.devices.eeg import EEG


class VisualGratingVEP(Experiment.BaseExperiment):

    def __init__(self, duration=120, eeg: Optional[EEG] = None, save_fn=None,
                 n_trials=2000, iti=0.2, soa=0.2, jitter=0.1, use_vr=False, use_fixation=False):

        exp_name = "Visual Grating VEP"
        super().__init__(exp_name, duration, eeg, save_fn, n_trials, iti, soa, jitter, use_vr, use_fixation)

        # create
        info = StreamInfo("Markers", "Markers", 1, 0, "int32", "myuidw43536")

        # next make an outlet
        self.outlet = StreamOutlet(info)

    def load_stimulus(self):
        # 
        self.markernames = [1, 2]

        grating_sf = 400 if self.use_vr else 0.2

        # self.grating = visual.GratingStim(win=self.window, mask="circle", size=20, sf=grating_sf)
        self.grating = visual.GratingStim(win=self.window, mask="circle", size=80, sf=grating_sf)
        # Setup log
        n_trials = 2000
        position = np.random.randint(0, 2, n_trials)
        self.trials = DataFrame(dict(position=position, timestamp=np.zeros(n_trials)))

    def present_stimulus(self, idx: int):
        # onset
        self.grating.phase += np.random.rand()
        pos = self.trials["position"].iloc[idx]
        self.grating.pos = [25 * (pos - 0.5), 0]
        self.grating.draw()

        self.outlet.push_sample([self.markernames[pos]], time())

        # Pushing the sample to the EEG
        if self.eeg:
            if self.eeg.backend == "muselsl":
                marker = [self.markernames[pos]]
            else:
                marker = self.markernames[pos]
            self.eeg.push_sample(marker=marker, timestamp=time())

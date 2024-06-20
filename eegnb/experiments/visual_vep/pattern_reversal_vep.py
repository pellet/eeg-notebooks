import os
from glob import glob
from time import time

from psychopy import visual
from pylsl import StreamInfo, StreamOutlet
from typing import Optional
from eegnb.devices.eeg import EEG
from eegnb.experiments import Experiment
from eegnb.stimuli import PATTERN_REVERSAL


class VisualPatternReversalVEP(Experiment.BaseExperiment):

    def __init__(self, duration=120, eeg: Optional[EEG] = None, save_fn=None,
                 n_trials=2000, iti=0, soa=0.5, jitter=0, use_vr=False):

        exp_name = "Visual Pattern Reversal VEP"
        super().__init__(exp_name, duration, eeg, save_fn, n_trials, iti, soa, jitter, use_vr)

        # create
        info = StreamInfo("Markers", "Markers", 1, 0, "int32", "myuidw43536")

        # next make an outlet
        self.outlet = StreamOutlet(info)

    def load_stimulus(self):
        # 
        self.markernames = [1, 2]

        load_image = lambda fn: visual.ImageStim(win=self.window, image=fn,
                                                 size=[2, 2] if self.use_vr else [40, 30])
        self.checkerboard = list(map(load_image, glob(os.path.join(PATTERN_REVERSAL, "checker*.jpeg"))))

        self.fixation = visual.GratingStim(win=self.window, size=0.2, pos=[0, 0], sf=0, rgb=[1, 0, 0])

    def present_stimulus(self, idx: int):
        # onset
        checkerboard_frame = idx % 2
        image = self.checkerboard[checkerboard_frame]
        image.draw()
        self.window.flip()

        self.outlet.push_sample([self.markernames[checkerboard_frame]], time())

        # Record the latency of the graphics displaying on the HUD
        perf_stats = super().rift._perfStats
        if perf_stats.frameStatsCount > 0:
            recent_stat = perf_stats.frameStats[0]
            self.eeg.set_latency(recent_stat.compositorLatency)

        # Pushing the sample to the EEG
        if self.eeg:
            if self.eeg.backend == "muselsl":
                marker = [self.markernames[checkerboard_frame]]
            else:
                marker = self.markernames[checkerboard_frame]
            self.eeg.push_sample(marker=marker, timestamp=time())

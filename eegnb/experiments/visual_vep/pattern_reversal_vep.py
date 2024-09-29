from time import time

from psychopy import visual
from pylsl import StreamInfo, StreamOutlet
from typing import Optional
from eegnb.devices.eeg import EEG
from eegnb.experiments import Experiment
from stimupy.stimuli.checkerboards import contrast_contrast


class VisualPatternReversalVEP(Experiment.BaseExperiment):

    def __init__(self, duration=120, eeg: Optional[EEG] = None, save_fn=None,
                 n_trials=2000, iti=0, soa=0.5, jitter=0, use_vr=False, size=None):

        exp_name = "Visual Pattern Reversal VEP"
        super().__init__(exp_name, duration, eeg, save_fn, n_trials, iti, soa, jitter, use_vr)

        #
        self.marker_names = [1, 2]

        if size is None:
            self.size = [2, 2] if self.use_vr else self.window.size
        else:
            self.size = size

    @staticmethod
    def create_checkerboard(intensity_checks):
        return contrast_contrast(
            visual_size=(10, 10),  # size in degrees
            ppd=30,  # pixels per degree
            frequency=(1, 1),  # spatial frequency of the checkerboard
            intensity_checks=intensity_checks,
            target_shape=(1, 1),
            alpha=0,
            tau=0,
        )

    def load_stimulus(self):

        contrast_checkerboard = self.create_checkerboard((1, -1))
        contrast_checkerboard_2 = self.create_checkerboard((-1, 1))

        # Create PsychoPy stimuli
        stim1 = visual.ImageStim(self.window, image=contrast_checkerboard['img'], units='pix',
                                 size=self.size, color='white')
        stim2 = visual.ImageStim(self.window, image=contrast_checkerboard_2['img'], units='pix',
                                 size=self.size, color='white')

        self.checkerboard = [stim1, stim2]

    def present_stimulus(self, idx: int):
        # onset
        checkerboard_frame = idx % 2
        image = self.checkerboard[checkerboard_frame]
        image.draw()
        self.window.flip()

        # Pushing the sample to the EEG
        if self.eeg:
            if self.eeg.backend == "muselsl":
                marker = [self.marker_names[checkerboard_frame]]
            else:
                marker = self.marker_names[checkerboard_frame]
            self.eeg.push_sample(marker=marker, timestamp=time())

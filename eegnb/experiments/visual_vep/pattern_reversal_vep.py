from time import time

from psychopy import visual
from typing import Optional, Any, List
from eegnb.devices.eeg import EEG
from eegnb.experiments import Experiment
from stimupy.stimuli.checkerboards import contrast_contrast


class VisualPatternReversalVEP(Experiment.BaseExperiment):

    def __init__(self, duration=120, eeg: Optional[EEG] = None, save_fn=None,
                 n_trials=2000, iti=0, soa=0.5, jitter=0, use_vr=False, window=None):

        exp_name = "Visual Pattern Reversal VEP"
        super().__init__(exp_name, duration, eeg, save_fn, n_trials, iti, soa, jitter, use_vr, window)

        self.marker_names = [1, 2]

    @staticmethod
    def create_monitor_checkerboard(intensity_checks):
        return contrast_contrast(
            visual_size=(9, 21),  # size in degrees
            ppd=30,  # pixels per degree
            frequency=(1, 1),  # spatial frequency of the checkerboard
            intensity_checks=intensity_checks,
            target_shape=(1, 1),
            alpha=0,
            tau=0,
            check_visual_size=0.5
        )

    @staticmethod
    def create_vr_checkerboard(intensity_checks):
        return contrast_contrast(
            visual_size=(21, 21),  # size in degrees
            ppd=30,  # pixels per degree
            frequency=(1, 1),  # spatial frequency of the checkerboard
            intensity_checks=intensity_checks,
            target_shape=(1, 1),
            alpha=0,
            tau=0,
            check_visual_size=0.5
        )

    def load_stimulus(self):

        if self.use_vr:
            # Create VR checkerboard
            create_checkerboard = self.create_vr_checkerboard

        else:
            # Create Monitor checkerboard
            create_checkerboard = self.create_monitor_checkerboard

        def create_checkerboard_stim(intensity_checks):
            return visual.ImageStim(self.window,
                                    image=create_checkerboard(intensity_checks)['img'],
                                    units='pix', size=self.window.size, color='white')

        return [create_checkerboard_stim((1, -1)), create_checkerboard_stim((-1, 1))]

    def present_stimulus(self, idx: int, trial: Any, stimuli: List[Any]):
        # onset
        checkerboard_frame = idx % 2
        image = stimuli[checkerboard_frame]
        image.draw()
        self.window.flip()

        # Pushing the sample to the EEG
        if self.eeg:
            if self.eeg.backend == "muselsl":
                marker = [self.marker_names[checkerboard_frame]]
            else:
                marker = self.marker_names[checkerboard_frame]
            self.eeg.push_sample(marker=marker, timestamp=time())

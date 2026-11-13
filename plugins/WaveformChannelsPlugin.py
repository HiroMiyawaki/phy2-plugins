
from phy import IPlugin


class WaveformChannelsPlugin(IPlugin):
    def attach_to_controller(self, controller):
        controller.model.n_closest_channels = 32
        controller.model.amplitude_threshold = 0

        print(
            "[WaveformChannelsPlugin] "
            "n_closest_channels = 32"
        )

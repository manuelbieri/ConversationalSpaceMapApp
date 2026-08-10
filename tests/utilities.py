from types import SimpleNamespace

from conversationalspacemapapp.Plotter import StylePicker
from conversationalspacemapapp.Types import Constants, Data

speaker00_name = "SPEAKER_00"
speaker00_label = "Label_00"
speaker00_type = Constants.Participant.Interviewer
speaker00_color = StylePicker.ColorPicker.pastel()[0]
speaker01_name = "SPEAKER_01"
speaker01_label = "Label_01"
speaker01_type = Constants.Participant.Interviewee
speaker01_color = StylePicker.ColorPicker.pastel()[1]


def get_parser_mock():
    return SimpleNamespace(
        map=[
            Data.Utterance(number=1, speaker=speaker00_name, words=10),
            Data.Utterance(number=2, speaker=speaker01_name, words=15),
        ],
        participants=[speaker00_name, speaker01_name],
    )


def get_plot_options(**changes) -> Data.PlotOptions:
    values = {
        "map": tuple(get_parser_mock().map),
        "participants": (
            Data.ParticipantOptions(
                speaker00_name,
                speaker00_type,
                speaker00_label,
                speaker00_color,
            ),
            Data.ParticipantOptions(
                speaker01_name,
                speaker01_type,
                speaker01_label,
                speaker01_color,
            ),
        ),
    }
    values.update(changes)
    return Data.PlotOptions(**values)

from mockito import when
from unittest.mock import MagicMock

import conversationalspacemapapp.Types.Data as Data
import conversationalspacemapapp.Types.Constants as Constants
import conversationalspacemapapp.App.AbstractApp as AbstractApp
import conversationalspacemapapp.Plotter.StylePicker as StylePicker
import conversationalspacemapapp.Parser.AbstractParser as AbstractParser

speaker00_name = "SPEAKER_00"
speaker00_label = "Label_00"
speaker00_type = Constants.Participant.Interviewer
speaker00_color = StylePicker.ColorPicker.pastel()[0]
speaker01_name = "SPEAKER_01"
speaker01_label = "Label_01"
speaker01_type = Constants.Participant.Interviewee
speaker01_color = StylePicker.ColorPicker.pastel()[1]


def get_parser_mock() -> AbstractParser.AbstractParser:
    parser = MagicMock()
    parser.map = [
        Data.Utterance(number=1, speaker=speaker00_name, words=10),
        Data.Utterance(number=2, speaker=speaker01_name, words=15),
    ]
    parser.participants = [speaker00_name, speaker01_name]
    return parser


def get_app_mock(
    parser: AbstractParser.AbstractParser = None,
) -> AbstractApp.AbstractApp:
    app = MagicMock()
    if parser is not None:
        app.parser = parser
    when(app)._get_participant_role(speaker00_name).thenReturn(speaker00_type)
    when(app)._get_participant_role(speaker01_name).thenReturn(speaker01_type)
    when(app)._get_participant_color(speaker00_name).thenReturn(speaker00_color)
    when(app)._get_participant_color(speaker01_name).thenReturn(speaker01_color)
    when(app)._get_participant_name(speaker00_name).thenReturn(speaker00_label)
    when(app)._get_participant_name(speaker01_name).thenReturn(speaker01_label)
    return app

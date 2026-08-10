from dataclasses import dataclass, field
from collections.abc import Sequence

import conversationalspacemapapp.Types.Constants as Constants


@dataclass(frozen=True, slots=True)
class ParticipantOptions:
    name: str
    type: Constants.Participant
    label: str
    color: str


@dataclass(frozen=True, slots=True)
class PlotOptions:
    """Complete, UI-independent input for a conversational-space plot."""

    map: Sequence["Utterance"] = field(default_factory=tuple)
    participants: Sequence[ParticipantOptions] = field(default_factory=tuple)
    title: str = "Conversational Map Space"
    show_title: bool = True
    labels: bool = True
    interviewer_label: str = "Interviewer"
    interviewee_label: str = "Interviewee"
    yaxis: bool = True
    xaxis: bool = True
    grid: bool = True
    legend: bool = True

    def _get_participant(self, participant_name: str) -> ParticipantOptions:
        for participant in self.participants:
            if participant.name == participant_name:
                return participant
        raise KeyError(f"Unknown participant: {participant_name}")

    def get_participant_color(self, participant_name: str) -> str:
        return self._get_participant(participant_name).color

    def get_participant_label(self, participant_name: str) -> str:
        return self._get_participant(participant_name).label

    def get_participant_type(self, participant_name: str) -> Constants.Participant:
        return self._get_participant(participant_name).type


@dataclass(frozen=True, slots=True)
class Utterance:
    number: int
    speaker: str
    words: int
    text: str = ""
    start_time: str | None = None
    end_time: str | None = None

    def __lt__(self, other):
        return self.number < other.number

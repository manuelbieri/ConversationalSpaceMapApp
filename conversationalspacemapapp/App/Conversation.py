from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path

from conversationalspacemapapp.Parser.AbstractParser import AbstractParser
from conversationalspacemapapp.Parser.TimestampParser import TimestampParser
from conversationalspacemapapp.Types.Constants import Participant
from conversationalspacemapapp.Types.Data import (
    ParticipantOptions,
    PlotOptions,
    Utterance,
)

ParserFactory = Callable[[Path], AbstractParser]


@dataclass(frozen=True, slots=True)
class ParticipantState:
    speaker: str
    role: Participant
    label: str
    color: str

    def as_plot_options(self) -> ParticipantOptions:
        return ParticipantOptions(
            name=self.speaker,
            type=self.role,
            label=self.label,
            color=self.color,
        )


@dataclass(frozen=True, slots=True)
class PlotSettings:
    title: str = "Conversational Map Space"
    show_title: bool = True
    labels: bool = True
    interviewer_label: str = "Interviewer"
    interviewee_label: str = "Interviewee"
    yaxis: bool = True
    xaxis: bool = True
    grid: bool = True
    legend: bool = True


@dataclass(frozen=True, slots=True)
class ConversationStatistics:
    total_words: int
    words_by_participant: Mapping[str, int]
    total_utterances: int
    utterances_by_participant: Mapping[str, int] = field(default_factory=dict)
    longest_utterance_by_participant: Mapping[str, int] = field(default_factory=dict)

    @property
    def speaker_count(self) -> int:
        return len(self.words_by_participant)

    @property
    def average_words_per_utterance(self) -> float:
        if self.total_utterances == 0:
            return 0.0
        return self.total_words / self.total_utterances

    def percentage_for(self, participant: str) -> float:
        if self.total_words == 0:
            return 0.0
        return round(
            100 * self.words_by_participant.get(participant, 0) / self.total_words, 1
        )

    def utterances_for(self, participant: str) -> int:
        return self.utterances_by_participant.get(participant, 0)

    def average_words_for(self, participant: str) -> float:
        utterances = self.utterances_for(participant)
        if utterances == 0:
            return 0.0
        return self.words_by_participant.get(participant, 0) / utterances

    def longest_utterance_for(self, participant: str) -> int:
        return self.longest_utterance_by_participant.get(participant, 0)

    def as_text(self) -> str:
        sections = [f"Total words: {self.total_words}"]
        sections.extend(
            f"Words {participant}: {words} ({self.percentage_for(participant)}%)"
            for participant, words in self.words_by_participant.items()
        )
        sections.append(f"Total utterances: {self.total_utterances}")
        return " / ".join(sections)


class ConversationSession:
    """Owns conversation state without depending on Toga widgets."""

    def __init__(
        self,
        *,
        parser_factory: ParserFactory = TimestampParser,
        default_role: Participant = Participant.Interviewer,
        default_color: str = "#66C2A5",
    ) -> None:
        self._parser_factory = parser_factory
        self._default_role = default_role
        self._default_color = default_color
        self._path: Path | None = None
        self._parser: AbstractParser | None = None
        self._utterances: tuple[Utterance, ...] = ()
        self._participants: dict[str, ParticipantState] = {}
        self._plot_settings = PlotSettings()

    @property
    def path(self) -> Path | None:
        return self._path

    @property
    def parser(self) -> AbstractParser | None:
        return self._parser

    @property
    def is_loaded(self) -> bool:
        return self._parser is not None

    @property
    def utterances(self) -> tuple[Utterance, ...]:
        return self._utterances

    @property
    def participants(self) -> tuple[ParticipantState, ...]:
        return tuple(self._participants.values())

    @property
    def plot_settings(self) -> PlotSettings:
        return self._plot_settings

    def load(self, path: Path) -> None:
        path = Path(path)
        if not path.is_file():
            raise FileNotFoundError(path)

        # Build the next state first so a parser failure cannot corrupt the active one.
        parser = self._parser_factory(path)
        utterances = tuple(parser.map)
        participants = {
            speaker: ParticipantState(
                speaker=speaker,
                role=self._default_role,
                label=speaker,
                color=self._default_color,
            )
            for speaker in parser.participants
        }

        self._path = path
        self._parser = parser
        self._utterances = utterances
        self._participants = participants

    def participant(self, speaker: str) -> ParticipantState:
        try:
            return self._participants[speaker]
        except KeyError as error:
            raise KeyError(f"Unknown participant: {speaker}") from error

    def set_participant_role(self, speaker: str, role: Participant) -> None:
        if not isinstance(role, Participant):
            raise TypeError("role must be a Participant")
        current = self.participant(speaker)
        self._participants[speaker] = replace(current, role=role)

    def set_participant_label(self, speaker: str, label: str) -> None:
        current = self.participant(speaker)
        self._participants[speaker] = replace(current, label=label)

    def set_participant_color(self, speaker: str, color: str) -> None:
        current = self.participant(speaker)
        self._participants[speaker] = replace(current, color=color)

    def set_plot_settings(self, settings: PlotSettings) -> None:
        if not isinstance(settings, PlotSettings):
            raise TypeError("settings must be PlotSettings")
        self._plot_settings = settings

    def roles_by_speaker(self) -> dict[str, Participant]:
        return {
            participant.speaker: participant.role
            for participant in self._participants.values()
        }

    def colors_by_speaker(self) -> dict[str, str]:
        return {
            participant.speaker: participant.color
            for participant in self._participants.values()
        }

    def labels_by_speaker(self) -> dict[str, str]:
        return {
            participant.speaker: participant.label
            for participant in self._participants.values()
        }

    def statistics(self) -> ConversationStatistics:
        words_by_participant = {
            participant.speaker: sum(
                utterance.words
                for utterance in self._utterances
                if utterance.speaker == participant.speaker
            )
            for participant in self._participants.values()
        }
        utterances_by_participant = {
            participant.speaker: sum(
                1
                for utterance in self._utterances
                if utterance.speaker == participant.speaker
            )
            for participant in self._participants.values()
        }
        longest_utterance_by_participant = {
            participant.speaker: max(
                (
                    utterance.words
                    for utterance in self._utterances
                    if utterance.speaker == participant.speaker
                ),
                default=0,
            )
            for participant in self._participants.values()
        }
        return ConversationStatistics(
            total_words=sum(words_by_participant.values()),
            words_by_participant=words_by_participant,
            total_utterances=len(self._utterances),
            utterances_by_participant=utterances_by_participant,
            longest_utterance_by_participant=longest_utterance_by_participant,
        )

    def build_plot_options(self) -> PlotOptions:
        if not self.is_loaded:
            raise RuntimeError("No conversation is loaded")
        settings = self._plot_settings
        return PlotOptions(
            map=self._utterances,
            participants=tuple(
                participant.as_plot_options() for participant in self.participants
            ),
            title=settings.title,
            show_title=settings.show_title,
            labels=settings.labels,
            interviewer_label=settings.interviewer_label,
            interviewee_label=settings.interviewee_label,
            yaxis=settings.yaxis,
            xaxis=settings.xaxis,
            grid=settings.grid,
            legend=settings.legend,
        )

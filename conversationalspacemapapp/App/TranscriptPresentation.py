import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from conversationalspacemapapp.Types.Constants import Participant
from conversationalspacemapapp.Types.Data import Utterance


@dataclass(frozen=True, slots=True)
class TranscriptMessage:
    """UI-independent presentation data for one transcript message."""

    speaker: str
    speaker_index: int
    label: str
    text: str
    timestamp: str
    role: Participant
    alignment: str
    color: str | None


class TranscriptPresentation:
    """Build consistent chat presentation data for HTML and PDF renderers."""

    _hex_color = re.compile(r"#[0-9a-fA-F]{6}\Z")

    @classmethod
    def build(
        cls,
        utterances: Sequence[Utterance],
        roles_by_speaker: Mapping[str, Participant] | None = None,
        colors_by_speaker: Mapping[str, str] | None = None,
        labels_by_speaker: Mapping[str, str] | None = None,
    ) -> tuple[TranscriptMessage, ...]:
        roles_by_speaker = roles_by_speaker or {}
        colors_by_speaker = colors_by_speaker or {}
        labels_by_speaker = labels_by_speaker or {}
        speaker_indexes: dict[str, int] = {}
        messages: list[TranscriptMessage] = []

        for utterance in utterances:
            if utterance.speaker not in speaker_indexes:
                speaker_indexes[utterance.speaker] = len(speaker_indexes)
            role = roles_by_speaker.get(utterance.speaker, Participant.Undefined)
            color = colors_by_speaker.get(utterance.speaker)
            messages.append(
                TranscriptMessage(
                    speaker=utterance.speaker,
                    speaker_index=speaker_indexes[utterance.speaker] % 8,
                    label=labels_by_speaker.get(
                        utterance.speaker,
                        utterance.speaker,
                    ),
                    text=utterance.text,
                    timestamp=cls._timestamp(utterance),
                    role=role,
                    alignment=cls._alignment_for(role),
                    color=(
                        color
                        if color is not None and cls._hex_color.fullmatch(color)
                        else None
                    ),
                )
            )
        return tuple(messages)

    @staticmethod
    def _alignment_for(role: Participant) -> str:
        if role == Participant.Interviewer:
            return "interviewer"
        if role == Participant.Interviewee:
            return "interviewee"
        return "undefined"

    @staticmethod
    def _timestamp(utterance: Utterance) -> str:
        if (
            utterance.start_time
            and utterance.end_time
            and utterance.start_time != utterance.end_time
        ):
            return f"{utterance.start_time}\u2013{utterance.end_time}"
        return utterance.start_time or utterance.end_time or ""

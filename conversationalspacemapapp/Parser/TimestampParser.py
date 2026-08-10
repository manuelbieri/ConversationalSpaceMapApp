import re

import conversationalspacemapapp.Types.Data as Data
import conversationalspacemapapp.Parser.AbstractParser as AbstractParser


class TimestampParser(AbstractParser.AbstractParser):
    @property
    def number_of_words_by_speaker(self) -> [int, int]:
        return [
            abs(sum(self.map_list[::2])),
            abs(sum(self.map_list[1::2])),
        ]

    def _clean_transcript(self) -> str:
        cleaned_transcript = re.sub(r"\n\[.*?] ", "\n", self._content)
        cleaned_transcript = cleaned_transcript.replace("\n-", "")
        return cleaned_transcript

    def _convert_text(self) -> list[Data.Utterance]:
        raw_tokens = self._content.split("\n\n")
        self._content = self._clean_transcript()
        tokens = self._content.split("\n\n")
        output = []
        counter = 0
        for raw_token, token in zip(raw_tokens, tokens):
            segments = token.split(" ")
            number_of_words = len(segments) - 1
            if number_of_words > 0:
                counter += 1
                timestamps = re.findall(r"(?m)^\[([^]]+)]", raw_token)
                output.append(
                    Data.Utterance(
                        number=counter,
                        speaker=segments[0],
                        words=number_of_words,
                        text=token.partition(" ")[2].strip(),
                        start_time=timestamps[0] if timestamps else None,
                        end_time=timestamps[-1] if timestamps else None,
                    )
                )
        return output

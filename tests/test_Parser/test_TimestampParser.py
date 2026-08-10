import unittest

import conversationalspacemapapp.Types.Data as Data
import conversationalspacemapapp.Parser.TimestampParser as TranscriptParser

import tests.TestResources as TestResources


class TestTimestampParser(unittest.TestCase):
    # Unlimited return of error messages
    maxDiff = None

    # Define parser
    parser: TranscriptParser.AbstractParser

    @classmethod
    def setUpParser(cls, short=True, multiple_speaker=False):
        if multiple_speaker:  # Long transcript with multiple speakers
            return TranscriptParser.TimestampParser(
                file=TestResources.path_multiple_speaker_transcript
            )
        elif short:
            return TranscriptParser.TimestampParser(
                file=TestResources.path_short_transcript
            )
        else:
            return TranscriptParser.TimestampParser(
                file=TestResources.path_long_transcript
            )

    def test_transcript_timestamp_short(self):
        parser = TestTimestampParser.setUpParser()
        self.assertEqual(parser.content, TestResources.content_short_transcript)

    def test_transcript_timestamp_map_short(self):
        parser = TestTimestampParser.setUpParser()
        sut: [Data.Utterance] = parser.map
        utterance1, utterance2 = sut[0], sut[1]

        # Test first utterance
        self.assertEqual(utterance1.number, 1)
        self.assertEqual(utterance1.speaker, "Interviewer")
        self.assertEqual(utterance1.words, 15)

        # Test second utterance
        self.assertEqual(utterance2.number, 2)
        self.assertEqual(utterance2.speaker, "Interviewee")
        self.assertEqual(utterance2.words, 4)

    def test_transcript_timestamp_map_short_list(self):
        parser = TestTimestampParser.setUpParser()
        self.assertEqual(parser.map_list, [-15, 4])

    def test_transcript_timestamp_message_short(self):
        parser = TestTimestampParser.setUpParser()
        utterance1, utterance2 = parser.map

        self.assertEqual(
            utterance1.text,
            "Ich habe noch nie so ein schlechtes Interview gesehen. "
            "Red jetzt nicht so klar, Mona.",
        )
        self.assertEqual(utterance1.start_time, "00:00:01")
        self.assertEqual(utterance1.end_time, "00:00:12")
        self.assertEqual(utterance2.text, "Jetzt noch etwas nuscheln.")
        self.assertEqual(utterance2.start_time, "00:00:22")
        self.assertEqual(utterance2.end_time, "00:00:22")

    def test_transcript_timestamp_map_long(self):
        parser = TestTimestampParser.setUpParser(short=False)
        sut: [Data.Utterance] = parser.map
        utterance1, utterance2, utterance3 = sut[0], sut[1], sut[2]

        # Test first utterance
        self.assertEqual(utterance1.number, 1)
        self.assertEqual(utterance1.speaker, "SPEAKER_00")
        self.assertEqual(utterance1.words, 26)

        # Test second utterance
        self.assertEqual(utterance2.number, 2)
        self.assertEqual(utterance2.speaker, "SPEAKER_01")
        self.assertEqual(utterance2.words, 31)

        # Test third utterance
        self.assertEqual(utterance3.number, 3)
        self.assertEqual(utterance3.speaker, "SPEAKER_00")
        self.assertEqual(utterance3.words, 2)

    def test_transcript_timestamp_map_long_list(self):
        parser = TestTimestampParser.setUpParser(short=False)
        self.assertEqual(parser.map_list, [-26, 31, -2])

    def test_transcript_timestamp_speaker_words_short(self):
        parser = TestTimestampParser.setUpParser()
        self.assertEqual(parser.number_of_words_by_speaker, [15, 4])

    def test_transcript_timestamp_speaker_words_long(self):
        parser = TestTimestampParser.setUpParser(short=False)
        self.assertEqual(parser.number_of_words_by_speaker, [28, 31])

    def test_transcript_timestamp_participants_short(self):
        parser = TestTimestampParser.setUpParser()
        self.assertEqual(parser.participants, ["Interviewee", "Interviewer"])

    def test_transcript_timestamp_participants_multiple_speakers(self):
        parser = TestTimestampParser.setUpParser(multiple_speaker=True)
        self.assertEqual(
            parser.participants, ["SPEAKER_00", "SPEAKER_01", "SPEAKER_02"]
        )

    def test_transcript_timestamp_message_multiple_speakers(self):
        parser = TestTimestampParser.setUpParser(multiple_speaker=True)
        utterance1, utterance2, utterance3 = parser.map

        self.assertEqual(utterance1.start_time, "00:00:01")
        self.assertEqual(utterance1.end_time, "00:00:12")
        self.assertEqual(utterance2.start_time, "00:00:15")
        self.assertEqual(utterance2.end_time, "00:00:24")
        self.assertEqual(utterance3.text, "Deine Mutter.")
        self.assertEqual(utterance3.start_time, "00:00:27")
        self.assertEqual(utterance3.end_time, "00:00:27")

import unittest

from conversationalspacemapapp.App.TranscriptRenderer import TranscriptRenderer
from conversationalspacemapapp.Types import Constants, Data


class TestTranscriptRenderer(unittest.TestCase):
    def setUp(self):
        self.renderer = TranscriptRenderer()

    def test_empty_transcript(self):
        content = self.renderer.render([])

        self.assertIn("No transcript loaded", content)
        self.assertNotIn('class="message-row', content)

    def test_role_alignment_color_timestamp_and_order(self):
        utterances = [
            Data.Utterance(1, "Interviewer A", 1, "First", "00:00:01", "00:00:01"),
            Data.Utterance(2, "Interviewee A", 1, "Second", "00:00:02", "00:00:03"),
            Data.Utterance(3, "Interviewer B", 1, "Third", None, "00:00:04"),
            Data.Utterance(4, "Interviewee B", 1, "Fourth"),
            Data.Utterance(5, "Observer", 1, "Fifth"),
        ]
        roles = {
            "Interviewer A": Constants.Participant.Interviewer,
            "Interviewee A": Constants.Participant.Interviewee,
            "Interviewer B": Constants.Participant.Interviewer,
            "Interviewee B": Constants.Participant.Interviewee,
        }
        colors = {
            "Interviewer A": "#123456",
            "Interviewee A": "#ABCDEF",
        }

        content = self.renderer.render(utterances, roles, colors)

        self.assertEqual(content.count('class="message-row interviewer"'), 2)
        self.assertEqual(content.count('class="message-row interviewee"'), 2)
        self.assertEqual(content.count('class="message-row undefined"'), 1)
        self.assertEqual(content.count('class="bubble speaker-0"'), 1)
        self.assertLess(content.index("First"), content.index("Second"))
        self.assertLess(content.index("Second"), content.index("Third"))
        self.assertIn("00:00:01", content)
        self.assertIn("00:00:02\u201300:00:03", content)
        self.assertIn("00:00:04", content)
        self.assertIn('style="--speaker-color: #123456"', content)
        self.assertIn('style="--speaker-color: #ABCDEF"', content)
        self.assertIn(
            ".message-row.interviewer { justify-content: flex-start; }",
            content,
        )
        self.assertIn(
            ".message-row.interviewee { justify-content: flex-end; }",
            content,
        )

    def test_invalid_speaker_color_is_not_injected(self):
        content = self.renderer.render(
            [Data.Utterance(1, "A", 1, "Hello")],
            colors_by_speaker={"A": '#123456; background: url("unsafe")'},
        )

        self.assertNotIn("background: url(&quot;unsafe&quot;)", content)
        self.assertNotIn('style="--speaker-color:', content)

    def test_plot_labels_replace_raw_speakers_and_blank_labels_hide_heading(self):
        content = self.renderer.render(
            [
                Data.Utterance(1, "SPEAKER_00", 1, "Question"),
                Data.Utterance(2, "SPEAKER_01", 1, "Answer"),
            ],
            labels_by_speaker={"SPEAKER_00": "Facilitator <A>", "SPEAKER_01": ""},
        )

        self.assertIn("Facilitator &lt;A&gt;", content)
        self.assertNotIn("SPEAKER_00", content)
        self.assertNotIn("SPEAKER_01", content)
        self.assertEqual(content.count('<header class="speaker">'), 1)

    def test_content_is_escaped_and_preserves_multiline_text(self):
        utterance = Data.Utterance(
            1,
            "Interviewer <lead>",
            1,
            '<script>alert("unsafe")</script> & text\nnext',
            "00:00:<01>",
            "00:00:<01>",
        )

        content = self.renderer.render([utterance])

        self.assertIn("Interviewer &lt;lead&gt;", content)
        self.assertIn(
            "&lt;script&gt;alert(&quot;unsafe&quot;)&lt;/script&gt; &amp; text\nnext",
            content,
        )
        self.assertIn("00:00:&lt;01&gt;", content)
        self.assertNotIn('<script>alert("unsafe")</script>', content)
        self.assertIn("white-space: pre-wrap", content)

    def test_document_is_local_read_only_and_minimal(self):
        content = self.renderer.render([Data.Utterance(1, "A", 1, "Hello")])

        self.assertIn("default-src 'none'", content)
        self.assertIn("background: transparent", content)
        self.assertIn("background: var(--bubble-background)", content)
        self.assertNotIn("<textarea", content)
        self.assertNotIn("contenteditable", content)
        self.assertNotIn("box-shadow", content)
        self.assertNotIn("--page-background", content)

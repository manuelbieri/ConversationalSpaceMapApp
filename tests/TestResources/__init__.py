import pathlib

path_short_transcript = (
    pathlib.Path(__file__).parent / "test_short_transcript/transcription_timestamps.txt"
)
content_short_transcript = """Interviewer Ich habe noch nie so ein schlechtes Interview gesehen. Red jetzt nicht so klar, Mona.\n\nInterviewee Jetzt noch etwas nuscheln.\n\n"""
path_long_transcript = (
    pathlib.Path(__file__).parent / "test_transcript/transcription_timestamps.txt"
)
path_multiple_speaker_transcript = (
    pathlib.Path(__file__).parent
    / "test_transcript_multiple_speakers/transcription_timestamps.txt"
)

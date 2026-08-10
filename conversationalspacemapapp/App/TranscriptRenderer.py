import html
from collections.abc import Mapping, Sequence

from conversationalspacemapapp.App.TranscriptPresentation import (
    TranscriptPresentation,
)
from conversationalspacemapapp.Types.Constants import Participant
from conversationalspacemapapp.Types.Data import Utterance


class TranscriptRenderer:
    """Renders a local, read-only transcript for a Toga WebView."""

    def render(
        self,
        utterances: Sequence[Utterance],
        roles_by_speaker: Mapping[str, Participant] | None = None,
        colors_by_speaker: Mapping[str, str] | None = None,
        labels_by_speaker: Mapping[str, str] | None = None,
    ) -> str:
        messages: list[str] = []

        presentation = TranscriptPresentation.build(
            utterances,
            roles_by_speaker,
            colors_by_speaker,
            labels_by_speaker,
        )
        for message in presentation:
            speaker = html.escape(message.label, quote=True)
            text = html.escape(message.text, quote=True)
            color_style = (
                f' style="--speaker-color: {message.color}"'
                if message.color is not None
                else ""
            )
            timestamp_markup = (
                '<footer class="timestamp">'
                f"{html.escape(message.timestamp, quote=True)}"
                "</footer>"
                if message.timestamp
                else ""
            )
            speaker_markup = (
                f'<header class="speaker">{speaker}</header>' if speaker else ""
            )

            messages.append(f"""
                <article class="message-row {message.alignment}">
                    <div class="bubble speaker-{message.speaker_index}"{color_style}>
                        {speaker_markup}
                        <div class="message-text">{text}</div>
                        {timestamp_markup}
                    </div>
                </article>
                """)

        transcript = "".join(messages) if messages else self._empty_state()
        return self._document(transcript)

    @staticmethod
    def _empty_state() -> str:
        return """
                <section class="empty-state">
                    <div class="empty-card">
                        <h1>No transcript loaded</h1>
                        <p>Open a timestamped transcript from the Home tab.</p>
                    </div>
                </section>
            """

    @staticmethod
    def _document(transcript: str) -> str:
        return f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="Content-Security-Policy"
          content="default-src 'none'; style-src 'unsafe-inline'">
    <style>
        :root {{
            color-scheme: light dark;
            --text-color: #172026;
            --muted-color: #5d6b73;
            --bubble-background: rgba(248, 250, 252, 0.92);
            --bubble-border: #e2e8f0;
        }}

        * {{ box-sizing: border-box; }}

        html, body {{
            min-height: 100%;
            margin: 0;
            background: transparent;
        }}

        body {{
            color: var(--text-color);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            font-size: 15px;
            line-height: 1.42;
            user-select: text;
        }}

        .chat {{
            display: flex;
            flex-direction: column;
            gap: 8px;
            min-height: 100vh;
            padding: 16px clamp(12px, 2.5vw, 36px);
        }}

        .message-row {{
            display: flex;
            width: 100%;
        }}

        .message-row.interviewer {{ justify-content: flex-start; }}
        .message-row.interviewee {{ justify-content: flex-end; }}
        .message-row.undefined {{ justify-content: center; }}

        .bubble {{
            max-width: min(72%, 780px);
            overflow-wrap: anywhere;
            padding: 8px 11px 6px;
            border: 1px solid var(--bubble-border);
            border-radius: 9px;
            background: var(--bubble-background);
        }}

        .speaker {{
            margin-bottom: 3px;
            color: var(--speaker-color, var(--speaker-fallback));
            font-size: 12px;
            font-weight: 700;
        }}

        .message-text {{ white-space: pre-wrap; }}

        .timestamp {{
            margin-top: 4px;
            color: var(--muted-color);
            font-size: 11px;
            text-align: right;
        }}

        .speaker-0 {{ --speaker-fallback: #006c63; }}
        .speaker-1 {{ --speaker-fallback: #176b35; }}
        .speaker-2 {{ --speaker-fallback: #185a88; }}
        .speaker-3 {{ --speaker-fallback: #8a3154; }}
        .speaker-4 {{ --speaker-fallback: #795b00; }}
        .speaker-5 {{ --speaker-fallback: #62419a; }}
        .speaker-6 {{ --speaker-fallback: #166c68; }}
        .speaker-7 {{ --speaker-fallback: #4f5b62; }}

        .empty-state {{
            display: grid;
            flex: 1;
            min-height: calc(100vh - 40px);
            place-items: center;
            text-align: center;
        }}

        .empty-card {{
            max-width: 430px;
            padding: 20px 24px;
        }}

        .empty-card h1 {{
            margin: 0 0 6px;
            font-size: 20px;
        }}

        .empty-card p {{
            margin: 0;
            color: var(--muted-color);
        }}

        @media (max-width: 600px) {{
            .chat {{ padding: 12px 10px; }}
            .bubble {{ max-width: 88%; }}
        }}

        @media (prefers-color-scheme: dark) {{
            :root {{
                --text-color: #e9edef;
                --muted-color: #aebac1;
                --bubble-background: rgba(39, 47, 53, 0.88);
                --bubble-border: #3f4b52;
            }}

            .speaker-0 {{ --speaker-fallback: #53bdeb; }}
            .speaker-1 {{ --speaker-fallback: #8de3a7; }}
            .speaker-2 {{ --speaker-fallback: #9bd5f5; }}
            .speaker-3 {{ --speaker-fallback: #f2a7c1; }}
            .speaker-4 {{ --speaker-fallback: #f2d47c; }}
            .speaker-5 {{ --speaker-fallback: #c8aef4; }}
            .speaker-6 {{ --speaker-fallback: #8cded8; }}
            .speaker-7 {{ --speaker-fallback: #c4cdd2; }}
        }}
    </style>
</head>
<body>
    <main class="chat">{transcript}</main>
</body>
</html>
"""

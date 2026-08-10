import base64
from pathlib import Path


class AboutRenderer:
    """Renders the local About page shown in a Toga WebView."""

    def __init__(self, *, icon_path: Path | None = None) -> None:
        self.icon_path = icon_path or Path(__file__).parent / "assets" / "CSM_icon.png"

    def render(self) -> str:
        return self._document(
            document_class="app",
            icon_markup=self._icon_markup(),
            security_policy=(
                '<meta http-equiv="Content-Security-Policy" '
                "content=\"default-src 'none'; style-src 'unsafe-inline'; "
                'img-src data:">'
            ),
        )

    def render_docs(self) -> str:
        """Render the static GitHub Pages variant of the About page."""
        return self._document(
            document_class="docs",
            icon_markup=(
                '<img class="intro-icon" src="images/CSM_icon.png" '
                'alt="Conversational Space Map illustration">'
            ),
            security_policy="",
        )

    def _icon_markup(self) -> str:
        try:
            icon = self.icon_path.read_bytes()
        except OSError:
            return ""
        encoded = base64.b64encode(icon).decode("ascii")
        return (
            '<img class="intro-icon" '
            f'src="data:image/png;base64,{encoded}" '
            'alt="Conversational Space Map illustration">'
        )

    @staticmethod
    def _document(
        *,
        document_class: str,
        icon_markup: str,
        security_policy: str,
    ) -> str:
        document = """<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="Create and interpret conversational space maps from timestamped interview transcripts.">
    <title>Conversational Space Map</title>
    __SECURITY_POLICY__
    <style>
        :root {
            color-scheme: light dark;
            --text-color: #172026;
            --muted-color: #5d6b73;
            --border-color: #e2e8f0;
            --link-color: #185a88;
        }

        * { box-sizing: border-box; }

        html, body {
            min-height: 100%;
            margin: 0;
            background: transparent;
        }

        body {
            color: var(--text-color);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            font-size: 15px;
            line-height: 1.42;
            user-select: text;
        }

        main {
            width: 100%;
            padding: 16px clamp(12px, 2.5vw, 36px) 32px;
        }

        body.docs main {
            width: min(calc(100% - 24px), 980px);
            margin-inline: auto;
        }

        section {
            padding: 4px 0 18px;
            border-bottom: 1px solid var(--border-color);
        }

        section:last-child { border-bottom: 0; }
        h1 { margin: 0 0 10px; font-size: 22px; }
        h2 { margin: 16px 0 8px; font-size: 17px; }
        p, ol { margin: 0 0 10px; }
        ol { padding-left: 24px; }
        li { margin-bottom: 8px; }
        .citation { color: var(--muted-color); }
        a { color: var(--link-color); }

        .intro {
            display: grid;
            grid-template-columns: minmax(180px, 260px) 1fr;
            gap: clamp(18px, 4vw, 38px);
            align-items: center;
        }

        .intro-icon {
            display: block;
            width: 100%;
            height: auto;
        }

        details.license { margin-top: 14px; }
        details.license summary { cursor: pointer; font-weight: 700; }
        details.license pre {
            margin: 14px 0 0;
            white-space: pre-wrap;
            overflow-wrap: anywhere;
            color: var(--text-color);
            font: 12px/1.45 ui-monospace, SFMono-Regular, Menlo, monospace;
        }

        @media (max-width: 650px) {
            .intro { grid-template-columns: 1fr; }
            .intro-icon { width: min(72vw, 280px); margin: 0 auto; }
        }

        @media (prefers-color-scheme: dark) {
            :root {
                --text-color: #e9edef;
                --muted-color: #aebac1;
                --border-color: #3f4b52;
                --link-color: #9bd5f5;
            }
        }
    </style>
</head>
<body class="__DOCUMENT_CLASS__">
    <main>
        <section>
            <div class="intro">
                __ICON_MARKUP__
                <div>
                    <h1>Conversational Space Map</h1>
                    <p>
                        A Conversational Space Map visually represents the
                        interaction between an interviewer and a participant.
                        Each horizontal bar records the number of words in one
                        utterance, with the speakers placed on opposite sides of
                        the central line. The resulting shape provides an overview
                        of the interview's rhythm and balance.
                    </p>
                    <p>
                        The map can reveal long monologues, repeated short answers,
                        stalled passages, interviewer dominance, or points where a
                        question generated a detailed response. Reading it beside
                        the transcript helps identify opportunities to improve the
                        questionnaire and interviewing approach.
                    </p>
                    <p class="citation">
                        <strong>Saunders, Mark, Philip Lewis, and Adrian Thornhill</strong>,
                        <em>Research methods for business students</em>, 9th edition,
                        Pearson, 2023.
                    </p>
                </div>
            </div>
        </section>

        <section>
            <h2>How to use</h2>
            <ol>
                <li>
                    Open an aTrain <code>transcription_timestamps.txt</code> file
                    with the document button, or select a previously opened file
                    from the recent-files list.
                </li>
                <li>
                    Open each speaker tab and assign the speaker's role as
                    Interviewer, Interviewee, or Undefined. Edit the displayed
                    label and choose the color used in both the plot and transcript.
                </li>
                <li>
                    In General settings, edit the title and decide whether the
                    participant labels, axes, legend, and grid should be visible.
                </li>
                <li>
                    Review word totals, turn lengths, speaker shares, and participant
                    statistics alongside the plot, then use the Transcript tab to
                    inspect interesting turns in the conversation.
                </li>
                <li>
                    Choose PDF or SVG for scalable publication-ready graphics, or
                    PNG for slides and documents, then use the save button to export
                    the plot. The Transcript tab can export the styled chat directly
                    to a paginated PDF. The recent-files list can be cleared without
                    closing the active transcript.
                </li>
            </ol>
        </section>

        <section>
            <h2>License</h2>
            <details class="license" open>
                <summary>MIT License</summary>
                <pre>MIT License

Copyright (c) 2024-2026 Manuel Bieri

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.</pre>
            </details>
        </section>
    </main>
</body>
</html>
"""
        return (
            document.replace("__DOCUMENT_CLASS__", document_class)
            .replace("__ICON_MARKUP__", icon_markup)
            .replace("    __SECURITY_POLICY__", security_policy)
        )

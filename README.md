# CTM Activity Parser v2

Easily fetch, store, and review up to 100 of your most recent CallTrackingMetrics call transcriptions.  
Extracted transcriptions are organized into local JSON files and featured in a dynamic HTML report with copy-paste tools—ideal for analysis and quick sharing.

---

## Features

- **Pulls up to 100 of your latest account calls via the CallTrackingMetrics API.**
- **Saves each call’s JSON to `/output_json` (wiped on each run for freshness).**
- **Auto-generates a rich HTML report with:**
  - Table view of all call IDs and transcriptions (+audio links if present)
  - Buttons to instantly copy 5, 10, or 25 numbered transcriptions to your clipboard
  - Visual feedback showing the number of transcripts copied
- **Supports direct call ID entry or "latest 100" by default.**
- **Overwrites old results every run for consistent, fresh outputs**
- **Auto-opens your report in your default web browser after script completes**

---

## Requirements

- Python 3.6+
- Internet connection (for fetching from the API)
- A CallTrackingMetrics API Access Key & Secret Key
- Your CTM Account ID

---

## Usage

1. **Download/copy the script (`activity_parser_v2.py`) into a local directory.**
2. **Open a terminal in that directory and run:**
   ```bash
   python3 activity_parser_v2.py
   ```
3. **Enter your CTM credentials and Account ID when prompted.**
4. **Leave call IDs blank** to fetch the latest 100; or enter a comma-separated list of specific call IDs.
5. After fetching, the local folder will contain:
   - `output_json/` folder with one JSON per call
   - `ctm_transcriptions_output.html` — your interactive report (auto-opens)
6. **Use the Copy 5, Copy 10, or Copy 25 button to instantly copy those transcriptions (with numbering!) to your clipboard for fast pasting elsewhere.**

---

## Security

- Your keys are used only for this one-time fetch and are never stored.
- Local files are wiped/overwritten on each run.

---

## Example

![Animated walk-through of script’s HTML output and copy buttons](screenshot_or_animation.gif)

---

## License

MIT License

---

## Issues

If you discover bugs or want further enhancements (filters, CSV export, more UI tools), please open an issue or pull request!

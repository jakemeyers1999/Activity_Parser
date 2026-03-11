import os
import json
import base64
import requests
import shutil

def extract_field(data, fieldstr):
    """Extracts value by dot-separated path from nested dict."""
    parts = fieldstr.split('.')
    val = data
    for p in parts:
        if isinstance(val, dict) and p in val:
            val = val[p]
        else:
            return ""
    return val

def fetch_activity_jsons(account_id, api_access_key, api_secret_key, activity_ids, output_dir, transcription_field):
    os.makedirs(output_dir, exist_ok=True)
    transcriptions = []
    total = len(activity_ids)
    for idx, call_id in enumerate(activity_ids, 1):
        url = f"https://api.calltrackingmetrics.com/api/v1/accounts/{account_id}/calls/{call_id}"
        print(f"DEBUG: ({idx}/{total}) Fetching call details from: {url}")
        resp = requests.get(
            url,
            auth=(api_access_key, api_secret_key),
            headers={"Accept": "application/json"}
        )
        out_path = os.path.join(output_dir, f"{call_id}.json")
        with open(out_path, "w") as jf:
            jf.write(resp.text)
        try:
            data = resp.json()
            transcription = extract_field(data, transcription_field)
            audio = data.get("audio", None)
        except Exception as e:
            print(f"Failed to parse json for {call_id}: {e}")
            transcription = ""
            audio = None
        transcriptions.append({
            "call_id": call_id,
            "transcription": transcription,
            "audio": audio
        })
    return transcriptions

def fetch_last_call_ids(account_id, api_access_key, api_secret_key, per_page=100):
    lookup_url = f"https://api.calltrackingmetrics.com/api/v1/accounts/{account_id}/lookup.json?object_type=activity&per_page={per_page}"
    print(f"Using lookup URL: {lookup_url}")
    credentials = f"{api_access_key}:{api_secret_key}"
    b64_credentials = base64.b64encode(credentials.encode()).decode()
    headers = {
        "Authorization": f"Basic {b64_credentials}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    resp = requests.get(lookup_url, headers=headers)
    data = resp.json()
    results = data.get('results', [])
    activity_ids = [str(r.get('id')) for r in results if r.get('id')]
    print(f"Fetched {len(activity_ids)} most recent Activity IDs")
    return activity_ids

def load_transcriptions_from_json(output_dir, transcription_field):
    transcriptions = []
    for fname in os.listdir(output_dir):
        if fname.endswith('.json'):
            try:
                with open(os.path.join(output_dir, fname)) as f:
                    data = json.load(f)
                    transcription = extract_field(data, transcription_field)
                    audio = data.get("audio", None)
                transcriptions.append({
                    "call_id": data.get("id", fname),
                    "transcription": transcription,
                    "audio": audio
                })
            except Exception as e:
                print(f"Skipping {fname}: {e}")
    return transcriptions

def make_html(transcriptions, transcription_field):
    safe_text = lambda text: str(text if text is not None else '').replace("<", "&lt;").replace(">", "&gt;")
    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>CTM Call Field Viewer</title>
  <style>
    body{{background:#182132;color:#fff;font-family:sans-serif;margin:0;}}
    .wrap{{max-width:1000px;margin:20px auto;padding:24px;}}
    .card{{background:#25324a;padding:16px 18px;border-radius:12px;margin-bottom:22px;box-shadow:0 4px 14px rgba(2,6,23,.12);}}
    .trans-table{{width:100%;border-collapse:collapse;margin-top:12px;}}
    th,td{{padding:8px;text-align:left;}}
    th{{background:#2db4ea;color:#161616;}}
    tr:nth-child(even){{background:#223046;}}
    tr:hover{{background:#204860;}}
    .transcription{{white-space:pre-line;}}
    textarea.gpt-copy{{width:100%;height:180px;font-size:15px;margin-bottom:8px;padding:10px;border-radius:6px;resize:vertical;}}
    .copy-btn{{background:#01BDF6;border:none;padding:7px 20px;border-radius:7px;color:#0b1120;font-weight:bold;cursor:pointer;margin-bottom:10px;}}
    label,input{{font-size:1rem;}}
    #copy-status{{color:#01BDF6;font-weight:bold;margin-top:5px;transition:opacity 0.3s;opacity: 0}}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>CTM: {safe_text(transcription_field)} field from recent calls</h1>
    <div class="card">
      <div style="margin-bottom:8px;">
        <button class="copy-btn" onclick="fillCopy(5)">Copy 5</button>
        <button class="copy-btn" onclick="fillCopy(10)">Copy 10</button>
        <button class="copy-btn" onclick="fillCopy(25)">Copy 25</button>
      </div>
      <textarea id="copyArea" class="gpt-copy" readonly></textarea><br>
      <div id="copy-status"></div>
    </div>
    <script>
      var transcripts =
"""
    joined_transcripts = []
    for t in transcriptions:
        if (str(t['transcription'] or '').strip()):
            joined_transcripts.append(
                f"Call ID: {safe_text(t['call_id'])}\\n{safe_text(transcription_field)}:\\n{safe_text(t['transcription'])}\\n" + '-'*32
            )
    html += json.dumps(joined_transcripts, ensure_ascii=False, indent=2)
    html += """;
function showCopyMsg(n) {
  let msgBox = document.getElementById('copy-status');
  msgBox.innerText = 'Copied ' + n + ' result' + (n === 1 ? '' : 's') + '!';
  msgBox.style.opacity = 1;
  setTimeout(function() { msgBox.style.opacity = 0; }, 1500);
}
function fillCopy(n) {
  let count = Math.min(transcripts.length, n);
  let lines = '';
  for (let i = 0; i < count; i++) {
    lines += (i + 1) + '. ' + transcripts[i] + '\\n';
  }
  document.getElementById('copyArea').value = lines;
  navigator.clipboard.writeText(lines);
  showCopyMsg(count);
}
// Fill 10 by default
fillCopy(10);
</script>
"""
    html += f"""
    <div class="card"><table class="trans-table">
<tr><th>Call ID</th><th>{safe_text(transcription_field)}</th><th>Audio</th></tr>
"""
    for t in transcriptions:
        if (str(t['transcription'] or '').strip()):
            audio_html = f"<a href='{safe_text(t['audio'])}' target='_blank'>Listen</a>" if t['audio'] else "Not available"
            html += f"<tr><td>{safe_text(t['call_id'])}</td><td class='transcription'>{safe_text(t['transcription'])}</td><td>{audio_html}</td></tr>\n"
    html += '</table></div>\n'
    html += "  </div>\n</body>\n</html>\n"
    return html

if __name__ == "__main__":
    print("Script started\n")
    account_id = input("Enter CTM Account ID: ").strip()
    print(f"INFO: Using account_id = {account_id} for all lookups and outputs.")
    api_access_key = input("Enter API Access Key: ").strip()
    api_secret_key = input("Enter API Secret Key: ").strip()

    print("Example field values you can enter: transcription_text  |  custom_fields.example")
    transcription_field = input(
        "Enter the JSON field to extract from each call (press Enter to use default: transcription_text): "
    ).strip()
    if not transcription_field:
        transcription_field = "transcription_text"

    raw_ids = input("Enter comma-separated Call IDs (leave blank for last 100 calls): ").strip()
    output_dir = "output_json"

    # Clean up previous outputs: remove ctm_transcriptions_* files in the current dir
    for fname in os.listdir('.'):
        if fname.startswith('ctm_transcriptions_'):
            try:
                os.remove(fname)
            except Exception as e:
                print(f"Warning: Could not delete {fname}: {e}")

    # Remove and recreate output_json dir for fresh results
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    if raw_ids:
        activity_ids = [aid.strip() for aid in raw_ids.split(',') if aid.strip()]
        transcriptions = fetch_activity_jsons(account_id, api_access_key, api_secret_key, activity_ids, output_dir, transcription_field)
    else:
        activity_ids = fetch_last_call_ids(account_id, api_access_key, api_secret_key, per_page=100)
        transcriptions = fetch_activity_jsons(account_id, api_access_key, api_secret_key, activity_ids, output_dir, transcription_field)

    # After API fetch, strictly use local JSONs for reliable HTML content
    transcriptions = [t for t in load_transcriptions_from_json(output_dir, transcription_field) if str(t["transcription"]).strip()]

    if not transcriptions:
        print("No results found for field '{0}' - nothing to output.".format(transcription_field))
        exit(1)

    html = make_html(transcriptions, transcription_field)
    out_html = "ctm_transcriptions_output.html"
    with open(out_html, "w") as outf:
        outf.write(html)

    print(f"\n✅ Done! Output refreshed: '{output_dir}' and '{out_html}' for account {account_id} and field '{transcription_field}'.")

    import subprocess
    subprocess.run(['open', out_html])
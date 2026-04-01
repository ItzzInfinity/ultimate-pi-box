from __future__ import annotations

try:
    from flask import Flask, jsonify, redirect, render_template_string, request, url_for
except Exception:  # pragma: no cover - depends on local environment
    Flask = None


HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Ultimate Pi Box</title>
  <style>
    :root {
      --bg-a: #f2efe6;
      --bg-b: #d9e7d4;
      --ink: #16221c;
      --card: rgba(255,255,255,0.82);
      --line: rgba(22,34,28,0.18);
      --accent: #1f6f5f;
      --accent-2: #d67b39;
      --shadow: 0 18px 50px rgba(24,40,33,0.14);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(214,123,57,0.18), transparent 28%),
        radial-gradient(circle at bottom right, rgba(31,111,95,0.22), transparent 32%),
        linear-gradient(160deg, var(--bg-a), var(--bg-b));
      font-family: "Trebuchet MS", "Gill Sans", sans-serif;
    }
    .shell {
      max-width: 1180px;
      margin: 0 auto;
      padding: 28px 18px 40px;
    }
    .hero {
      display: grid;
      gap: 14px;
      grid-template-columns: 1.6fr 1fr;
      margin-bottom: 18px;
    }
    .panel {
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 20px;
      padding: 18px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(8px);
    }
    .hero h1, .panel h2 {
      margin: 0 0 8px;
      font-family: Georgia, "Times New Roman", serif;
      letter-spacing: 0.02em;
    }
    .meta {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-top: 14px;
    }
    .pill {
      display: inline-flex;
      align-items: center;
      padding: 8px 12px;
      border-radius: 999px;
      background: rgba(31,111,95,0.08);
      border: 1px solid rgba(31,111,95,0.14);
      font-size: 14px;
    }
    .grid {
      display: grid;
      gap: 16px;
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .actions, .transport, .menu-links {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
    }
    button, a.button {
      border: 0;
      border-radius: 12px;
      padding: 11px 14px;
      background: var(--accent);
      color: white;
      cursor: pointer;
      text-decoration: none;
      font: inherit;
      box-shadow: 0 8px 24px rgba(31,111,95,0.22);
    }
    button.alt, a.button.alt {
      background: var(--accent-2);
    }
    button.ghost, a.button.ghost {
      background: white;
      color: var(--ink);
      border: 1px solid var(--line);
      box-shadow: none;
    }
    ul {
      list-style: none;
      margin: 0;
      padding: 0;
      display: grid;
      gap: 8px;
      max-height: 290px;
      overflow: auto;
    }
    li.row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 10px 12px;
      background: rgba(255,255,255,0.62);
      border: 1px solid rgba(22,34,28,0.08);
      border-radius: 12px;
    }
    .dim { opacity: 0.72; }
    .mono { font-family: "Consolas", monospace; }
    .wide { grid-column: 1 / -1; }
    @media (max-width: 860px) {
      .hero, .grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <section class="hero">
      <div class="panel">
        <h1>Ultimate Pi Box</h1>
        <div class="dim">Remote control and media overview for the Pi on the local network.</div>
        <div class="meta">
          <span class="pill">Current screen: {{ state.current_component_label or "Main Menu" }}</span>
          <span class="pill">Mock mode: {{ "yes" if state.mock_mode else "no" }}</span>
          <span class="pill mono">Port {{ state.web_port }}</span>
        </div>
      </div>
      <div class="panel">
        <h2>Now Playing</h2>
        {% if state.current_component_state and state.current_component_state.get("current_item") %}
        <div><strong>{{ state.current_component_state.get("current_item") }}</strong></div>
        <div class="dim">{{ state.current_component_label }}</div>
        {% else %}
        <div class="dim">No active track selected.</div>
        {% endif %}
      </div>
    </section>

    <section class="grid">
      <div class="panel">
        <h2>OLED Controls</h2>
        <form class="actions" method="post" action="{{ url_for('action') }}">
          <button name="name" value="up">Up</button>
          <button name="name" value="down">Down</button>
          <button name="name" value="press" class="alt">Press</button>
          <button name="name" value="back" class="ghost">Back</button>
        </form>
      </div>

      <div class="panel">
        <h2>Open Screen</h2>
        <div class="menu-links">
          {% for item in state.menu_items %}
          <a class="button ghost" href="{{ url_for('open_component', key=item['key']) }}">{{ item['label'] }}</a>
          {% endfor %}
        </div>
      </div>

      <div class="panel wide">
        <h2>Transport</h2>
        <div class="transport">
          <a class="button" href="{{ url_for('component_command', key='my_music', command='previous') }}">Music Prev</a>
          <a class="button alt" href="{{ url_for('component_command', key='my_music', command='play_pause') }}">Music Play/Pause</a>
          <a class="button" href="{{ url_for('component_command', key='my_music', command='next') }}">Music Next</a>
          <a class="button ghost" href="{{ url_for('component_command', key='internet_radio', command='previous') }}">Radio Prev</a>
          <a class="button alt" href="{{ url_for('component_command', key='internet_radio', command='play_pause') }}">Radio Play/Stop</a>
          <a class="button ghost" href="{{ url_for('component_command', key='internet_radio', command='next') }}">Radio Next</a>
          <a class="button ghost" href="{{ url_for('component_command', key='dlna_upnp', command='refresh') }}">DLNA Refresh</a>
        </div>
      </div>

      {% for component_key in ['my_music', 'internet_radio', 'youtube_online', 'dlna_upnp'] %}
      {% set component = state.components.get(component_key) %}
      <div class="panel">
        <h2>{{ component.label }}</h2>
        {% if component.get("current_item") %}
        <div><strong>{{ component.get("current_item") }}</strong></div>
        {% endif %}
        {% if component.get("source_path") %}
        <div class="dim mono">{{ component.get("source_path") }}</div>
        {% endif %}
        <ul>
          {% for item in component.get("items", [])[:14] %}
          <li class="row">
            <span>{{ item }}</span>
            <a class="button ghost" href="{{ url_for('component_command', key=component_key, command='open', value=loop.index0) }}">Open</a>
          </li>
          {% else %}
          <li class="row dim"><span>No items available.</span></li>
          {% endfor %}
        </ul>
      </div>
      {% endfor %}
    </section>
  </div>
</body>
</html>
"""


def create_web_app(controller):
    if Flask is None:
        return None
    app = Flask(__name__)

    @app.route("/", methods=["GET"])
    def home():
        return render_template_string(HTML, state=controller.snapshot_state())

    @app.route("/api/status", methods=["GET"])
    def status():
        return jsonify(controller.snapshot_state())

    @app.route("/open/<key>", methods=["GET"])
    def open_component(key: str):
        controller.open_component_by_key(key)
        return redirect(url_for("home"))

    @app.route("/action", methods=["POST"])
    def action():
        name = request.form.get("name", "")
        if name == "up":
            controller.handle_rotation(-1)
        elif name == "down":
            controller.handle_rotation(1)
        elif name == "press":
            controller.handle_short_press()
        elif name == "back":
            controller.handle_long_press()
        return redirect(url_for("home"))

    @app.route("/component/<key>/<command>", methods=["GET", "POST"])
    def component_command(key: str, command: str):
        value = request.values.get("value")
        controller.dispatch_web_command(key, command, value)
        return redirect(url_for("home"))

    return app

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
    body { font-family: sans-serif; max-width: 860px; margin: 24px auto; padding: 0 16px; }
    h1, h2 { margin-bottom: 8px; }
    .card { border: 1px solid #ccc; border-radius: 10px; padding: 16px; margin-bottom: 16px; }
    .row { display: flex; gap: 8px; flex-wrap: wrap; }
    button, a.button { border: 1px solid #333; border-radius: 8px; padding: 10px 14px; background: #fff; cursor: pointer; text-decoration: none; color: #111; }
    ul { padding-left: 20px; }
    .mono { font-family: monospace; }
  </style>
</head>
<body>
  <h1>Ultimate Pi Box</h1>
  <div class="card">
    <div>Current screen: <strong>{{ state.current_component_label or "Main Menu" }}</strong></div>
    <div>Mock mode: <strong>{{ "yes" if state.mock_mode else "no" }}</strong></div>
    <div>Web port: <span class="mono">{{ state.web_port }}</span></div>
  </div>

  <div class="card">
    <h2>Remote Controls</h2>
    <form method="post" action="{{ url_for('action') }}">
      <div class="row">
        <button name="name" value="up">Up</button>
        <button name="name" value="down">Down</button>
        <button name="name" value="press">Press</button>
        <button name="name" value="back">Back</button>
      </div>
    </form>
  </div>

  <div class="card">
    <h2>Open Component</h2>
    <div class="row">
      {% for item in state.menu_items %}
      <a class="button" href="{{ url_for('open_component', key=item['key']) }}">{{ item['label'] }}</a>
      {% endfor %}
    </div>
  </div>

  <div class="card">
    <h2>Menu</h2>
    <ul>
      {% for item in state.menu_items %}
      <li>
        {% if loop.index0 == state.selected_index %}<strong>{% endif %}
        {{ item['label'] }}
        {% if loop.index0 == state.selected_index %}</strong>{% endif %}
      </li>
      {% endfor %}
    </ul>
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

    return app

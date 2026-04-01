"""Shared UI utilities for Colab SLM notebooks.

Functions
---------
build_model_table_html(models, precision_toggle=False) -> str
    Interactive table with per-row Load buttons.
    models: list of dicts with keys id, downloads, likes,
            and optionally gated (bool) and gguf_files (list[str]).
    precision_toggle: show fp16 / 4-bit selector above the table (PyTorch notebook).

register_load_callback(load_fn) -> None
    Registers load_fn as the notebook.load_model Colab callback.
    load_fn(model_id: str, variant: str) -> None
    variant is "" for ONNX, "fp16"/"4bit" for PyTorch, gguf filename for GGUF.

build_chat_html(title, subtitle="") -> str
    Returns the chat UI HTML string.

register_callback(generate_fn) -> None
    Registers generate_fn as the notebook.chat Colab callback.
    generate_fn(messages: list[dict]) -> str
"""

# ---------------------------------------------------------------------------
# Model table
# ---------------------------------------------------------------------------

# Plain string — not an f-string — so JS ${} template literals work without escaping.
_TABLE_TEMPLATE = """\
<style>
  .slm-table {
    border-collapse: collapse;
    font-family: monospace;
    font-size: 13px;
    color-scheme: light dark;
    width: 100%;
    max-width: 760px;
  }
  .slm-table th {
    text-align: left;
    border-bottom: 2px solid;
    padding: 6px 12px;
  }
  .slm-table td { padding: 5px 12px; }
  .slm-table td:nth-child(3),
  .slm-table td:nth-child(4),
  .slm-table th:nth-child(3),
  .slm-table th:nth-child(4) { text-align: right; }
  .slm-table tr:hover td { opacity: 0.85; }
  @media (prefers-color-scheme: light) {
    .slm-table th { background: #f0f0f0; border-color: #bbb; color: #111; }
    .slm-table td { color: #111; }
  }
  @media (prefers-color-scheme: dark) {
    .slm-table th { background: #2a2a2a; border-color: #555; color: #ddd; }
    .slm-table td { color: #ccc; }
  }
  .load-btn {
    background: #1a1a2e;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 5px 14px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    min-width: 72px;
    transition: background 0.15s;
  }
  .load-btn:disabled { opacity: 0.55; cursor: default; }
  .load-btn.loaded { background: #2d6a4f; }
  .load-btn.errored { background: #922b21; }
  .variant-select {
    font-size: 12px;
    padding: 3px 6px;
    border-radius: 4px;
    border: 1px solid #888;
    background: transparent;
    color: inherit;
    max-width: 180px;
  }
  .prec-btn {
    background: transparent;
    border: 1px solid #888;
    border-radius: 6px;
    padding: 4px 14px;
    font-size: 12px;
    cursor: pointer;
    color: inherit;
    transition: all 0.15s;
  }
  .prec-btn.active { background: #1a1a2e; color: white; border-color: #1a1a2e; }
</style>

__PRECISION__

<table class="slm-table">
  <thead>
    <tr>
      <th>#</th>
      <th>Model ID</th>
      <th>Downloads</th>
      <th>Likes</th>
      __VARIANT_HEADER__
      <th></th>
    </tr>
  </thead>
  <tbody>
    __ROWS__
  </tbody>
</table>

<script>
(function() {
  let selectedPrecision = "fp16";

  window.setPrecision = function(btn) {
    selectedPrecision = btn.dataset.prec;
    document.querySelectorAll(".prec-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
  };

  function extractPayload(result) {
    if (result && result.data) {
      if (result.data["application/json"]) {
        const v = result.data["application/json"];
        return (typeof v === "string") ? JSON.parse(v) : v;
      }
      if (result.data["text/plain"]) {
        let t = result.data["text/plain"];
        t = t.replace(/^['"]/,"").replace(/['"]$/,"");
        t = t.replace(/\\'/g, "'").replace(/\\"/g, '"');
        return JSON.parse(t);
      }
    }
    if (result && result.ok !== undefined) return result;
    throw new Error("Unexpected response: " + JSON.stringify(result).substring(0, 200));
  }

  window.notebookLoadModel = async function(btn) {
    const modelId = btn.dataset.model;
    const row = btn.closest("tr");
    const variantEl = row ? row.querySelector(".variant-select") : null;
    const variant = variantEl ? variantEl.value : selectedPrecision;

    document.querySelectorAll(".load-btn").forEach(b => b.disabled = true);
    btn.textContent = "Loading...";

    try {
      const result = await google.colab.kernel.invokeFunction(
        "notebook.load_model", [modelId, variant], {}
      );
      const data = extractPayload(result);
      if (data.error) throw new Error(data.error);
      btn.textContent = "✓ Loaded";
      btn.classList.add("loaded");
      document.querySelectorAll(".load-btn:not(.loaded)").forEach(b => b.disabled = false);
    } catch (err) {
      btn.textContent = "✗ Error";
      btn.title = err.message;
      btn.classList.add("errored");
      btn.disabled = false;
      document.querySelectorAll(".load-btn:not(.errored)").forEach(b => b.disabled = false);
    }
  };
})();
</script>
"""


def build_model_table_html(models: list, precision_toggle: bool = False) -> str:
    """Return the interactive model selection table HTML.

    Args:
        models:           List of model dicts (id, downloads, likes,
                          optionally gated and gguf_files).
        precision_toggle: If True, render an fp16 / 4-bit selector above
                          the table (used by the PyTorch notebook).
    """
    has_gguf = any("gguf_files" in m for m in models)
    variant_header = "<th>Variant</th>" if has_gguf else ""

    rows = []
    for i, m in enumerate(models):
        gated = " 🔒" if m.get("gated") else ""
        if has_gguf:
            files = m.get("gguf_files", [])
            options = "".join(
                f'<option value="{f}">{f.split("/")[-1]}</option>'
                for f in files
            )
            variant_cell = f'<td><select class="variant-select">{options}</select></td>'
        else:
            variant_cell = ""
        rows.append(
            f"<tr>"
            f"<td>{i + 1}</td>"
            f"<td><code>{m['id']}</code>{gated}</td>"
            f"<td>{m.get('downloads', 0):,}</td>"
            f"<td>{m.get('likes', 0):,}</td>"
            f"{variant_cell}"
            f'<td><button class="load-btn" data-model="{m["id"]}" '
            f"onclick=\"notebookLoadModel(this)\">Load</button></td>"
            f"</tr>"
        )

    precision_html = ""
    if precision_toggle:
        precision_html = (
            '<div style="margin-bottom:12px; display:flex; gap:8px; align-items:center;">'
            '<span style="font-size:13px; opacity:0.7; font-family:monospace;">Precision:</span>'
            '<button class="prec-btn active" data-prec="fp16" onclick="setPrecision(this)">fp16</button>'
            '<button class="prec-btn" data-prec="4bit" onclick="setPrecision(this)">4-bit</button>'
            "</div>"
        )

    return (
        _TABLE_TEMPLATE
        .replace("__ROWS__", "\n    ".join(rows))
        .replace("__PRECISION__", precision_html)
        .replace("__VARIANT_HEADER__", variant_header)
    )


def register_load_callback(load_fn) -> None:
    """Register load_fn as the notebook.load_model Colab callback.

    Args:
        load_fn: Callable(model_id: str, variant: str) -> None.
                 Should raise on failure; the error message is shown in the table.
    """
    from google.colab import output as colab_output
    from IPython.display import JSON as IPJSON

    def _callback(model_id, variant=""):
        try:
            load_fn(model_id, variant)
            return IPJSON({"ok": True})
        except Exception as e:
            return IPJSON({"error": str(e)})

    colab_output.register_callback("notebook.load_model", _callback)


# ---------------------------------------------------------------------------
# Chat UI
# ---------------------------------------------------------------------------

_CHAT_TEMPLATE = """\
<div id="chat-ui" style="
  font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
  max-width: 640px;
  border: 1px solid #d0d0d0;
  border-radius: 12px;
  overflow: hidden;
  background: #fafafa;
">
  <div style="
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    color: white;
    padding: 14px 18px;
    font-size: 15px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 8px;
  ">
    <span style="font-size:20px;">&#x1F916;</span>
    __HEADER__
  </div>

  <div id="chat-messages" style="
    height: 380px;
    overflow-y: auto;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  "></div>

  <div style="
    display: flex;
    border-top: 1px solid #e0e0e0;
    background: white;
    padding: 8px;
    gap: 8px;
  ">
    <input id="chat-input" type="text" placeholder="Type a message..."
      style="
        flex: 1;
        border: 1px solid #d0d0d0;
        border-radius: 8px;
        padding: 10px 14px;
        font-size: 14px;
        outline: none;
      "
    />
    <button onclick="chatSend()" style="
      background: #1a1a2e;
      color: white;
      border: none;
      border-radius: 8px;
      padding: 10px 18px;
      font-size: 14px;
      cursor: pointer;
      font-weight: 600;
    ">Send</button>
  </div>
</div>

<script>
(function() {
  const messagesDiv = document.getElementById("chat-messages");
  const inputEl     = document.getElementById("chat-input");
  let history = [];

  function addBubble(role, text) {
    const isUser = role === "user";
    const bubble = document.createElement("div");
    bubble.style.cssText = `
      max-width: 82%;
      padding: 10px 14px;
      border-radius: 12px;
      font-size: 14px;
      line-height: 1.5;
      word-wrap: break-word;
      white-space: pre-wrap;
      align-self: ${isUser ? "flex-end" : "flex-start"};
      background: ${isUser ? "#1a1a2e" : "#e8e8e8"};
      color: ${isUser ? "#fff" : "#1a1a1a"};
    `;
    bubble.textContent = text;
    messagesDiv.appendChild(bubble);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    return bubble;
  }

  function extractPayload(result) {
    if (result && result.data) {
      if (result.data["application/json"]) {
        const v = result.data["application/json"];
        return (typeof v === "string") ? JSON.parse(v) : v;
      }
      if (result.data["text/plain"]) {
        let t = result.data["text/plain"];
        t = t.replace(/^['"]/,"").replace(/['"]$/,"");
        t = t.replace(/\\'/g, "'").replace(/\\"/g, '"');
        return JSON.parse(t);
      }
    }
    if (result && result.reply) return result;
    throw new Error("Could not parse kernel response: " + JSON.stringify(result).substring(0, 200));
  }

  window.chatSend = async function() {
    const text = inputEl.value.trim();
    if (!text) return;
    inputEl.value = "";
    inputEl.disabled = true;
    const sendBtn = document.querySelector("#chat-ui button");
    sendBtn.disabled = true;
    sendBtn.textContent = "...";

    addBubble("user", text);
    history.push({role: "user", content: text});
    const thinking = addBubble("assistant", "Thinking...");

    try {
      const result = await google.colab.kernel.invokeFunction(
        "notebook.chat", [JSON.stringify(history)], {}
      );
      const data = extractPayload(result);
      if (data.error) throw new Error(data.error);
      thinking.textContent = data.reply;
      history.push({role: "assistant", content: data.reply});
    } catch (err) {
      thinking.textContent = "Error: " + err.message;
      thinking.style.background = "#ffe0e0";
      thinking.style.color = "#900";
      history.pop();
    }

    inputEl.disabled = false;
    sendBtn.disabled = false;
    sendBtn.textContent = "Send";
    inputEl.focus();
  };

  inputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); chatSend(); }
  });
})();
</script>
"""


def build_chat_html(title: str, subtitle: str = "") -> str:
    """Return the chat UI HTML string.

    Args:
        title:    Model name shown in the header.
        subtitle: Optional label (e.g. "ONNX · Q4", "fp16 · GPU").
    """
    if subtitle:
        header = (
            f'{title} &nbsp;<span style="font-weight:400; opacity:0.7; font-size:12px;">'
            f"{subtitle}</span>"
        )
    else:
        header = title
    return _CHAT_TEMPLATE.replace("__HEADER__", header)


def register_callback(generate_fn) -> None:
    """Register generate_fn as the notebook.chat Colab callback.

    Args:
        generate_fn: Callable(messages: list[dict]) -> str.
    """
    import json
    from google.colab import output as colab_output
    from IPython.display import JSON as IPJSON

    def _callback(messages_json):
        try:
            messages = json.loads(messages_json)
            reply = generate_fn(messages)
            return IPJSON({"reply": reply})
        except Exception as e:
            return IPJSON({"error": str(e)})

    colab_output.register_callback("notebook.chat", _callback)

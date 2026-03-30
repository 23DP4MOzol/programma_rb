from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from i18n import load_translations, t
from inventory_db import ALLOWED_STATUSES, Device, InventoryDB


def _read_json(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length") or 0)
    raw = handler.rfile.read(length) if length > 0 else b"{}"
    if not raw:
        return {}
    return json.loads(raw.decode("utf-8"))


def _write_json(handler: BaseHTTPRequestHandler, status: int, payload: Any) -> None:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


def _device_to_dict(d: Device) -> dict[str, Any]:
    return {
        "serial": d.serial,
        "device_type": d.device_type,
        "model": d.model,
        "from_store": d.from_store,
        "to_store": d.to_store,
        "status": d.status,
        "comment": d.comment,
        "created_at": d.created_at,
        "updated_at": d.updated_at,
    }


INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>programma_rb</title>
  <style>
    :root {
      --brand-red: #d50000;
      --bg: #ffffff;
      --text: #111111;
      --muted: #666666;
      --border: #e6e6e6;
      --panel: #fafafa;
      --danger: #b00020;
      --ok: #0a7a2f;
      --mono: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
      --sans: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
    }

    body { margin: 0; font-family: var(--sans); background: var(--bg); color: var(--text); }
    header { background: var(--brand-red); color: white; padding: 14px 16px; }
    header .title { font-weight: 700; font-size: 16px; }
    header .subtitle { opacity: 0.95; font-size: 13px; margin-top: 4px; }

    main { max-width: 1100px; margin: 0 auto; padding: 16px; }
    .row { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
    @media (max-width: 900px) { .row { grid-template-columns: 1fr; } }

    .card { border: 1px solid var(--border); border-radius: 10px; background: var(--panel); padding: 12px; }
    .card h2 { margin: 0 0 10px 0; font-size: 14px; }
    .toolbar { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }

    label { font-size: 12px; color: var(--muted); display: block; margin-bottom: 4px; }
    input, select { width: 100%; padding: 8px 10px; border: 1px solid var(--border); border-radius: 8px; font-size: 13px; background: white; }

    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    @media (max-width: 900px) { .grid { grid-template-columns: 1fr; } }

    button {
      background: var(--brand-red);
      color: white;
      border: none;
      border-radius: 10px;
      padding: 9px 12px;
      font-size: 13px;
      cursor: pointer;
    }
    button:hover { filter: brightness(0.96); }
    button:active { transform: translateY(1px); }
    button:disabled { opacity: 0.55; cursor: not-allowed; transform: none; }
    button.secondary { background: #ffffff; color: var(--brand-red); border: 1px solid var(--brand-red); }
    button.danger { background: var(--danger); }

    table { width: 100%; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden; border: 1px solid var(--border); }
    th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--border); font-size: 13px; }
    th { background: #fff5f5; color: #7a0000; font-size: 12px; text-transform: uppercase; letter-spacing: .04em; }
    td code { font-family: var(--mono); font-size: 12px; }
    tbody tr:hover { background: #fff5f5; }
    tbody tr.selected { outline: 2px solid var(--brand-red); outline-offset: -2px; }

    .row-actions { display:flex; gap:8px; align-items:center; }
    .row-actions button { padding: 6px 10px; border-radius: 9px; font-size: 12px; }
    .row-actions select { padding: 6px 8px; border-radius: 9px; font-size: 12px; }

    .result { font-family: var(--mono); font-size: 12px; padding: 10px; background: white; border: 1px solid var(--border); border-radius: 10px; white-space: pre-wrap; }
    .ok { color: var(--ok); }
    .err { color: var(--danger); }

    .footer { margin-top: 10px; color: var(--muted); font-size: 12px; }
  </style>
</head>
<body>
  <header>
    <div class="title" id="title">programma_rb</div>
    <div class="subtitle" id="subtitle"></div>
  </header>

  <main>
    <div class="toolbar" style="margin-bottom: 12px;">
      <div style="min-width: 210px;">
        <label id="lblLang"></label>
        <select id="lang">
          <option value="lv">LV</option>
          <option value="en">EN</option>
        </select>
      </div>
      <button class="secondary" id="btnRefresh"></button>
      <div class="footer">Tip: colors are in :root CSS variables (edit in web_app.py).</div>
    </div>

    <div class="row">
      <div class="card">
        <h2 id="hActions"></h2>
        <div class="grid">
          <div>
            <label id="lblSerial"></label>
            <input id="serial" placeholder="SN-001" />
          </div>
          <div>
            <label id="lblType"></label>
            <select id="device_type"></select>
          </div>
          <div>
            <label id="lblModel"></label>
            <input id="model" placeholder="Zebra DS2208" />
          </div>
          <div>
            <label id="lblStatus"></label>
            <select id="status"></select>
          </div>
          <div>
            <label id="lblFrom"></label>
            <input id="from_store" placeholder="RIMI001" />
          </div>
          <div>
            <label id="lblTo"></label>
            <input id="to_store" placeholder="RIMI123" />
          </div>
          <div style="grid-column: 1 / -1;">
            <label id="lblComment"></label>
            <input id="comment" placeholder="..." />
          </div>
        </div>

        <div class="toolbar" style="margin-top: 10px;">
          <label style="display:flex; align-items:center; gap:8px; margin:0; color: var(--text);">
            <input type="checkbox" id="overwrite" style="width:auto;" />
            <span id="lblOverwrite"></span>
          </label>
        </div>

        <div class="toolbar" style="margin-top: 10px;">
          <button id="btnAdd"></button>
          <button id="btnUpdate" class="secondary"></button>
          <button id="btnStatus" class="secondary"></button>
          <button id="btnDelete" class="danger"></button>
        </div>

        <div style="margin-top: 10px;">
          <label id="lblResult"></label>
          <div class="result" id="result"></div>
        </div>
      </div>

      <div class="card">
        <h2 id="hList"></h2>
        <div class="grid">
          <div>
            <label id="lblFilterStatus"></label>
            <select id="filter_status">
              <option value="">(all)</option>
            </select>
          </div>
          <div>
            <label id="lblLimit"></label>
            <input id="limit" type="number" min="1" max="2000" value="200" />
          </div>
          <div>
            <label id="lblFilterFrom"></label>
            <input id="filter_from" placeholder="RIMI001" />
          </div>
          <div>
            <label id="lblFilterTo"></label>
            <input id="filter_to" placeholder="RIMI123" />
          </div>
        </div>

        <div style="margin-top: 10px; overflow:auto;">
          <table>
            <thead>
              <tr>
                <th>serial</th>
                <th>type</th>
                <th>model</th>
                <th>from</th>
                <th>to</th>
                <th>status</th>
                <th>updated</th>
                <th id="thActions"></th>
              </tr>
            </thead>
            <tbody id="tbody"></tbody>
          </table>
          <div class="footer" id="count"></div>
        </div>
      </div>
    </div>
  </main>

<script>
  const el = (id) => document.getElementById(id);
  let I18N = {};
  let SELECTED_SERIAL = null;

  function escapeHtml(s) {
    return String(s)
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');
  }

  function setSelected(serial) {
    SELECTED_SERIAL = serial;
  }

  function deviceTypeLabel(code) {
    const c = (code || '').toLowerCase();
    const m = {
      'scanner': I18N.type_scanner,
      'laptop': I18N.type_laptop,
      'tablet': I18N.type_tablet,
      'phone': I18N.type_phone,
      'other': I18N.type_other,
    };
    return m[c] || code || '';
  }

  function setResult(text, ok=true) {
    const r = el('result');
    r.textContent = text;
    r.classList.toggle('ok', ok);
    r.classList.toggle('err', !ok);
  }

  async function loadI18n() {
    const lang = el('lang').value;
    const res = await fetch(`/api/i18n?lang=${encodeURIComponent(lang)}`);
    I18N = await res.json();

    el('title').textContent = I18N.web_title;
    el('subtitle').textContent = I18N.web_subtitle;
    el('lblLang').textContent = I18N.web_language;
    el('btnRefresh').textContent = I18N.web_refresh;
    el('hActions').textContent = I18N.web_action;
    el('hList').textContent = I18N.web_list;
    el('lblSerial').textContent = I18N.web_serial;
    el('lblType').textContent = I18N.web_type;
    el('lblModel').textContent = I18N.web_model;
    el('lblFrom').textContent = I18N.web_from_store;
    el('lblTo').textContent = I18N.web_to_store;
    el('lblStatus').textContent = I18N.web_status;
    el('lblComment').textContent = I18N.web_comment;
    el('lblOverwrite').textContent = I18N.web_overwrite;
    el('btnAdd').textContent = I18N.web_add;
    el('btnUpdate').textContent = I18N.web_update;
    el('btnStatus').textContent = I18N.web_change_status;
    el('btnDelete').textContent = I18N.web_delete;
    el('lblResult').textContent = I18N.web_result;
    el('lblFilterStatus').textContent = I18N.web_status;
    el('lblFilterFrom').textContent = I18N.web_from_store;
    el('lblFilterTo').textContent = I18N.web_to_store;
    el('lblLimit').textContent = I18N.web_limit;

    el('thActions').textContent = I18N.web_actions;

    fillStatusOptions();
    fillDeviceTypeOptions();
  }

  function fillStatusOptions() {
    const statuses = ["RECEIVED","PREPARING","PREPARED","SENT","IN_USE","RETURNED","RETIRED"];
    const labelFor = (s) => {
      const m = {
        "RECEIVED": I18N.status_received,
        "PREPARING": I18N.status_preparing,
        "PREPARED": I18N.status_prepared,
        "SENT": I18N.status_sent,
        "IN_USE": I18N.status_in_use,
        "RETURNED": I18N.status_returned,
        "RETIRED": I18N.status_retired,
      };
      return m[s] || s;
    };

    const statusSel = el('status');
    const filterSel = el('filter_status');

    statusSel.innerHTML = '';
    filterSel.innerHTML = '<option value="">(all)</option>';

    for (const s of statuses) {
      const o1 = document.createElement('option');
      o1.value = s;
      o1.textContent = `${s} — ${labelFor(s)}`;
      statusSel.appendChild(o1);

      const o2 = document.createElement('option');
      o2.value = s;
      o2.textContent = `${s} — ${labelFor(s)}`;
      filterSel.appendChild(o2);
    }
  }

  function fillDeviceTypeOptions() {
    const types = [
      { value: 'scanner', label: I18N.type_scanner },
      { value: 'laptop', label: I18N.type_laptop },
      { value: 'tablet', label: I18N.type_tablet },
      { value: 'phone', label: I18N.type_phone },
      { value: 'other', label: I18N.type_other },
    ];

    const sel = el('device_type');
    sel.innerHTML = '';
    for (const t of types) {
      const o = document.createElement('option');
      o.value = t.value;
      o.textContent = `${t.value} — ${t.label || t.value}`;
      sel.appendChild(o);
    }
  }

  function ensureTypeOption(value) {
    const v = (value || '').trim();
    if (!v) return;
    const sel = el('device_type');
    for (const o of sel.options) {
      if (o.value === v) return;
    }
    const o = document.createElement('option');
    o.value = v;
    o.textContent = v;
    sel.appendChild(o);
  }

  function payloadFromForm() {
    return {
      serial: el('serial').value.trim(),
      device_type: (el('device_type').value || 'scanner').trim() || 'scanner',
      model: el('model').value.trim() || null,
      from_store: el('from_store').value.trim() || null,
      to_store: el('to_store').value.trim() || null,
      status: el('status').value,
      comment: el('comment').value.trim() || null,
    };
  }

  async function apiJson(url, options) {
    const res = await fetch(url, options);
    let data = null;
    try { data = await res.json(); } catch (_) { data = { ok: false, error: 'invalid json' }; }
    return { res, data };
  }

  async function refreshList() {
    const status = el('filter_status').value;
    const to_store = el('filter_to').value.trim();
    const from_store = el('filter_from').value.trim();
    const limit = el('limit').value;

    const qs = new URLSearchParams();
    if (status) qs.set('status', status);
    if (to_store) qs.set('to_store', to_store);
    if (from_store) qs.set('from_store', from_store);
    if (limit) qs.set('limit', limit);

    const { res, data } = await apiJson('/api/devices?' + qs.toString());
    if (!res.ok) {
      setResult(JSON.stringify(data, null, 2), false);
      return;
    }

    const tbody = el('tbody');
    tbody.innerHTML = '';

    const statuses = ["RECEIVED","PREPARING","PREPARED","SENT","IN_USE","RETURNED","RETIRED"];
    const statusLabel = (s) => {
      const m = {
        "RECEIVED": I18N.status_received,
        "PREPARING": I18N.status_preparing,
        "PREPARED": I18N.status_prepared,
        "SENT": I18N.status_sent,
        "IN_USE": I18N.status_in_use,
        "RETURNED": I18N.status_returned,
        "RETIRED": I18N.status_retired,
      };
      return m[s] || s;
    };

    for (const d of data.devices) {
      const tr = document.createElement('tr');

      const tdSerial = document.createElement('td');
      tdSerial.innerHTML = `<code>${escapeHtml(d.serial)}</code>`;

      const tdType = document.createElement('td');
      tdType.textContent = deviceTypeLabel(d.device_type);

      const tdModel = document.createElement('td');
      tdModel.textContent = d.model || '';

      const tdFrom = document.createElement('td');
      tdFrom.textContent = d.from_store || '';

      const tdTo = document.createElement('td');
      tdTo.textContent = d.to_store || '';

      const tdStatus = document.createElement('td');
      const rowStatus = document.createElement('select');
      rowStatus.title = I18N.web_status_inline || 'Change status';
      rowStatus.className = 'row-status';
      for (const s of statuses) {
        const o = document.createElement('option');
        o.value = s;
        o.textContent = `${s} — ${statusLabel(s)}`;
        rowStatus.appendChild(o);
      }
      rowStatus.value = d.status || 'RECEIVED';
      rowStatus.addEventListener('click', (ev) => ev.stopPropagation());
      rowStatus.addEventListener('change', async (ev) => {
        ev.stopPropagation();
        const prev = d.status;
        const next = rowStatus.value;
        const { res: r2, data: d2 } = await apiJson(
          '/api/device/' + encodeURIComponent(d.serial) + '/status',
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ new_status: next, to_store: null, comment: null }),
          }
        );
        if (!r2.ok) {
          rowStatus.value = prev || 'RECEIVED';
          setResult(JSON.stringify(d2, null, 2), false);
          return;
        }
        setResult(JSON.stringify(d2, null, 2), true);
        if (SELECTED_SERIAL === d.serial) {
          el('status').value = next;
        }
        await refreshList();
      });
      tdStatus.appendChild(rowStatus);

      const tdUpdated = document.createElement('td');
      tdUpdated.innerHTML = `<code>${escapeHtml((d.updated_at || '').replace('T',' '))}</code>`;

      const tdActions = document.createElement('td');
      const actions = document.createElement('div');
      actions.className = 'row-actions';

      const btnDelete = document.createElement('button');
      btnDelete.className = 'danger';
      btnDelete.type = 'button';
      btnDelete.textContent = I18N.web_delete_short || 'Delete';
      btnDelete.addEventListener('click', async (ev) => {
        ev.stopPropagation();
        const msg = (I18N.web_confirm_delete || 'Delete device with Serial: {serial}?').replace('{serial}', d.serial);
        if (!confirm(msg)) return;

        const { res: r3, data: d3 } = await apiJson('/api/device/' + encodeURIComponent(d.serial), { method: 'DELETE' });
        setResult(JSON.stringify(d3, null, 2), r3.ok);
        if (SELECTED_SERIAL === d.serial) {
          setSelected(null);
          el('serial').value = '';
          el('model').value = '';
          el('from_store').value = '';
          el('to_store').value = '';
          el('comment').value = '';
          el('status').value = 'RECEIVED';
          el('device_type').value = 'scanner';
        }
        await refreshList();
      });

      actions.appendChild(btnDelete);
      tdActions.appendChild(actions);

      tr.appendChild(tdSerial);
      tr.appendChild(tdType);
      tr.appendChild(tdModel);
      tr.appendChild(tdFrom);
      tr.appendChild(tdTo);
      tr.appendChild(tdStatus);
      tr.appendChild(tdUpdated);
      tr.appendChild(tdActions);

      tr.style.cursor = 'pointer';
      tr.classList.toggle('selected', SELECTED_SERIAL === d.serial);
      tr.addEventListener('click', () => {
        setSelected(d.serial);
        el('serial').value = d.serial;
        ensureTypeOption(d.device_type || 'scanner');
        el('device_type').value = d.device_type || 'scanner';
        el('model').value = d.model || '';
        el('from_store').value = d.from_store || '';
        el('to_store').value = d.to_store || '';
        el('status').value = d.status || 'RECEIVED';
        el('comment').value = d.comment || '';
        refreshList();
      });
      tbody.appendChild(tr);
    }

    el('count').textContent = (I18N.count || 'Count: {n}').replace('{n}', String(data.count));
  }

  async function doAdd() {
    const payload = payloadFromForm();
    const overwrite = el('overwrite').checked;

    const { res, data } = await apiJson('/api/device?overwrite=' + (overwrite ? '1' : '0'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    setResult(JSON.stringify(data, null, 2), res.ok);
    if (res.ok) {
      setSelected(payload.serial);
    }
    await refreshList();
  }

  async function doUpdate() {
    const p = payloadFromForm();
    const serial = p.serial;
    if (!serial) return setResult('Missing serial', false);

    const body = {
      device_type: p.device_type,
      model: p.model,
      from_store: p.from_store,
      to_store: p.to_store,
      status: p.status,
      comment: p.comment,
    };

    const { res, data } = await apiJson('/api/device/' + encodeURIComponent(serial), {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    setResult(JSON.stringify(data, null, 2), res.ok);
    if (res.ok) {
      setSelected(serial);
    }
    await refreshList();
  }

  async function doStatus() {
    const serial = el('serial').value.trim();
    const new_status = el('status').value;
    const to_store = el('to_store').value.trim() || null;
    const comment = el('comment').value.trim() || null;

    if (!serial) return setResult('Missing serial', false);

    const { res, data } = await apiJson('/api/device/' + encodeURIComponent(serial) + '/status', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ new_status, to_store, comment }),
    });
    setResult(JSON.stringify(data, null, 2), res.ok);
    if (res.ok) {
      setSelected(serial);
    }
    await refreshList();
  }

  async function doDelete() {
    const serial = el('serial').value.trim();
    if (!serial) return setResult('Missing serial', false);

    const msg = (I18N.web_confirm_delete || 'Delete device with Serial: {serial}?').replace('{serial}', serial);
    if (!confirm(msg)) return;

    const { res, data } = await apiJson('/api/device/' + encodeURIComponent(serial), { method: 'DELETE' });
    setResult(JSON.stringify(data, null, 2), res.ok);
    if (res.ok && SELECTED_SERIAL === serial) {
      setSelected(null);
    }
    await refreshList();
  }

  async function boot() {
    el('lang').addEventListener('change', async () => { await loadI18n(); await refreshList(); });
    el('btnRefresh').addEventListener('click', refreshList);
    el('btnAdd').addEventListener('click', doAdd);
    el('btnUpdate').addEventListener('click', doUpdate);
    el('btnStatus').addEventListener('click', doStatus);
    el('btnDelete').addEventListener('click', doDelete);

    await loadI18n();
    await refreshList();
    setResult('Ready');
  }

  boot();
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    db: InventoryDB
    translations: dict[str, dict[str, str]]

    def _lang(self) -> str:
        qs = parse_qs(urlparse(self.path).query)
        return (qs.get("lang", ["lv"])[0] or "lv").lower()

    def _send_html(self, html: str) -> None:
        data = html.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
      try:
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path == "/":
          return self._send_html(INDEX_HTML)

        if path == "/api/i18n":
          lang = (qs.get("lang", ["lv"])[0] or "lv").lower()
          payload = self.translations.get(lang) or self.translations.get("lv") or {}
          return _write_json(self, HTTPStatus.OK, payload)

        if path == "/api/devices":
          status = qs.get("status", [None])[0]
          to_store = qs.get("to_store", [None])[0]
          from_store = qs.get("from_store", [None])[0]
          limit_raw = qs.get("limit", ["200"])[0]
          try:
            limit = int(limit_raw)
          except Exception:
            limit = 200

          devices = self.db.list_devices(status=status, to_store=to_store, from_store=from_store, limit=limit)
          return _write_json(
            self,
            HTTPStatus.OK,
            {"devices": [_device_to_dict(d) for d in devices], "count": len(devices)},
          )

        if path.startswith("/api/device/"):
          serial = path.removeprefix("/api/device/")
          if not serial or "/" in serial:
            return _write_json(self, HTTPStatus.BAD_REQUEST, {"ok": False, "error": "invalid serial"})

          d = self.db.get_device(serial)
          if not d:
            return _write_json(self, HTTPStatus.NOT_FOUND, {"ok": False, "error": "not found"})
          return _write_json(self, HTTPStatus.OK, {"ok": True, "device": _device_to_dict(d)})

        return _write_json(self, HTTPStatus.NOT_FOUND, {"ok": False, "error": "not found"})
      except ValueError as exc:
        return _write_json(self, HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})
      except Exception as exc:  # noqa: BLE001
        return _write_json(self, HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, "error": str(exc)})

    def do_POST(self) -> None:  # noqa: N802
      try:
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path == "/api/device":
          body = _read_json(self)
          overwrite = (qs.get("overwrite", ["0"])[0] == "1")
          device = Device(
            serial=str(body.get("serial") or "").strip(),
            device_type=str(body.get("device_type") or "scanner").strip() or "scanner",
            model=(body.get("model") if body.get("model") not in ("", None) else None),
            from_store=(body.get("from_store") if body.get("from_store") not in ("", None) else None),
            to_store=(body.get("to_store") if body.get("to_store") not in ("", None) else None),
            status=str(body.get("status") or "RECEIVED").strip() or "RECEIVED",
            comment=(body.get("comment") if body.get("comment") not in ("", None) else None),
          )
          self.db.add_device(device, overwrite=overwrite)
          return _write_json(self, HTTPStatus.OK, {"ok": True})

        if path.startswith("/api/device/") and path.endswith("/status"):
          serial = path.removesuffix("/status").removeprefix("/api/device/")
          body = _read_json(self)
          new_status = str(body.get("new_status") or "").strip()
          to_store = body.get("to_store")
          comment = body.get("comment")
          changed = self.db.change_status(serial, new_status, to_store=to_store, comment=comment)
          if not changed:
            return _write_json(self, HTTPStatus.NOT_FOUND, {"ok": False, "error": "not found"})
          return _write_json(self, HTTPStatus.OK, {"ok": True})

        return _write_json(self, HTTPStatus.NOT_FOUND, {"ok": False, "error": "not found"})
      except ValueError as exc:
        return _write_json(self, HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})
      except json.JSONDecodeError:
        return _write_json(self, HTTPStatus.BAD_REQUEST, {"ok": False, "error": "invalid json"})
      except Exception as exc:  # noqa: BLE001
        return _write_json(self, HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, "error": str(exc)})

    def do_PATCH(self) -> None:  # noqa: N802
      try:
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/device/"):
          serial = path.removeprefix("/api/device/")
          if not serial or "/" in serial:
            return _write_json(self, HTTPStatus.BAD_REQUEST, {"ok": False, "error": "invalid serial"})

          body = _read_json(self)
          changed = self.db.update_device(
            serial,
            device_type=body.get("device_type"),
            model=body.get("model"),
            from_store=body.get("from_store"),
            to_store=body.get("to_store"),
            status=body.get("status"),
            comment=body.get("comment"),
          )
          if not changed:
            return _write_json(self, HTTPStatus.NOT_FOUND, {"ok": False, "error": "not found"})
          return _write_json(self, HTTPStatus.OK, {"ok": True})

        return _write_json(self, HTTPStatus.NOT_FOUND, {"ok": False, "error": "not found"})
      except ValueError as exc:
        return _write_json(self, HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})
      except json.JSONDecodeError:
        return _write_json(self, HTTPStatus.BAD_REQUEST, {"ok": False, "error": "invalid json"})
      except Exception as exc:  # noqa: BLE001
        return _write_json(self, HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, "error": str(exc)})

    def do_DELETE(self) -> None:  # noqa: N802
      try:
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/device/"):
          serial = path.removeprefix("/api/device/")
          if not serial or "/" in serial:
            return _write_json(self, HTTPStatus.BAD_REQUEST, {"ok": False, "error": "invalid serial"})
          deleted = self.db.delete_device(serial)
          if not deleted:
            return _write_json(self, HTTPStatus.NOT_FOUND, {"ok": False, "error": "not found"})
          return _write_json(self, HTTPStatus.OK, {"ok": True})

        return _write_json(self, HTTPStatus.NOT_FOUND, {"ok": False, "error": "not found"})
      except Exception as exc:  # noqa: BLE001
        return _write_json(self, HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, "error": str(exc)})

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        # Keep console quieter
        return


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Local inventory web UI (no external deps)")
    p.add_argument("--db", default="inventory.db")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    return p


def run(host: str, port: int, db_path: str) -> None:
    db = InventoryDB(Path(db_path))
    db.init_db()

    translations = load_translations()

    Handler.db = db
    Handler.translations = translations

    server = ThreadingHTTPServer((host, port), Handler)
    print(f"Web UI running: http://{host}:{port}  (DB: {db_path})")
    print(f"Allowed statuses: {sorted(ALLOWED_STATUSES)}")
    server.serve_forever()


if __name__ == "__main__":
    args = build_parser().parse_args()
    run(args.host, args.port, args.db)

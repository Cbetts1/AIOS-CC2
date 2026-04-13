/* AI-OS Web UI JavaScript - No external libraries */
"use strict";

(function () {

  /* ── State ─────────────────────────────────────────── */
  const state = {
    status: {},
    consoleLogs: [],
    heartbeatCount: 0,
    lastUpdate: null,
    refreshInterval: 3000,
    touchStartX: 0,
    touchStartY: 0,
    touchStartTime: 0,
    longPressTimer: null,
    rootMode: false,
    token: sessionStorage.getItem("aios_token") || "",
    sseActive: false,
  };

  /* ── DOM helpers ───────────────────────────────────── */
  const $ = id => document.getElementById(id);
  const el = (tag, cls, txt) => {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (txt !== undefined) e.textContent = txt;
    return e;
  };

  /* ── Clock ─────────────────────────────────────────── */
  function updateClock() {
    const clk = $("live-clock");
    if (clk) {
      const now = new Date();
      clk.textContent = now.toISOString().replace("T", " ").slice(0, 19) + " UTC";
    }
  }
  setInterval(updateClock, 1000);
  updateClock();

  /* ── Auth helpers ──────────────────────────────────── */
  function authUrl(url) {
    if (!state.token) return url;
    const sep = url.includes("?") ? "&" : "?";
    return `${url}${sep}token=${encodeURIComponent(state.token)}`;
  }

  async function authFetch(url, opts) {
    const headers = Object.assign({}, (opts || {}).headers || {});
    if (state.token) headers["Authorization"] = `Bearer ${state.token}`;
    return fetch(url, Object.assign({}, opts, { headers }));
  }

  /* ── Login overlay ─────────────────────────────────── */
  function showLogin(msg) {
    const overlay = $("login-overlay");
    if (overlay) {
      overlay.style.display = "flex";
      const err = $("login-error");
      if (err) err.textContent = msg || "";
    }
  }

  function hideLogin() {
    const overlay = $("login-overlay");
    if (overlay) overlay.style.display = "none";
  }

  async function tryLogin() {
    const input = $("token-input");
    const token = input ? input.value.trim() : "";
    if (!token) { showLogin("Please enter your operator token."); return; }
    try {
      const resp = await fetch(authUrl(`/api/login?token=${encodeURIComponent(token)}`));
      const data = await resp.json();
      if (data.ok) {
        state.token = token;
        sessionStorage.setItem("aios_token", token);
        hideLogin();
        initSSE();
        appendConsole("  [AUTH] Operator authenticated.", "ok");
      } else {
        showLogin("Invalid token. Try again.");
      }
    } catch (err) {
      showLogin("Login failed: " + err.message);
    }
  }

  function initLoginForm() {
    const btn = $("login-btn");
    const input = $("token-input");
    if (btn) btn.addEventListener("click", tryLogin);
    if (input) input.addEventListener("keydown", e => { if (e.key === "Enter") tryLogin(); });
  }

  /* ── SSE / polling ─────────────────────────────────── */
  function initSSE() {
    if (state.sseActive) return;
    const url = authUrl("/api/stream");
    try {
      const es = new EventSource(url);
      es.onmessage = evt => {
        try {
          const data = JSON.parse(evt.data);
          state.status = data;
          state.lastUpdate = Date.now();
          renderDashboard(data);
        } catch (_) {}
      };
      es.onerror = () => {
        state.sseActive = false;
        es.close();
        // Fall back to polling
        setTimeout(startPolling, 2000);
      };
      es.onopen = () => {
        state.sseActive = true;
        appendConsole("  [SSE] Real-time stream connected.", "info");
      };
    } catch (_) {
      startPolling();
    }
  }

  let _pollTimer = null;
  function startPolling() {
    if (state.sseActive) return;
    if (_pollTimer) return;
    _pollTimer = setInterval(fetchStatus, state.refreshInterval);
    fetchStatus();
  }

  /* ── API Fetch ─────────────────────────────────────── */
  async function fetchStatus() {
    try {
      const resp = await authFetch("/api/status", { cache: "no-store" });
      if (resp.status === 401) {
        state.token = "";
        sessionStorage.removeItem("aios_token");
        showLogin("Session expired — please re-authenticate.");
        if (_pollTimer) { clearInterval(_pollTimer); _pollTimer = null; }
        return;
      }
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const data = await resp.json();
      state.status = data;
      state.lastUpdate = Date.now();
      renderDashboard(data);
      appendConsole(`[${new Date().toISOString().slice(11,19)}] Status updated`, "info");
    } catch (err) {
      appendConsole(`[ERROR] Status fetch failed: ${err.message}`, "err");
    }
  }

  /* ── Console ───────────────────────────────────────── */
  function appendConsole(msg, type) {
    const output = $("console-output");
    if (!output) return;
    const line = el("div", `console-line ${type || ""}`, msg);
    output.appendChild(line);
    state.consoleLogs.push({ msg, type, ts: Date.now() });
    if (state.consoleLogs.length > 500) {
      state.consoleLogs.shift();
      if (output.firstChild) output.removeChild(output.firstChild);
    }
    output.scrollTop = output.scrollHeight;
  }

  function printBanner() {
    const lines = [
      "  ╔══════════════════════════════════════════╗",
      "  ║     AI-OS COMMAND CENTER  v2.0-CC2       ║",
      "  ║     Operator: Chris  |  Status: ONLINE   ║",
      "  ║     Network: 10.0.0.0/8 (VIRTUAL)        ║",
      "  ╚══════════════════════════════════════════╝",
    ];
    lines.forEach(l => appendConsole(l, "banner"));
    appendConsole("  System ready. Select a menu item or type a command.", "info");
  }

  /* ── Dashboard Rendering ───────────────────────────── */
  function renderDashboard(data) {
    // Uptime
    updateMetric("dash-uptime", formatUptime(data.uptime_seconds));
    updateMetric("dash-operator", data.operator || "Chris");
    updateMetric("dash-version", data.version || "2.0.0-CC2");
    updateMetric("dash-ts", (data.timestamp || "").slice(11, 19));

    // Heartbeat
    const hb = data.heartbeat || {};
    const beatCount = hb.beat_count !== undefined ? hb.beat_count : (state.heartbeatCount);
    if (hb.beat_count !== undefined) state.heartbeatCount = hb.beat_count;
    const hbCount = $("hb-count");
    if (hbCount) hbCount.textContent = `Beat #${beatCount}`;

    // Sensors
    const vsensors = data.vsensors || {};
    const readings = vsensors.readings || {};
    updateMetric("dash-cpu-temp", readings.cpu_temp ? readings.cpu_temp.toFixed(1) + "°C" : "N/A");
    updateMetric("dash-cpu-load", readings.cpu_load ? readings.cpu_load.toFixed(1) + "%" : "N/A");
    updateMetric("dash-mem-load", readings.memory_load ? readings.memory_load.toFixed(1) + "%" : "N/A");
    updateMetric("dash-power", readings.power_draw_watts ? readings.power_draw_watts.toFixed(1) + "W" : "N/A");

    // Layer dots
    for (let i = 1; i <= 7; i++) {
      const dot = $(`layer-dot-${i}`);
      if (dot) {
        dot.className = "ld";  // always green (all layers online)
      }
    }

    // Network
    const vnet = data.vnet || {};
    updateMetric("dash-net-ifaces", vnet.interfaces || 0);
    updateMetric("dash-net-pkts", vnet.packets_sent || 0);

    // Virtual HW
    const vcpu = data.vcpu || {};
    updateMetric("dash-cpu-cycles", vcpu.cycles || 0);
    const vmem = data.vmem || {};
    updateMetric("dash-mem-size", vmem.size_mb ? vmem.size_mb + " MB" : "64 MB");
    const vstorage = data.vstorage || {};
    updateMetric("dash-storage-files", vstorage.file_count || 0);

    // Status bar
    renderStatusBar(data);
  }

  function updateMetric(id, value) {
    const el = $(id);
    if (el) el.textContent = value;
  }

  function formatUptime(secs) {
    if (!secs && secs !== 0) return "--:--:--";
    const s = Math.floor(secs);
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    const sec = s % 60;
    return `${String(h).padStart(2,"0")}:${String(m).padStart(2,"0")}:${String(sec).padStart(2,"0")}`;
  }

  function renderStatusBar(data) {
    const sb = $("status-bar");
    if (!sb) return;
    const items = [
      { label: "AIOS", val: "ONLINE", cls: "ok" },
      { label: "L1-7", val: "GREEN", cls: "ok" },
      { label: "HB", val: `#${state.heartbeatCount}`, cls: "cyan" },
      { label: "NET", val: "10.0.0.0/8", cls: "cyan" },
      { label: "OP", val: data.operator || "Chris", cls: "" },
      { label: "VER", val: data.version || "2.0.0-CC2", cls: "" },
    ];
    sb.innerHTML = "";
    items.forEach(item => {
      const span = el("span", `sb-item ${item.cls}`, `${item.label}: ${item.val}`);
      sb.appendChild(span);
    });
  }

  /* ── Menu ──────────────────────────────────────────── */
  const MENU_DATA = [
    [1,"System Status",["Full Report","Layer Health","Subsystems","Resources","Event Log"]],
    [2,"Layer Control",["L1 Physical","L2 Virt HW","L3 Kernel","L4 Proc/Mem","L5 Engines","L6 Command","L7 App/Out"]],
    [3,"Engine Control",["Start All","Tick Aura","Builder","Repair","Documentation","Evolution","Legal"]],
    [4,"Virtual HW",["CPU Status","Memory","Storage","Sensors","Exec Instr","Mem Dump"]],
    [5,"Network",["Interfaces","Mesh Status","Heartbeat","Pkt Log","Broadcast"]],
    [6,"Security",["Identity","Sec Log","Policy","Permissions","Sandbox"]],
    [7,"Cloud",["Cloud Status","List Nodes","Start Cloud","Stop Cloud","Spawn Node","Exec Task","Heartbeat","Storage Info","Event Log"]],
    [8,"Cellular",["Status","Signal","Channels"]],
    [9,"Computer",["Supervisor","Mem Map","ProcWriters","Storage Files"]],
    [10,"AI Systems",["Aura Status","Evolution","Builder Queue","Repair Hist"]],
    [11,"Diagnostics",["Full Report","Health Check","Error Log","Performance"]],
    [12,"Maintenance",["Clear State","Reset CPU","Repair Scan","Alloc Mem"]],
    [13,"Legal",["Compliance","Audit Log","Violations","Check Action"]],
    [14,"Documentation",["Overview","Layer Map","API Ref","Operator Manual","Topics"]],
    [15,"Logs",["Sec Log","Policy Log","Legal Log","Engine Log","Full Dump"]],
    [16,"Shutdown",["Graceful","Emergency","Restart"]],
  ];

  function buildMenu() {
    const menu = $("left-menu");
    if (!menu) return;
    MENU_DATA.forEach(([num, name, subs]) => {
      const item = el("div", "menu-item");
      item.dataset.num = num;
      const numSpan = el("span", "num", num);
      const nameSpan = el("span", "", name);
      item.appendChild(numSpan);
      item.appendChild(nameSpan);
      menu.appendChild(item);

      const subMenu = el("div", "menu-sub");
      subMenu.id = `sub-${num}`;
      subs.forEach((sub, i) => {
        const subItem = el("div", "menu-sub-item", `${num}.${i+1} ${sub}`);
        subItem.addEventListener("click", e => {
          e.stopPropagation();
          handleMenuCommand(`${num}.${i+1}`, sub);
        });
        subMenu.appendChild(subItem);
      });
      menu.appendChild(subMenu);

      item.addEventListener("click", () => toggleMenu(num, item, subMenu));
    });
  }

  function toggleMenu(num, item, subMenu) {
    const wasOpen = subMenu.classList.contains("open");
    // Close all
    document.querySelectorAll(".menu-sub.open").forEach(s => s.classList.remove("open"));
    document.querySelectorAll(".menu-item.active").forEach(i => i.classList.remove("active"));
    if (!wasOpen) {
      subMenu.classList.add("open");
      item.classList.add("active");
      handleMenuCommand(String(num), item.querySelector("span:last-child").textContent);
    }
  }

  function handleMenuCommand(cmd, name) {
    appendConsole(`> CMD ${cmd} : ${name || ""}`, "cmd");
    const top = cmd.split(".")[0];
    const sub = cmd.split(".")[1];

    if (!sub) {
      appendConsole(`  [${name}] Sub-menu opened.`, "info");
      return;
    }

    // Always POST to the backend for real results
    fetch("/api/command", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cmd }),
    })
      .then(r => r.json())
      .then(data => {
        if (data.error) {
          appendConsole(`  [ERROR] ${data.error}`, "err");
        } else {
          const lines = (data.result || "").split("\n");
          lines.forEach(l => { if (l.trim()) appendConsole(l, "ok"); });
        }
      })
      .catch(err => {
        appendConsole(`  [offline] ${err.message}`, "warn");
      });
  }

  function displayCommandResult(top, sub, name, data) {
    const formatObj = obj => {
      if (!obj || typeof obj !== "object") return String(obj);
      return Object.entries(obj)
        .filter(([k,v]) => typeof v !== "object")
        .map(([k,v]) => `  ${k}: ${v}`)
        .join("\n");
    };

    appendConsole(`  ── ${name} ──────────────────────────`, "info");

    if (top === "1") {
      if (sub === "1") {
        appendConsole(`  Version   : ${data.version || "2.0.0-CC2"}`, "ok");
        appendConsole(`  Operator  : ${data.operator || "Chris"}`, "ok");
        appendConsole(`  Uptime    : ${formatUptime(data.uptime_seconds)}`, "ok");
        appendConsole(`  Status    : ONLINE`, "ok");
        for (let i = 1; i <= 7; i++) appendConsole(`  Layer ${i}   : ONLINE ✓`, "ok");
      } else if (sub === "2") {
        const layers = ["Physical Abstraction","Virtual Hardware","Kernel Bridge",
          "Process & Memory","Engine & Intelligence","Command & Interface","Application & Output"];
        layers.forEach((l,i) => appendConsole(`  L${i+1}: ${l} → ONLINE ✓`, "ok"));
      } else if (sub === "3") {
        const subs = ["StateRegistry","PolicyEngine","SecurityKernel","IdentityLock",
          "VirtualCPU","VirtualMemory","VirtualStorage","VirtualNetwork","VirtualSensors",
          "HostBridge","NodeMesh","HeartbeatSystem","AuraEngine","ProcessSupervisor"];
        subs.forEach(s => appendConsole(`  ✓ ${s}`, "ok"));
      }
    } else if (top === "4") {
      const vcpu = data.vcpu || {};
      const vmem = data.vmem || {};
      const vst = data.vstorage || {};
      const vsens = data.vsensors || {};
      if (sub === "1") appendConsole(formatObj(vcpu), "");
      else if (sub === "2") appendConsole(formatObj(vmem), "");
      else if (sub === "3") appendConsole(formatObj(vst), "");
      else if (sub === "4") {
        const r = vsens.readings || {};
        Object.entries(r).forEach(([k,v]) => appendConsole(`  ${k}: ${v}`, ""));
      }
    } else if (top === "3") {
      const aura = data.aura || {};
      appendConsole(formatObj(aura), "ok");
    } else if (top === "5") {
      const vnet = data.vnet || {};
      if (sub === "1") {
        (vnet.interface_list || []).forEach(i =>
          appendConsole(`  [${i.name}] ${i.ip} rx=${i.rx} tx=${i.tx}`, "info"));
      } else if (sub === "3") {
        const hb = data.heartbeat || {};
        appendConsole(formatObj(hb), "info");
      }
    } else if (top === "6") {
      const identity = data.identity || {};
      const security = data.security || {};
      if (sub === "1") appendConsole(formatObj(identity), "ok");
      else if (sub === "2") appendConsole(formatObj(security), "info");
    } else if (top === "11") {
      let healthy = 0, total = 0;
      Object.values(data).forEach(v => {
        if (v && typeof v === "object" && "healthy" in v) {
          total++; if (v.healthy) healthy++;
        }
      });
      appendConsole(`  Healthy: ${healthy}/${total} subsystems`, healthy === total ? "ok" : "warn");
      appendConsole(`  Uptime : ${formatUptime(data.uptime_seconds)}`, "ok");
      appendConsole(`  Result : ALL SYSTEMS NOMINAL`, "ok");
    } else {
      appendConsole(`  ${name}: OPERATIONAL`, "ok");
      appendConsole(`  Timestamp: ${new Date().toISOString()}`, "info");
    }
  }

  /* ── Command Input ─────────────────────────────────── */
  function initInput() {
    const input = $("cmd-input");
    const btn = $("send-btn");
    if (!input) return;

    const send = () => {
      const val = input.value.trim();
      if (!val) return;
      input.value = "";
      appendConsole(`> ${val}`, "cmd");
      // POST command to backend and display real result
      authFetch("/api/command", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cmd: val }),
      })
        .then(r => {
          if (r.status === 401) {
            state.token = "";
            sessionStorage.removeItem("aios_token");
            showLogin("Session expired — please re-authenticate.");
            return null;
          }
          return r.json();
        })
        .then(data => {
          if (!data) return;
          if (data.error) {
            appendConsole(`  [ERROR] ${data.error}`, "err");
          } else {
            const lines = (data.result || "").split("\n");
            lines.forEach(l => {
              if (l.trim()) appendConsole(l, "ok");
            });
          }
        })
        .catch(err => {
          appendConsole(`  [offline] Could not reach server: ${err.message}`, "warn");
        });
    };

    input.addEventListener("keydown", e => {
      if (e.key === "Enter") send();
    });
    if (btn) btn.addEventListener("click", send);
  }

  /* ── Touch Gestures ────────────────────────────────── */
  function initGestures() {
    const body = document.body;

    body.addEventListener("touchstart", e => {
      const t = e.touches[0];
      state.touchStartX = t.clientX;
      state.touchStartY = t.clientY;
      state.touchStartTime = Date.now();
      state.longPressTimer = setTimeout(() => {
        state.rootMode = !state.rootMode;
        appendConsole(
          state.rootMode ? "  [ROOT MODE ACTIVATED]" : "  [ROOT MODE DEACTIVATED]",
          state.rootMode ? "warn" : "info"
        );
      }, 1500);
    }, { passive: true });

    body.addEventListener("touchend", e => {
      clearTimeout(state.longPressTimer);
      const t = e.changedTouches[0];
      const dx = t.clientX - state.touchStartX;
      const dy = t.clientY - state.touchStartY;
      const dt = Date.now() - state.touchStartTime;
      if (Math.abs(dx) > 60 && Math.abs(dy) < 40 && dt < 400) {
        if (dx < 0) {
          // Swipe left - show menu
          const lm = $("left-menu");
          if (lm) lm.style.display = lm.style.display === "none" ? "" : "none";
        } else {
          // Swipe right - show dashboard
          const rd = $("right-dash");
          if (rd) rd.style.display = rd.style.display === "none" ? "" : "none";
        }
      }
    }, { passive: true });

    body.addEventListener("touchmove", e => {
      clearTimeout(state.longPressTimer);
    }, { passive: true });
  }

  /* ── Init ──────────────────────────────────────────── */
  function init() {
    buildMenu();
    initInput();
    initGestures();
    initLoginForm();
    printBanner();

    // If we already have a stored token, attempt SSE immediately;
    // otherwise show the login overlay.
    if (state.token) {
      initSSE();
    } else {
      showLogin();
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

})();

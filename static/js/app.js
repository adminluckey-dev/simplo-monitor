(() => {
  const PAGE_SIZE = 24;
  const state = {
    devices: [],
    events: [],
    meta: {},
    summary: {},
    filter: "all",
    sort: "priority",
    page: 1,
    selectedId: null,
    view: "dashboard",
    user: null,
    menuOptions: [],
    report: { logs: [], devices: [], filters: {} },
    statistik: { summary: {}, daily: [], timeline: [], devices: [], per_device: [], filters: {} },
  };

  const el = {
    siteName: document.getElementById("siteName"),
    siteSite: document.getElementById("siteSite"),
    siteOrg: document.getElementById("siteOrg"),
    pageTitle: document.getElementById("pageTitle"),
    liveClock: document.getElementById("liveClock"),
    errorBanner: document.getElementById("errorBanner"),
    viewDashboard: document.getElementById("viewDashboard"),
    viewReport: document.getElementById("viewReport"),
    viewStatistik: document.getElementById("viewStatistik"),
    viewNotify: document.getElementById("viewNotify"),
    viewAssets: document.getElementById("viewAssets"),
    viewTeam: document.getElementById("viewTeam"),
    viewWo: document.getElementById("viewWo"),
    viewPm: document.getElementById("viewPm"),
    viewUsers: document.getElementById("viewUsers"),
    userAvatar: document.getElementById("userAvatar"),
    userRoleLabel: document.getElementById("userRoleLabel"),
    btnLogout: document.getElementById("btnLogout"),
    userBody: document.getElementById("userBody"),
    userSummary: document.getElementById("userSummary"),
    btnNewUser: document.getElementById("btnNewUser"),
    userModal: document.getElementById("userModal"),
    userEditId: document.getElementById("userEditId"),
    userFormTitle: document.getElementById("userFormTitle"),
    userUsername: document.getElementById("userUsername"),
    userFullName: document.getElementById("userFullName"),
    userPassword: document.getElementById("userPassword"),
    userRole: document.getElementById("userRole"),
    userMenuBox: document.getElementById("userMenuBox"),
    userMenuOptions: document.getElementById("userMenuOptions"),
    userActive: document.getElementById("userActive"),
    btnSaveUser: document.getElementById("btnSaveUser"),
    userSaveMsg: document.getElementById("userSaveMsg"),
    woBody: document.getElementById("woBody"),
    woSummary: document.getElementById("woSummary"),
    btnNewWo: document.getElementById("btnNewWo"),
    woModal: document.getElementById("woModal"),
    woFormTitle: document.getElementById("woFormTitle"),
    woDate: document.getElementById("woDate"),
    woTime: document.getElementById("woTime"),
    woCategory: document.getElementById("woCategory"),
    woNotes: document.getElementById("woNotes"),
    woAsset: document.getElementById("woAsset"),
    woTech: document.getElementById("woTech"),
    btnSaveWo: document.getElementById("btnSaveWo"),
    woSaveMsg: document.getElementById("woSaveMsg"),
    woAutoMinutes: document.getElementById("woAutoMinutes"),
    woAutoCooldown: document.getElementById("woAutoCooldown"),
    btnSaveWoAuto: document.getElementById("btnSaveWoAuto"),
    woAutoMsg: document.getElementById("woAutoMsg"),
    pmBody: document.getElementById("pmBody"),
    pmSummary: document.getElementById("pmSummary"),
    btnNewPm: document.getElementById("btnNewPm"),
    pmModal: document.getElementById("pmModal"),
    pmEditId: document.getElementById("pmEditId"),
    pmFormTitle: document.getElementById("pmFormTitle"),
    pmAsset: document.getElementById("pmAsset"),
    pmInterval: document.getElementById("pmInterval"),
    pmCustomDaysWrap: document.getElementById("pmCustomDaysWrap"),
    pmCustomDays: document.getElementById("pmCustomDays"),
    pmNextDue: document.getElementById("pmNextDue"),
    pmActive: document.getElementById("pmActive"),
    pmNotes: document.getElementById("pmNotes"),
    btnSavePm: document.getElementById("btnSavePm"),
    pmSaveMsg: document.getElementById("pmSaveMsg"),
    pmDetailModal: document.getElementById("pmDetailModal"),
    pmDetailTitle: document.getElementById("pmDetailTitle"),
    pmDetailSub: document.getElementById("pmDetailSub"),
    pmDetailMeta: document.getElementById("pmDetailMeta"),
    pmRecordDate: document.getElementById("pmRecordDate"),
    pmRecordTech: document.getElementById("pmRecordTech"),
    pmRecordNotes: document.getElementById("pmRecordNotes"),
    btnSavePmRecord: document.getElementById("btnSavePmRecord"),
    pmRecordMsg: document.getElementById("pmRecordMsg"),
    pmRecordsBody: document.getElementById("pmRecordsBody"),
    techBody: document.getElementById("techBody"),
    techSummary: document.getElementById("techSummary"),
    btnNewTech: document.getElementById("btnNewTech"),
    techModal: document.getElementById("techModal"),
    techEditId: document.getElementById("techEditId"),
    techFormTitle: document.getElementById("techFormTitle"),
    techName: document.getElementById("techName"),
    techPhone: document.getElementById("techPhone"),
    techEmail: document.getElementById("techEmail"),
    techTelegram: document.getElementById("techTelegram"),
    techSkillOptions: document.getElementById("techSkillOptions"),
    btnSaveTech: document.getElementById("btnSaveTech"),
    techSaveMsg: document.getElementById("techSaveMsg"),
    assetsBody: document.getElementById("assetsBody"),
    assetsSummary: document.getElementById("assetsSummary"),
    btnImportAssets: document.getElementById("btnImportAssets"),
    btnNewAsset: document.getElementById("btnNewAsset"),
    assetModal: document.getElementById("assetModal"),
    assetEditId: document.getElementById("assetEditId"),
    assetFormTitle: document.getElementById("assetFormTitle"),
    assetName: document.getElementById("assetName"),
    assetCategory: document.getElementById("assetCategory"),
    assetLocation: document.getElementById("assetLocation"),
    assetIp: document.getElementById("assetIp"),
    assetLocDetail: document.getElementById("assetLocDetail"),
    assetVendor: document.getElementById("assetVendor"),
    assetModel: document.getElementById("assetModel"),
    assetMac: document.getElementById("assetMac"),
    assetInstallDate: document.getElementById("assetInstallDate"),
    assetWarrantyEnd: document.getElementById("assetWarrantyEnd"),
    assetMaintenanceEnd: document.getElementById("assetMaintenanceEnd"),
    btnSaveAsset: document.getElementById("btnSaveAsset"),
    assetSaveMsg: document.getElementById("assetSaveMsg"),
    detailCategory: document.getElementById("detailCategory"),
    detailLocDetail: document.getElementById("detailLocDetail"),
    detailInstallDate: document.getElementById("detailInstallDate"),
    detailWarrantyStatus: document.getElementById("detailWarrantyStatus"),
    detailWarrantyEnd: document.getElementById("detailWarrantyEnd"),
    detailMaintenanceStatus: document.getElementById("detailMaintenanceStatus"),
    detailMaintenanceEnd: document.getElementById("detailMaintenanceEnd"),
    emailEnabled: document.getElementById("emailEnabled"),
    emailSmtpHost: document.getElementById("emailSmtpHost"),
    emailSmtpPort: document.getElementById("emailSmtpPort"),
    emailSmtpUser: document.getElementById("emailSmtpUser"),
    emailSmtpPassword: document.getElementById("emailSmtpPassword"),
    emailFromName: document.getElementById("emailFromName"),
    emailFromEmail: document.getElementById("emailFromEmail"),
    emailTo: document.getElementById("emailTo"),
    btnSaveEmail: document.getElementById("btnSaveEmail"),
    btnTestEmail: document.getElementById("btnTestEmail"),
    emailSaveMsg: document.getElementById("emailSaveMsg"),
    tgEnabled: document.getElementById("tgEnabled"),
    tgBotToken: document.getElementById("tgBotToken"),
    tgChatIds: document.getElementById("tgChatIds"),
    btnSaveTelegram: document.getElementById("btnSaveTelegram"),
    btnTestTelegram: document.getElementById("btnTestTelegram"),
    tgSaveMsg: document.getElementById("tgSaveMsg"),
    statTotal: document.getElementById("statTotal"),
    statHealthy: document.getElementById("statHealthy"),
    statHealthyPct: document.getElementById("statHealthyPct"),
    statAttention: document.getElementById("statAttention"),
    statIssue: document.getElementById("statIssue"),
    statIssueSub: document.getElementById("statIssueSub"),
    deviceGrid: document.getElementById("deviceGrid"),
    pageInfo: document.getElementById("pageInfo"),
    pager: document.getElementById("pager"),
    detailEmpty: document.getElementById("detailEmpty"),
    detailBody: document.getElementById("detailBody"),
    detailBadge: document.getElementById("detailBadge"),
    detailName: document.getElementById("detailName"),
    detailModel: document.getElementById("detailModel"),
    detailConn: document.getElementById("detailConn"),
    detailRec: document.getElementById("detailRec"),
    detailRecLabel: document.getElementById("detailRecLabel"),
    detailLoc: document.getElementById("detailLoc"),
    detailIp: document.getElementById("detailIp"),
    detailDirectIp: document.getElementById("detailDirectIp"),
    detailDirectIpRow: document.getElementById("detailDirectIpRow"),
    detailVendor: document.getElementById("detailVendor"),
    detailMac: document.getElementById("detailMac"),
    detailSched: document.getElementById("detailSched"),
    detailSchedLabel: document.getElementById("detailSchedLabel"),
    detailRouterExtra: document.getElementById("detailRouterExtra"),
    detailRouterInfo: document.getElementById("detailRouterInfo"),
    detailUptimePct: document.getElementById("detailUptimePct"),
    detailUptimeBar: document.getElementById("detailUptimeBar"),
    detailTimeline: document.getElementById("detailTimeline"),
    btnNx: document.getElementById("btnNx"),
    btnRefreshOne: document.getElementById("btnRefreshOne"),
    btnWall: document.getElementById("btnWall"),
    sortBy: document.getElementById("sortBy"),
    filters: document.getElementById("filters"),
    reportFrom: document.getElementById("reportFrom"),
    reportTo: document.getElementById("reportTo"),
    reportDevice: document.getElementById("reportDevice"),
    reportBody: document.getElementById("reportBody"),
    reportSummary: document.getElementById("reportSummary"),
    btnReportApply: document.getElementById("btnReportApply"),
    btnExportPdf: document.getElementById("btnExportPdf"),
    statFrom: document.getElementById("statFrom"),
    statTo: document.getElementById("statTo"),
    statDevice: document.getElementById("statDevice"),
    btnStatApply: document.getElementById("btnStatApply"),
    kpiHealthyPct: document.getElementById("kpiHealthyPct"),
    kpiHealthySub: document.getElementById("kpiHealthySub"),
    kpiUptimePct: document.getElementById("kpiUptimePct"),
    kpiDowntimePct: document.getElementById("kpiDowntimePct"),
    kpiDowntimeSub: document.getElementById("kpiDowntimeSub"),
    kpiDeviceCount: document.getElementById("kpiDeviceCount"),
    kpiRangeLabel: document.getElementById("kpiRangeLabel"),
    statTimelineRibbon: document.getElementById("statTimelineRibbon"),
    statTimelineAxis: document.getElementById("statTimelineAxis"),
    statDailyChart: document.getElementById("statDailyChart"),
    statSummary: document.getElementById("statSummary"),
    statDeviceBody: document.getElementById("statDeviceBody"),
  };

  const healthLabel = {
    healthy: "Sehat",
    attention: "Perlu perhatian",
    issue: "Gangguan",
  };

  const priorityRank = { issue: 0, attention: 1, healthy: 2 };

  function formatClock(iso) {
    const d = iso ? new Date(iso) : new Date();
    if (Number.isNaN(d.getTime())) return new Date().toLocaleString("id-ID");
    return d.toLocaleString("id-ID", {
      weekday: "short",
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    });
  }

  function tickClock() {
    el.liveClock.textContent = formatClock();
  }

  function filteredDevices() {
    let list = [...state.devices];
    const f = state.filter;
    if (f === "issue" || f === "attention" || f === "healthy") {
      list = list.filter((d) => d.health === f);
    } else if (f === "recording") {
      list = list.filter((d) => d.recording);
    } else if (f === "CCTV" || f === "Access" || f === "Alarm" || f === "Network") {
      list = list.filter((d) => d.type === f);
    }

    if (state.sort === "name") {
      list.sort((a, b) => a.name.localeCompare(b.name, "id"));
    } else if (state.sort === "status") {
      list.sort((a, b) => a.status_raw.localeCompare(b.status_raw));
    } else {
      list.sort((a, b) => {
        const pr = priorityRank[a.health] - priorityRank[b.health];
        if (pr !== 0) return pr;
        return a.name.localeCompare(b.name, "id");
      });
    }
    return list;
  }

  function renderStats() {
    const s = state.summary || {};
    el.statTotal.textContent = s.total ?? 0;
    el.statHealthy.textContent = s.healthy ?? 0;
    el.statHealthyPct.textContent = `${s.healthy_pct ?? 0}%`;
    el.statAttention.textContent = s.attention ?? 0;
    el.statIssue.textContent = s.issue ?? 0;
    el.statIssueSub.textContent = `${s.issue ?? s.offline ?? 0} offline`;
  }

  function renderMeta() {
    const m = state.meta || {};
    if (m.site_name) el.siteName.textContent = m.site_name;
    if (m.site_site) el.siteSite.textContent = m.site_site;
    // #siteOrg menampilkan user login, bukan site_org
    tickClock();

    if (m.error) {
      el.errorBanner.hidden = false;
      el.errorBanner.textContent = m.error;
    } else {
      el.errorBanner.hidden = true;
    }
  }

  function cardBadgeHtml(d) {
    const isNet = d.type === "Network" || d.server_id === "router";
    if (isNet) {
      if (d.internet_ok || d.recording) return `<span class="rec-badge net">NET</span>`;
      if (d.online) return `<span class="rec-badge off">NO WAN</span>`;
      return "";
    }
    if (d.recording) return `<span class="rec-badge">REC</span>`;
    if (d.health === "healthy") return `<span class="dot" title="Online"></span>`;
    if (d.online) return `<span class="rec-badge off">NO REC</span>`;
    return "";
  }

  function syncCardBadge(card, badgeHtml) {
    const oldBadge = card.querySelector(":scope > .rec-badge, :scope > .dot");
    if (!badgeHtml) {
      if (oldBadge) oldBadge.remove();
      return;
    }
    const wrap = document.createElement("div");
    wrap.innerHTML = badgeHtml;
    const next = wrap.firstElementChild;
    if (!next) return;
    if (!oldBadge) {
      card.insertBefore(next, card.firstChild);
      return;
    }
    if (
      oldBadge.className !== next.className ||
      oldBadge.textContent !== next.textContent ||
      oldBadge.getAttribute("title") !== next.getAttribute("title")
    ) {
      oldBadge.replaceWith(next);
    }
  }

  function renderGrid() {
    const list = filteredDevices();
    const pages = Math.max(1, Math.ceil(list.length / PAGE_SIZE));
    if (state.page > pages) state.page = pages;
    const start = (state.page - 1) * PAGE_SIZE;
    const slice = list.slice(start, start + PAGE_SIZE);
    const wanted = new Set(slice.map((d) => d.id));

    // Remove cards that are no longer on this page (avoid full innerHTML wipe).
    Array.from(el.deviceGrid.children).forEach((node) => {
      if (!wanted.has(node.dataset.id)) node.remove();
    });

    const cardsById = new Map(
      Array.from(el.deviceGrid.children).map((node) => [node.dataset.id, node])
    );

    slice.forEach((d, index) => {
      let card = cardsById.get(d.id);
      const selected = d.id === state.selectedId ? "selected" : "";
      const nextClass = `device-card ${d.health}${selected ? ` ${selected}` : ""}`;
      const locText = d.location || d.ip || "—";

      if (!card) {
        card = document.createElement("article");
        card.dataset.id = d.id;
        card.innerHTML = `<div class="name"></div><div class="loc"></div>`;
        card.className = `${nextClass} device-card-enter`;
        card.addEventListener(
          "animationend",
          () => card.classList.remove("device-card-enter"),
          { once: true }
        );
        cardsById.set(d.id, card);
      } else {
        const keepEnter = card.classList.contains("device-card-enter");
        if (card.className !== (keepEnter ? `${nextClass} device-card-enter` : nextClass)) {
          card.className = keepEnter ? `${nextClass} device-card-enter` : nextClass;
        }
      }

      if (card.title !== (d.status_raw || "")) card.title = d.status_raw || "";
      const nameEl = card.querySelector(".name");
      const locEl = card.querySelector(".loc");
      if (nameEl && nameEl.textContent !== d.name) nameEl.textContent = d.name;
      if (locEl && locEl.textContent !== locText) locEl.textContent = locText;
      syncCardBadge(card, cardBadgeHtml(d));

      const ref = el.deviceGrid.children[index];
      if (ref !== card) el.deviceGrid.insertBefore(card, ref || null);
    });

    const infoText = list.length
      ? `Menampilkan ${start + 1}–${Math.min(start + PAGE_SIZE, list.length)} dari ${list.length} perangkat`
      : "Tidak ada perangkat";
    if (el.pageInfo.textContent !== infoText) el.pageInfo.textContent = infoText;

    const buttons = [];
    buttons.push(`<button type="button" data-page="prev" ${state.page <= 1 ? "disabled" : ""}>&lt;</button>`);
    for (let i = 1; i <= pages && i <= 7; i++) {
      buttons.push(
        `<button type="button" data-page="${i}" class="${i === state.page ? "active" : ""}">${i}</button>`
      );
    }
    buttons.push(
      `<button type="button" data-page="next" ${state.page >= pages ? "disabled" : ""}>&gt;</button>`
    );
    const pagerHtml = buttons.join("");
    if (el.pager.dataset.sig !== pagerHtml) {
      el.pager.dataset.sig = pagerHtml;
      el.pager.innerHTML = pagerHtml;
    }
  }

  function contractStatusLabel(status) {
    if (status === "active") return { text: "Aktif", cls: "ok" };
    if (status === "expired") return { text: "Tidak aktif", cls: "danger" };
    return { text: "Belum diisi", cls: "muted" };
  }

  function computeDateStatus(endDate) {
    if (!endDate) return "unset";
    const end = new Date(`${endDate}T00:00:00`);
    if (Number.isNaN(end.getTime())) return "unset";
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return end >= today ? "active" : "expired";
  }

  function paintMetaStatus(badgeEl, status) {
    if (!badgeEl) return;
    const info = contractStatusLabel(status);
    badgeEl.textContent = info.text;
    badgeEl.className = `meta-status-badge ${info.cls}`;
  }

  function formatDateId(value) {
    if (!value) return "—";
    const d = new Date(`${value}T00:00:00`);
    if (Number.isNaN(d.getTime())) return value;
    return d.toLocaleDateString("id-ID", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  }

  function fillDeviceMetaReadonly(d) {
    if (el.detailCategory) el.detailCategory.textContent = d.category || d.type || "—";
    if (el.detailLocDetail) el.detailLocDetail.textContent = d.location_detail || "—";
    if (el.detailInstallDate) el.detailInstallDate.textContent = formatDateId(d.installation_date);
    paintMetaStatus(
      el.detailWarrantyStatus,
      d.warranty_status || computeDateStatus(d.warranty_end_date)
    );
    paintMetaStatus(
      el.detailMaintenanceStatus,
      d.maintenance_status || computeDateStatus(d.maintenance_end_date)
    );
    if (el.detailWarrantyEnd) {
      el.detailWarrantyEnd.textContent = d.warranty_end_date
        ? `s/d ${formatDateId(d.warranty_end_date)}`
        : "—";
    }
    if (el.detailMaintenanceEnd) {
      el.detailMaintenanceEnd.textContent = d.maintenance_end_date
        ? `s/d ${formatDateId(d.maintenance_end_date)}`
        : "—";
    }
  }

  function renderDetail() {
    const d = state.devices.find((x) => x.id === state.selectedId);
    if (!d) {
      el.detailEmpty.hidden = false;
      el.detailBody.hidden = true;
      return;
    }
    el.detailEmpty.hidden = true;
    el.detailBody.hidden = false;

    const isNet = d.type === "Network" || d.server_id === "router";
    const r = d.router || {};

    el.detailBadge.textContent = healthLabel[d.health] || d.status_raw;
    el.detailBadge.className = `badge ${d.health}`;
    el.detailName.textContent = d.name;
    el.detailModel.textContent = [
      d.type,
      [d.vendor, d.model].filter(Boolean).join(" ") || (isNet ? "WiFi Router" : "Kamera IP"),
    ]
      .filter(Boolean)
      .join(" · ");

    el.detailConn.textContent = d.online ? `Online (${d.status_raw})` : `Offline (${d.status_raw})`;
    el.detailConn.className = d.online ? "ok" : "danger";

    if (el.detailRecLabel) {
      el.detailRecLabel.textContent = isNet ? "Koneksi internet" : "Recording";
    }
    if (isNet) {
      const inetOk = !!(d.internet_ok || d.recording);
      const lat = r.internet_latency_ms != null ? ` · ${r.internet_latency_ms} ms` : "";
      el.detailRec.textContent = inetOk
        ? `Terhubung${lat}`
        : r.internet_icmp_ok
          ? "ICMP OK, DNS gagal"
          : "Terputus";
      el.detailRec.className = inetOk ? "ok" : "danger";
    } else {
      el.detailRec.textContent = d.recording ? "Aktif merekam" : "Tidak merekam";
      el.detailRec.className = d.recording ? "ok" : d.online ? "warn" : "danger";
    }

    el.detailLoc.textContent = d.location || "—";
    el.detailIp.textContent = d.ip || "—";
    if (el.detailDirectIpRow && el.detailDirectIp) {
      const isCctv = (d.category || d.type) === "CCTV";
      const dip = d.direct_ip;
      el.detailDirectIpRow.hidden = !isCctv;
      if (isCctv && dip) {
        if (dip.reachable) {
          const port = dip.port != null ? ` · port ${dip.port}` : "";
          const lat = dip.latency_ms != null ? ` · ${dip.latency_ms} ms` : "";
          el.detailDirectIp.textContent = `Reachable${port}${lat}`;
          el.detailDirectIp.className = "ok";
        } else {
          el.detailDirectIp.textContent = "Tidak terjangkau (TCP)";
          el.detailDirectIp.className = "danger";
        }
      } else if (isCctv) {
        el.detailDirectIp.textContent = d.ip ? "Belum diprobe" : "IP belum diisi";
        el.detailDirectIp.className = "warn";
      }
    }
    el.detailVendor.textContent = [d.vendor, d.model].filter(Boolean).join(" / ") || "—";
    el.detailMac.textContent = d.mac || "—";

    if (el.detailSchedLabel) {
      el.detailSchedLabel.textContent = isNet ? "UI Admin / SSID" : "Jadwal rekam";
    }
    if (isNet) {
      const ui = r.http_ok ? "UI OK" : "UI Down";
      const ssid = r.ssid ? ` · SSID ${r.ssid}` : "";
      el.detailSched.textContent = `${ui}${ssid}`;
      el.detailSched.className = r.http_ok ? "ok" : "warn";
    } else {
      el.detailSched.textContent = d.schedule_enabled ? "Aktif" : "Nonaktif";
      el.detailSched.className = d.schedule_enabled ? "ok" : "warn";
    }

    if (el.detailRouterExtra && el.detailRouterInfo) {
      if (isNet) {
        el.detailRouterExtra.hidden = false;
        el.detailRouterExtra.removeAttribute("hidden");

        const fmtMs = (v) => {
          const n = Number(v);
          if (!Number.isFinite(n)) return String(v);
          return `${n.toLocaleString("id-ID", {
            minimumFractionDigits: 0,
            maximumFractionDigits: 3,
          })} ms`;
        };
        const rows = [];
        const add = (label, value) => {
          if (value === undefined || value === null || value === "") return;
          rows.push([label, String(value)]);
        };

        add("API login", r.api_ok ? "OK" : r.api_error ? `Gagal (${r.api_error})` : "Tidak");
        if (r.ping_ms != null) add("Ping GW", fmtMs(r.ping_ms));
        if (r.internet_latency_ms != null) add("Ping internet", fmtMs(r.internet_latency_ms));
        add("Internet", r.internet_ok ? "Terhubung" : "Terputus");
        add("DNS", r.internet_dns_ok ? "OK" : "Gagal");
        add("HTTP UI", r.http_ok ? `OK (${r.http_status || 200})` : "Down");
        if (r.http_latency_ms != null) add("Latency UI", fmtMs(r.http_latency_ms));
        if (r.http_server) add("HTTP server", r.http_server);
        if (r.ssid) add("SSID", r.ssid);
        if (r.uptime) add("Uptime", r.uptime);
        if (r.active_clients !== "" && r.active_clients != null) {
          add("Client total", r.active_clients);
        }
        if (r.active_lan_clients) add("Client LAN", r.active_lan_clients);
        if (r.active_wifi_24g) add("Client WiFi 2.4G", r.active_wifi_24g);
        if (r.active_wifi_5g) add("Client WiFi 5G", r.active_wifi_5g);
        if (r.wan_proto) add("WAN proto", r.wan_proto);
        if (r.dial_switch) add("Dial switch", r.dial_switch);
        if (r.apn_config) add("APN", r.apn_config);
        if (r.profile_name) add("Profile", r.profile_name);
        if (r.wan_ip) add("WAN IP", r.wan_ip);
        if (r.wan_gateway) add("WAN gateway", r.wan_gateway);
        if (r.wan_dns) add("WAN DNS", r.wan_dns);
        if (r.network_name) add("Operator", r.network_name);
        if (r.sys_mode && r.sys_mode !== "—") add("Sys mode", r.sys_mode);
        if (r.data_mode && r.data_mode !== "—" && r.data_mode !== "0") {
          add("Data mode", r.data_mode);
        }
        if (r.rssi && r.rssi !== "0") add("RSSI", r.rssi);
        if (r.wan_connected === true) add("PDP", "Connected");
        if (r.wan_connected === false) add("PDP", "Disconnected");
        if (r.sim_status) add("SIM", r.sim_status);
        if (r.msisdn) add("MSISDN", r.msisdn);
        if (r.imei) add("IMEI", r.imei);
        if (r.imsi) add("IMSI", r.imsi);
        if (r.iccid) add("ICCID", r.iccid);
        if (r.sw_version) add("Firmware", r.sw_version);
        if (r.hw_version) add("Hardware", r.hw_version);
        if (r.baseband_version) add("Baseband", r.baseband_version);
        if (r.lan_ip) add("LAN IP", r.lan_ip);
        if (r.lan_netmask) add("LAN mask", r.lan_netmask);
        if (r.workmode) add("Work mode", r.workmode);
        if (Array.isArray(r.wifi_ssids) && r.wifi_ssids.length) {
          add(
            "WiFi SSID",
            r.wifi_ssids.map((s) => `${s.ssid} (${s.band})`).join(", ")
          );
        }
        if (Array.isArray(r.apns) && r.apns.length) {
          add(
            "APN list",
            r.apns.map((a) => `${a.apn || "?"} [${a.status || "?"}]`).join(", ")
          );
        }
        if (r.uplink_note) add("Catatan uplink", r.uplink_note);

        el.detailRouterInfo.innerHTML = rows.length
          ? rows
              .map(
                ([label, value]) => `
            <li>
              <span class="net-bullet">-</span>
              <span class="net-label">${escapeHtml(label)}</span>
              <span class="net-sep">:</span>
              <span class="net-value">${escapeHtml(value)}</span>
            </li>`
              )
              .join("")
          : `<li><span class="net-value">Tidak ada detail</span></li>`;
      } else {
        el.detailRouterExtra.hidden = true;
        el.detailRouterExtra.setAttribute("hidden", "");
        el.detailRouterInfo.innerHTML = "";
      }
    }

    fillDeviceMetaReadonly(d);

    // Visual indicator bar based on current health (placeholder 30-seg)
    const segs = [];
    for (let i = 0; i < 30; i++) {
      let cls = "";
      if (d.health === "issue") cls = i > 24 ? "bad" : "warn";
      else if (d.health === "attention") cls = i > 26 ? "warn" : "";
      else if (i === 28) cls = "warn";
      segs.push(`<span class="${cls}"></span>`);
    }
    el.detailUptimeBar.innerHTML = segs.join("");
    if (isNet) {
      el.detailUptimePct.textContent = d.online
        ? (d.internet_ok || d.recording ? "NET OK" : "NO WAN")
        : "OFFLINE";
    } else {
      el.detailUptimePct.textContent = d.online ? (d.recording ? "REC" : "ONLINE") : "OFFLINE";
    }

    const deviceEvents = (state.events || []).filter((e) => e.device_id === d.id).slice(0, 8);
    const fallback = [];
    if (!deviceEvents.length) {
      if (isNet) {
        fallback.push({
          tone: d.online ? ((d.internet_ok || d.recording) ? "green" : "red") : "red",
          time: new Date().toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" }),
          text: d.online
            ? d.internet_ok || d.recording
              ? "Router online dan internet terhubung"
              : "Router online, koneksi internet terputus"
            : "Router/gateway tidak terjangkau",
        });
        fallback.push({
          tone: "blue",
          time: new Date().toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" }),
          text: `Monitoring gateway ${d.ip || "192.168.1.1"} (ping + HTTP + internet)`,
        });
      } else {
        fallback.push({
          tone: d.online ? (d.recording ? "green" : "orange") : "red",
          time: new Date().toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" }),
          text: d.online
            ? d.recording
              ? "Kamera online dan sedang merekam"
              : "Kamera online, recording tidak aktif"
            : "Kamera terdeteksi offline dari NX Witness",
        });
        fallback.push({
          tone: "blue",
          time: new Date().toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" }),
          text: "Status diambil via REST API NX Witness",
        });
      }
    }
    const timeline = deviceEvents.length ? deviceEvents : fallback;
    el.detailTimeline.innerHTML = timeline
      .map(
        (e) => `
        <li>
          <span class="t-dot ${e.tone || "grey"}"></span>
          <span>${escapeHtml(e.text)}</span>
          <span class="t-time">${escapeHtml(e.time || "")}</span>
        </li>`
      )
      .join("");

    if (isNet) {
      el.btnNx.href = d.admin_url || `http://${d.ip || "192.168.1.1"}/`;
      el.btnNx.textContent = "Buka Admin Router";
    } else {
      el.btnNx.href = nxPublicUrl();
      el.btnNx.textContent = "Buka di NX Witness";
    }
  }

  function renderAll() {
    renderMeta();
    renderStats();
    renderGrid();
    renderDetail();
  }

  async function loadStatus(forceRefresh = false) {
    const url = forceRefresh ? "/api/refresh" : "/api/status";
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    state.devices = data.devices || [];
    state.events = data.events || [];
    state.meta = data.meta || {};
    state.summary = data.summary || {};
    if (state.selectedId && !state.devices.some((d) => d.id === state.selectedId)) {
      state.selectedId = null;
    }
    renderAll();
  }

  function escapeHtml(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
  function escapeAttr(s) {
    return escapeHtml(s).replace(/'/g, "&#39;");
  }

  /** NX URL for the browser: same host as CMMS address bar, NX port from config. */
  function nxPublicUrl() {
    const configured = state.meta.nx_host || "https://127.0.0.1:7001";
    let protocol = "https:";
    let port = "7001";
    try {
      const u = new URL(configured);
      protocol = u.protocol || "https:";
      port = u.port || (protocol === "https:" ? "443" : "80");
    } catch (_) {
      /* keep defaults */
    }
    const host = window.location.hostname || "127.0.0.1";
    return `${protocol}//${host}:${port}`;
  }

  // Events
  el.filters.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-filter]");
    if (!btn) return;
    state.filter = btn.dataset.filter;
    state.page = 1;
    el.filters.querySelectorAll(".chip").forEach((c) => c.classList.toggle("active", c === btn));
    renderGrid();
  });

  el.sortBy.addEventListener("change", () => {
    state.sort = el.sortBy.value;
    renderGrid();
  });

  el.deviceGrid.addEventListener("click", (e) => {
    const card = e.target.closest("[data-id]");
    if (!card) return;
    state.selectedId = card.dataset.id;
    renderGrid();
    renderDetail();
  });

  el.pager.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-page]");
    if (!btn || btn.disabled) return;
    const list = filteredDevices();
    const pages = Math.max(1, Math.ceil(list.length / PAGE_SIZE));
    const p = btn.dataset.page;
    if (p === "prev") state.page = Math.max(1, state.page - 1);
    else if (p === "next") state.page = Math.min(pages, state.page + 1);
    else state.page = Number(p) || 1;
    renderGrid();
  });

  el.btnWall.addEventListener("click", () => {
    document.body.classList.toggle("wall-mode");
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen?.().catch(() => {});
    } else {
      document.exitFullscreen?.().catch(() => {});
    }
  });

  el.btnRefreshOne.addEventListener("click", () => {
    loadStatus(true).catch(console.error);
  });

  if (el.btnSaveEmail) {
    el.btnSaveEmail.addEventListener("click", () => {
      saveNotifySettings("email").catch(console.error);
    });
  }
  if (el.btnTestEmail) {
    el.btnTestEmail.addEventListener("click", () => {
      testNotify("email").catch(console.error);
    });
  }
  if (el.btnSaveTelegram) {
    el.btnSaveTelegram.addEventListener("click", () => {
      saveNotifySettings("telegram").catch(console.error);
    });
  }
  if (el.btnTestTelegram) {
    el.btnTestTelegram.addEventListener("click", () => {
      testNotify("telegram").catch(console.error);
    });
  }

  let assetsCache = [];

  function openAssetModal() {
    if (!el.assetModal) return;
    el.assetModal.hidden = false;
    document.body.style.overflow = "hidden";
    el.assetName?.focus();
  }

  function closeAssetModal() {
    if (!el.assetModal) return;
    el.assetModal.hidden = true;
    document.body.style.overflow = "";
    setMsg(el.assetSaveMsg, "");
  }

  function resetAssetForm() {
    if (el.assetEditId) el.assetEditId.value = "";
    if (el.assetFormTitle) el.assetFormTitle.textContent = "Tambah Perangkat";
    [
      el.assetName,
      el.assetLocation,
      el.assetIp,
      el.assetLocDetail,
      el.assetVendor,
      el.assetModel,
      el.assetMac,
      el.assetInstallDate,
      el.assetWarrantyEnd,
      el.assetMaintenanceEnd,
    ].forEach((node) => {
      if (node) node.value = "";
    });
    if (el.assetCategory) el.assetCategory.value = "CCTV";
    setMsg(el.assetSaveMsg, "");
  }

  function fillAssetForm(asset) {
    if (!asset) {
      resetAssetForm();
      openAssetModal();
      return;
    }
    if (el.assetEditId) el.assetEditId.value = asset.id || "";
    if (el.assetFormTitle) el.assetFormTitle.textContent = "Edit Perangkat";
    if (el.assetName) el.assetName.value = asset.name || "";
    if (el.assetCategory) el.assetCategory.value = asset.category || "CCTV";
    if (el.assetLocation) el.assetLocation.value = asset.location || "";
    if (el.assetIp) el.assetIp.value = asset.ip || "";
    if (el.assetLocDetail) el.assetLocDetail.value = asset.location_detail || "";
    if (el.assetVendor) el.assetVendor.value = asset.vendor || "";
    if (el.assetModel) el.assetModel.value = asset.model || "";
    if (el.assetMac) el.assetMac.value = asset.mac || "";
    if (el.assetInstallDate) el.assetInstallDate.value = asset.installation_date || "";
    if (el.assetWarrantyEnd) el.assetWarrantyEnd.value = asset.warranty_end_date || "";
    if (el.assetMaintenanceEnd) el.assetMaintenanceEnd.value = asset.maintenance_end_date || "";
    setMsg(el.assetSaveMsg, "");
    openAssetModal();
  }

  function collectAssetPayload() {
    return {
      name: el.assetName?.value?.trim() || "",
      category: el.assetCategory?.value || "CCTV",
      location: el.assetLocation?.value?.trim() || "",
      ip: el.assetIp?.value?.trim() || "",
      location_detail: el.assetLocDetail?.value?.trim() || "",
      vendor: el.assetVendor?.value?.trim() || "",
      model: el.assetModel?.value?.trim() || "",
      mac: el.assetMac?.value?.trim() || "",
      installation_date: el.assetInstallDate?.value || "",
      warranty_end_date: el.assetWarrantyEnd?.value || "",
      maintenance_end_date: el.assetMaintenanceEnd?.value || "",
      monitor_enabled: true,
    };
  }

  function renderAssetsTable(assets) {
    assetsCache = assets || [];
    if (el.assetsSummary) {
      el.assetsSummary.textContent = `${assetsCache.length} perangkat terdaftar`;
    }
    if (!el.assetsBody) return;
    if (!assetsCache.length) {
      el.assetsBody.innerHTML =
        '<tr><td colspan="7" class="muted">Belum ada perangkat. Tambah manual atau impor dari live monitoring.</td></tr>';
      return;
    }
    el.assetsBody.innerHTML = assetsCache
      .map((a) => {
        const garansi = contractStatusLabel(a.warranty_status || computeDateStatus(a.warranty_end_date));
        const maint = contractStatusLabel(
          a.maintenance_status || computeDateStatus(a.maintenance_end_date)
        );
        return `<tr>
          <td>
            <div class="report-title">${escapeHtml(a.name || "—")}</div>
            <div class="muted">${escapeHtml(a.vendor || "")}${a.model ? " · " + escapeHtml(a.model) : ""}</div>
          </td>
          <td>${escapeHtml(a.category || "—")}</td>
          <td>${escapeHtml(a.location || a.location_detail || "—")}</td>
          <td>${escapeHtml(a.ip || "—")}</td>
          <td><span class="meta-status-badge ${garansi.cls}">${garansi.text}</span></td>
          <td><span class="meta-status-badge ${maint.cls}">${maint.text}</span></td>
          <td>
            <div class="assets-actions">
              <button type="button" data-asset-edit="${escapeHtml(a.id)}">Edit</button>
              <button type="button" class="danger" data-asset-del="${escapeHtml(a.id)}">Hapus</button>
            </div>
          </td>
        </tr>`;
      })
      .join("");
  }

  async function loadAssets() {
    const res = await fetch("/api/assets", { cache: "no-store" });
    const data = await res.json();
    if (!res.ok || !data.ok) throw new Error(data.error || "Gagal memuat aset");
    renderAssetsTable(data.assets || []);
  }

  async function saveAsset() {
    const editId = el.assetEditId?.value || "";
    const payload = collectAssetPayload();
    if (!payload.name) {
      setMsg(el.assetSaveMsg, "Nama perangkat wajib diisi", "danger");
      return;
    }
    if (el.btnSaveAsset) el.btnSaveAsset.disabled = true;
    setMsg(el.assetSaveMsg, "Menyimpan…");
    try {
      const url = editId ? `/api/assets/${encodeURIComponent(editId)}` : "/api/assets";
      const res = await fetch(url, {
        method: editId ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok || !data.ok) throw new Error(data.error || "Gagal menyimpan");
      setMsg(el.assetSaveMsg, "Tersimpan", "ok");
      await loadAssets();
      loadStatus(true).catch(console.error);
      closeAssetModal();
      resetAssetForm();
    } catch (err) {
      setMsg(el.assetSaveMsg, err.message || "Gagal menyimpan", "danger");
    } finally {
      if (el.btnSaveAsset) el.btnSaveAsset.disabled = false;
    }
  }

  async function deleteAsset(id) {
    const asset = assetsCache.find((a) => a.id === id);
    const label = asset?.name || id;
    if (!window.confirm(`Hapus perangkat "${label}" dari monitoring?`)) return;
    const res = await fetch(`/api/assets/${encodeURIComponent(id)}`, { method: "DELETE" });
    const data = await res.json();
    if (!res.ok || !data.ok) throw new Error(data.error || "Gagal menghapus");
    if (el.assetEditId?.value === id) {
      closeAssetModal();
      resetAssetForm();
    }
    await loadAssets();
    loadStatus(true).catch(console.error);
  }

  async function importLiveAssets() {
    if (el.btnImportAssets) el.btnImportAssets.disabled = true;
    try {
      const res = await fetch("/api/assets/import-live", { method: "POST" });
      const data = await res.json();
      if (!res.ok || !data.ok) throw new Error(data.error || "Gagal impor");
      renderAssetsTable(data.assets || []);
      if (el.assetsSummary) {
        el.assetsSummary.textContent = `${data.assets?.length || 0} perangkat terdaftar · ${data.added || 0} baru diimpor`;
      }
      loadStatus(true).catch(console.error);
    } catch (err) {
      alert(err.message || "Gagal impor");
    } finally {
      if (el.btnImportAssets) el.btnImportAssets.disabled = false;
    }
  }

  if (el.btnSaveAsset) {
    el.btnSaveAsset.addEventListener("click", () => saveAsset().catch(console.error));
  }
  if (el.btnNewAsset) {
    el.btnNewAsset.addEventListener("click", () => {
      resetAssetForm();
      openAssetModal();
    });
  }
  if (el.assetModal) {
    el.assetModal.addEventListener("click", (e) => {
      if (e.target.closest("[data-asset-close]")) closeAssetModal();
    });
  }
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    if (el.assetModal && !el.assetModal.hidden) closeAssetModal();
    if (el.techModal && !el.techModal.hidden) closeTechModal();
    if (el.woModal && !el.woModal.hidden) closeWoModal();
  });
  if (el.btnImportAssets) {
    el.btnImportAssets.addEventListener("click", () => importLiveAssets().catch(console.error));
  }
  if (el.assetsBody) {
    el.assetsBody.addEventListener("click", (e) => {
      const editBtn = e.target.closest("[data-asset-edit]");
      if (editBtn) {
        const asset = assetsCache.find((a) => a.id === editBtn.dataset.assetEdit);
        fillAssetForm(asset);
        return;
      }
      const delBtn = e.target.closest("[data-asset-del]");
      if (delBtn) {
        deleteAsset(delBtn.dataset.assetDel).catch((err) => {
          alert(err.message || "Gagal menghapus");
        });
      }
    });
  }

  function canAccessMenu(menu) {
    const user = state.user;
    if (!user) return false;
    if (user.role === "administrator") return true;
    return (user.menus || []).includes(menu);
  }

  function applyNavAccess() {
    document.querySelectorAll("[data-nav]").forEach((a) => {
      const nav = a.dataset.nav;
      a.hidden = !canAccessMenu(nav);
    });
  }

  function applyCurrentUser() {
    const user = state.user;
    if (!user) return;
    const label = user.full_name || user.username || "User";
    if (el.siteOrg) el.siteOrg.textContent = label;
    if (el.userRoleLabel) {
      el.userRoleLabel.textContent =
        user.role === "administrator" ? "Administrator" : "Operator";
    }
    if (el.userAvatar) {
      const src = (user.full_name || user.username || "U").trim();
      const parts = src.split(/\s+/).filter(Boolean);
      el.userAvatar.textContent = (
        parts.length >= 2 ? parts[0][0] + parts[1][0] : src.slice(0, 2)
      ).toUpperCase();
    }
  }

  function firstAllowedView() {
    const order = [
      "dashboard",
      "assets",
      "wo",
      "pm",
      "team",
      "statistik",
      "report",
      "notify",
      "users",
    ];
    return order.find((v) => canAccessMenu(v)) || "dashboard";
  }

  document.querySelectorAll("[data-nav]").forEach((a) => {
    a.addEventListener("click", (e) => {
      e.preventDefault();
      const nav = a.dataset.nav;
      if (!canAccessMenu(nav)) return;
      document.querySelectorAll(".nav-item").forEach((n) => n.classList.remove("active"));
      a.classList.add("active");
      if (nav === "report") {
        showView("report");
      } else if (nav === "statistik") {
        showView("statistik");
      } else if (nav === "notify") {
        showView("notify");
      } else if (nav === "assets") {
        showView("assets");
      } else if (nav === "team") {
        showView("team");
      } else if (nav === "wo") {
        showView("wo");
      } else if (nav === "pm") {
        showView("pm");
      } else if (nav === "users") {
        showView("users");
      } else if (nav === "dashboard") {
        showView("dashboard");
      } else {
        // menu lain belum diimplementasi — tetap di dashboard
        showView("dashboard");
      }
    });
  });

  if (el.btnLogout) {
    el.btnLogout.addEventListener("click", async () => {
      try {
        await fetch("/api/auth/logout", { method: "POST" });
      } catch (_) {
        /* ignore */
      }
      window.location.replace("/login");
    });
  }

  let woCache = [];
  let woAssetChoices = [];
  let woTechChoices = [];

  function openWoModal() {
    if (!el.woModal) return;
    el.woModal.hidden = false;
    document.body.style.overflow = "hidden";
  }

  function closeWoModal() {
    if (!el.woModal) return;
    el.woModal.hidden = true;
    document.body.style.overflow = "";
    setMsg(el.woSaveMsg, "");
  }

  function fillSelectOptions(selectEl, placeholder, items, labelFn) {
    if (!selectEl) return;
    const options = [`<option value="">${escapeHtml(placeholder)}</option>`];
    for (const item of items) {
      options.push(
        `<option value="${escapeHtml(item.id)}">${escapeHtml(labelFn(item))}</option>`
      );
    }
    selectEl.innerHTML = options.join("");
    selectEl.disabled = false;
  }

  function renderWoPickLists() {
    const category = el.woCategory?.value || "";
    if (el.woAsset) {
      if (!category) {
        el.woAsset.innerHTML = '<option value="">— Pilih kategori dulu —</option>';
        el.woAsset.disabled = true;
      } else {
        const assets = woAssetChoices.filter((a) => (a.category || "") === category);
        fillSelectOptions(
          el.woAsset,
          assets.length ? "— Pilih asset —" : `— Tidak ada asset ${category} —`,
          assets,
          (a) => {
            const loc = a.location || a.ip || "";
            return loc ? `${a.name || a.id} · ${loc}` : a.name || a.id;
          }
        );
        if (!assets.length) el.woAsset.disabled = true;
      }
    }
    if (el.woTech) {
      if (!category) {
        el.woTech.innerHTML = '<option value="">— Pilih kategori dulu —</option>';
        el.woTech.disabled = true;
      } else {
        const techs = woTechChoices.filter((t) => (t.skills || []).includes(category));
        fillSelectOptions(
          el.woTech,
          techs.length ? "— Pilih teknisi —" : `— Tidak ada teknisi ${category} —`,
          techs,
          (t) => {
            const mail = t.email || "tanpa email";
            return `${t.name || t.id} · ${mail}`;
          }
        );
        if (!techs.length) el.woTech.disabled = true;
      }
    }
  }

  if (el.woCategory) {
    el.woCategory.addEventListener("change", () => {
      renderWoPickLists();
    });
  }

  function resetWoForm() {
    const now = new Date();
    if (el.woDate) el.woDate.value = isoDate(now);
    if (el.woTime) {
      const hh = String(now.getHours()).padStart(2, "0");
      const mm = String(now.getMinutes()).padStart(2, "0");
      el.woTime.value = `${hh}:${mm}`;
    }
    if (el.woCategory) el.woCategory.value = "";
    if (el.woNotes) el.woNotes.value = "";
    if (el.woFormTitle) el.woFormTitle.textContent = "Buat Work Order";
    renderWoPickLists();
    setMsg(el.woSaveMsg, "");
  }

  function renderWoTable(list) {
    woCache = list || [];
    if (el.woSummary) el.woSummary.textContent = `${woCache.length} work order`;
    if (!el.woBody) return;
    if (!woCache.length) {
      el.woBody.innerHTML =
        '<tr><td colspan="8" class="muted">Belum ada work order. Klik Buat Work Order untuk menambah.</td></tr>';
      return;
    }
    el.woBody.innerHTML = woCache
      .map((w) => {
        const assets = (w.assets || []).map((a) => a.name || a.id).join(", ") || "—";
        const techs = (w.technicians || []).map((t) => t.name || t.id).join(", ") || "—";
        return `<tr>
          <td><div class="report-title">${escapeHtml(w.wo_number || "—")}</div></td>
          <td><span class="skill-tag">${escapeHtml(w.category || "—")}</span></td>
          <td>${escapeHtml(w.work_date || "—")}</td>
          <td>${escapeHtml(w.work_time || "—")}</td>
          <td><div class="wo-stack">${escapeHtml(assets)}</div></td>
          <td><div class="wo-stack">${escapeHtml(techs)}</div></td>
          <td>${escapeHtml(w.email_status || "—")}</td>
          <td>
            <div class="assets-actions">
              <button type="button" data-wo-resend="${escapeHtml(w.id)}">Re-send Email</button>
              <button type="button" class="danger" data-wo-del="${escapeHtml(w.id)}">Hapus</button>
            </div>
          </td>
        </tr>`;
      })
      .join("");
  }

  async function loadWoChoices() {
    const [assetsRes, techRes] = await Promise.all([
      fetch("/api/assets", { cache: "no-store" }),
      fetch("/api/technicians", { cache: "no-store" }),
    ]);
    const assetsData = await assetsRes.json();
    const techData = await techRes.json();
    if (!assetsRes.ok || !assetsData.ok) throw new Error(assetsData.error || "Gagal memuat asset");
    if (!techRes.ok || !techData.ok) throw new Error(techData.error || "Gagal memuat teknisi");
    woAssetChoices = assetsData.assets || [];
    woTechChoices = techData.technicians || [];
  }

  let woEmailPollTimer = null;

  function hasPendingWoEmail(list) {
    return (list || []).some((w) => String(w.email_status || "").includes("mengirim"));
  }

  function stopWoEmailPoll() {
    if (woEmailPollTimer) {
      clearInterval(woEmailPollTimer);
      woEmailPollTimer = null;
    }
  }

  function startWoEmailPoll() {
    stopWoEmailPoll();
    let ticks = 0;
    woEmailPollTimer = setInterval(() => {
      ticks += 1;
      loadWorkOrders()
        .then(() => {
          if (!hasPendingWoEmail(woCache) || ticks >= 20) stopWoEmailPoll();
        })
        .catch(() => {
          if (ticks >= 20) stopWoEmailPoll();
        });
    }, 2000);
  }

  async function loadWorkOrders() {
    const res = await fetch("/api/work-orders", { cache: "no-store" });
    const data = await res.json();
    if (!res.ok || !data.ok) throw new Error(data.error || "Gagal memuat work order");
    renderWoTable(data.work_orders || []);
  }

  async function loadAutoWoSettings() {
    const res = await fetch("/api/settings/auto-wo", { cache: "no-store" });
    const data = await res.json();
    if (!res.ok || !data.ok) throw new Error(data.error || "Gagal memuat setting Auto WO");
    const minutes = data.settings?.delay_minutes ?? 0;
    const cooldown = data.settings?.cooldown_minutes ?? 60;
    if (el.woAutoMinutes) el.woAutoMinutes.value = minutes > 0 ? String(minutes) : "";
    if (el.woAutoCooldown) el.woAutoCooldown.value = String(cooldown);
    setMsg(el.woAutoMsg, "");
  }

  async function saveAutoWoSettings() {
    const raw = el.woAutoMinutes?.value;
    const rawCool = el.woAutoCooldown?.value;
    const payload = {
      delay_minutes: raw === "" || raw == null ? 0 : Number(raw),
      cooldown_minutes: rawCool === "" || rawCool == null ? 60 : Number(rawCool),
    };
    if (el.btnSaveWoAuto) el.btnSaveWoAuto.disabled = true;
    setMsg(el.woAutoMsg, "Menyimpan…");
    try {
      const res = await fetch("/api/settings/auto-wo", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok || !data.ok) throw new Error(data.error || "Gagal menyimpan");
      const minutes = data.settings?.delay_minutes ?? 0;
      const cooldown = data.settings?.cooldown_minutes ?? 60;
      if (el.woAutoMinutes) el.woAutoMinutes.value = minutes > 0 ? String(minutes) : "";
      if (el.woAutoCooldown) el.woAutoCooldown.value = String(cooldown);
      const coolTxt = cooldown > 0 ? ` · jeda ${cooldown} mnt/asset` : "";
      setMsg(
        el.woAutoMsg,
        minutes > 0 ? `Aktif: auto WO setelah ${minutes} menit gangguan${coolTxt}` : "Nonaktif",
        "ok"
      );
    } catch (err) {
      setMsg(el.woAutoMsg, err.message || "Gagal menyimpan", "danger");
    } finally {
      if (el.btnSaveWoAuto) el.btnSaveWoAuto.disabled = false;
    }
  }

  if (el.btnSaveWoAuto) {
    el.btnSaveWoAuto.addEventListener("click", () => saveAutoWoSettings().catch(console.error));
  }

  async function saveWorkOrder() {
    const category = el.woCategory?.value || "";
    const assetId = el.woAsset?.value || "";
    const techId = el.woTech?.value || "";
    const payload = {
      category,
      work_date: el.woDate?.value || "",
      work_time: el.woTime?.value || "",
      notes: el.woNotes?.value?.trim() || "",
      asset_ids: assetId ? [assetId] : [],
      technician_ids: techId ? [techId] : [],
    };
    if (!payload.work_date) {
      setMsg(el.woSaveMsg, "Tanggal wajib diisi", "danger");
      return;
    }
    if (!payload.work_time) {
      setMsg(el.woSaveMsg, "Waktu wajib diisi", "danger");
      return;
    }
    if (!category) {
      setMsg(el.woSaveMsg, "Pilih kategori terlebih dahulu", "danger");
      return;
    }
    if (!payload.asset_ids.length) {
      setMsg(el.woSaveMsg, "Pilih asset", "danger");
      return;
    }
    if (!payload.technician_ids.length) {
      setMsg(el.woSaveMsg, "Pilih teknisi", "danger");
      return;
    }
    if (el.btnSaveWo) el.btnSaveWo.disabled = true;
    setMsg(el.woSaveMsg, "Menyimpan…");
    try {
      const res = await fetch("/api/work-orders", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok || !data.ok) throw new Error(data.error || "Gagal menyimpan");
      closeWoModal();
      resetWoForm();
      await loadWorkOrders();
      startWoEmailPoll();
    } catch (err) {
      setMsg(el.woSaveMsg, err.message || "Gagal menyimpan", "danger");
    } finally {
      if (el.btnSaveWo) el.btnSaveWo.disabled = false;
    }
  }

  async function resendWorkOrderEmail(id) {
    const wo = woCache.find((w) => w.id === id);
    const label = wo?.wo_number || id;
    if (!window.confirm(`Kirim ulang email work order "${label}"?`)) return;
    const res = await fetch(`/api/work-orders/${encodeURIComponent(id)}/resend-email`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });
    const data = await res.json();
    if (!res.ok || !data.ok) throw new Error(data.error || "Gagal mengirim ulang email");
    if (data.work_order) {
      const idx = woCache.findIndex((w) => w.id === id);
      if (idx >= 0) {
        woCache[idx] = data.work_order;
        renderWoTable(woCache);
      } else {
        await loadWorkOrders();
      }
    } else {
      await loadWorkOrders();
    }
    startWoEmailPoll();
  }

  async function deleteWorkOrder(id) {
    const wo = woCache.find((w) => w.id === id);
    const label = wo?.wo_number || id;
    if (!window.confirm(`Hapus work order "${label}"?`)) return;
    const res = await fetch(`/api/work-orders/${encodeURIComponent(id)}`, { method: "DELETE" });
    const data = await res.json();
    if (!res.ok || !data.ok) throw new Error(data.error || "Gagal menghapus");
    await loadWorkOrders();
  }

  if (el.btnNewWo) {
    el.btnNewWo.addEventListener("click", () => {
      loadWoChoices()
        .then(() => {
          resetWoForm();
          openWoModal();
        })
        .catch((err) => alert(err.message || "Gagal memuat pilihan"));
    });
  }
  if (el.btnSaveWo) {
    el.btnSaveWo.addEventListener("click", () => saveWorkOrder().catch(console.error));
  }
  if (el.woModal) {
    el.woModal.addEventListener("click", (e) => {
      if (e.target.closest("[data-wo-close]")) closeWoModal();
    });
  }
  if (el.woBody) {
    el.woBody.addEventListener("click", (e) => {
      const resendBtn = e.target.closest("[data-wo-resend]");
      if (resendBtn) {
        resendWorkOrderEmail(resendBtn.dataset.woResend).catch((err) =>
          alert(err.message || "Gagal mengirim ulang email")
        );
        return;
      }
      const delBtn = e.target.closest("[data-wo-del]");
      if (delBtn) {
        deleteWorkOrder(delBtn.dataset.woDel).catch((err) => alert(err.message || "Gagal menghapus"));
      }
    });
  }

  let pmCache = [];
  let pmAssetChoices = [];
  let pmTechChoices = [];
  let pmDetailScheduleId = null;

  function pmDueLabel(status) {
    if (status === "overdue") return { text: "Terlambat", cls: "danger" };
    if (status === "due_soon") return { text: "Segera", cls: "warn" };
    if (status === "ok") return { text: "Sesuai jadwal", cls: "ok" };
    if (status === "inactive") return { text: "Nonaktif", cls: "muted" };
    return { text: "—", cls: "muted" };
  }

  function openPmModal() {
    if (!el.pmModal) return;
    el.pmModal.hidden = false;
    document.body.style.overflow = "hidden";
  }

  function closePmModal() {
    if (!el.pmModal) return;
    el.pmModal.hidden = true;
    if (!el.pmDetailModal || el.pmDetailModal.hidden) {
      document.body.style.overflow = "";
    }
  }

  function openPmDetailModal() {
    if (!el.pmDetailModal) return;
    el.pmDetailModal.hidden = false;
    document.body.style.overflow = "hidden";
  }

  function closePmDetailModal() {
    if (!el.pmDetailModal) return;
    el.pmDetailModal.hidden = true;
    pmDetailScheduleId = null;
    if (!el.pmModal || el.pmModal.hidden) {
      document.body.style.overflow = "";
    }
  }

  function syncPmIntervalUi() {
    const custom = el.pmInterval?.value === "custom";
    if (el.pmCustomDaysWrap) el.pmCustomDaysWrap.hidden = !custom;
  }

  function resetPmForm() {
    if (el.pmEditId) el.pmEditId.value = "";
    if (el.pmFormTitle) el.pmFormTitle.textContent = "Tambah Jadwal PM";
    if (el.pmInterval) el.pmInterval.value = "90";
    if (el.pmCustomDays) el.pmCustomDays.value = "";
    if (el.pmNextDue) el.pmNextDue.value = isoDate(new Date());
    if (el.pmActive) el.pmActive.checked = true;
    if (el.pmNotes) el.pmNotes.value = "";
    if (el.pmAsset) el.pmAsset.disabled = false;
    syncPmIntervalUi();
    renderPmAssetOptions();
    setMsg(el.pmSaveMsg, "");
  }

  function renderPmAssetOptions(selectedId, { includeId } = {}) {
    if (!el.pmAsset) return;
    const scheduled = new Set(
      pmCache.filter((s) => !includeId || s.id !== includeId).map((s) => s.asset_id)
    );
    const available = pmAssetChoices.filter(
      (a) => a.id === selectedId || !scheduled.has(a.id)
    );
    fillSelectOptions(
      el.pmAsset,
      available.length ? "— Pilih asset —" : "— Semua asset sudah terjadwal —",
      available,
      (a) => `${a.name || a.id} · ${a.category || ""}${a.location ? ` · ${a.location}` : ""}`
    );
    if (selectedId) el.pmAsset.value = selectedId;
    if (!available.length) el.pmAsset.disabled = true;
  }

  function fillPmForm(schedule) {
    if (!schedule) return resetPmForm();
    if (el.pmEditId) el.pmEditId.value = schedule.id || "";
    if (el.pmFormTitle) el.pmFormTitle.textContent = "Edit Jadwal PM";
    const days = Number(schedule.interval_days) || 90;
    const presets = new Set([30, 90, 180, 365]);
    if (el.pmInterval) el.pmInterval.value = presets.has(days) ? String(days) : "custom";
    if (el.pmCustomDays) el.pmCustomDays.value = presets.has(days) ? "" : String(days);
    if (el.pmNextDue) el.pmNextDue.value = schedule.next_due_date || "";
    if (el.pmActive) el.pmActive.checked = schedule.active !== false;
    if (el.pmNotes) el.pmNotes.value = schedule.notes || "";
    syncPmIntervalUi();
    renderPmAssetOptions(schedule.asset_id, { includeId: schedule.id });
    if (el.pmAsset) el.pmAsset.disabled = true;
    setMsg(el.pmSaveMsg, "");
  }

  function renderPmTable(list) {
    pmCache = list || [];
    const overdue = pmCache.filter((s) => s.due_status === "overdue" && s.active).length;
    const soon = pmCache.filter((s) => s.due_status === "due_soon" && s.active).length;
    if (el.pmSummary) {
      const bits = [`${pmCache.length} jadwal PM`];
      if (overdue) bits.push(`${overdue} terlambat`);
      if (soon) bits.push(`${soon} segera`);
      el.pmSummary.textContent = bits.join(" · ");
    }
    if (!el.pmBody) return;
    if (!pmCache.length) {
      el.pmBody.innerHTML =
        '<tr><td colspan="7" class="muted">Belum ada jadwal PM. Klik Jadwal PM untuk menambah.</td></tr>';
      return;
    }
    el.pmBody.innerHTML = pmCache
      .map((s) => {
        const asset = s.asset || {};
        const due = pmDueLabel(s.due_status);
        const contract = contractStatusLabel(s.contract_status || "unset");
        const contractUntil = s.contract_end_date
          ? `s/d ${formatDateId(s.contract_end_date)}`
          : "";
        return `<tr>
          <td>
            <div class="report-title">${escapeHtml(asset.name || s.asset_id || "—")}</div>
            <div class="muted">${escapeHtml(asset.category || "—")}${asset.location ? ` · ${escapeHtml(asset.location)}` : ""}</div>
          </td>
          <td><span class="skill-tag">${escapeHtml(s.interval_label || `${s.interval_days} hari`)}</span></td>
          <td>${escapeHtml(formatDateId(s.last_service_date))}</td>
          <td><strong>${escapeHtml(formatDateId(s.next_due_date))}</strong></td>
          <td>
            <div class="meta-status-line">
              <span class="meta-status-badge ${contract.cls}">${escapeHtml(contract.text)}</span>
              <span class="meta-until-text">${escapeHtml(contractUntil || "—")}</span>
            </div>
          </td>
          <td><span class="meta-status-badge ${due.cls}">${escapeHtml(due.text)}</span></td>
          <td>
            <div class="assets-actions">
              <button type="button" data-pm-records="${escapeHtml(s.id)}">Service Record</button>
              <button type="button" data-pm-edit="${escapeHtml(s.id)}">Edit</button>
              <button type="button" class="danger" data-pm-del="${escapeHtml(s.id)}">Hapus</button>
            </div>
          </td>
        </tr>`;
      })
      .join("");
  }

  async function loadPmChoices() {
    const [assetsRes, techRes] = await Promise.all([
      fetch("/api/assets", { cache: "no-store" }),
      fetch("/api/technicians", { cache: "no-store" }),
    ]);
    const assetsData = await assetsRes.json();
    const techData = await techRes.json();
    if (!assetsRes.ok || !assetsData.ok) throw new Error(assetsData.error || "Gagal memuat asset");
    if (!techRes.ok || !techData.ok) throw new Error(techData.error || "Gagal memuat teknisi");
    pmAssetChoices = assetsData.assets || [];
    pmTechChoices = techData.technicians || [];
  }

  async function loadPmSchedules() {
    const res = await fetch("/api/pm-schedules", { cache: "no-store" });
    const data = await res.json();
    if (!res.ok || !data.ok) throw new Error(data.error || "Gagal memuat jadwal PM");
    renderPmTable(data.schedules || []);
  }

  function resolvePmIntervalDays() {
    if (el.pmInterval?.value === "custom") {
      return Number(el.pmCustomDays?.value || 0);
    }
    return Number(el.pmInterval?.value || 0);
  }

  async function savePmSchedule() {
    const editId = el.pmEditId?.value || "";
    const payload = {
      asset_id: el.pmAsset?.value || "",
      interval_days: resolvePmIntervalDays(),
      next_due_date: el.pmNextDue?.value || "",
      notes: el.pmNotes?.value?.trim() || "",
      active: !!el.pmActive?.checked,
    };
    if (!payload.asset_id) {
      setMsg(el.pmSaveMsg, "Pilih asset", "danger");
      return;
    }
    if (!payload.interval_days || payload.interval_days < 1) {
      setMsg(el.pmSaveMsg, "Interval hari tidak valid", "danger");
      return;
    }
    if (!payload.next_due_date) {
      setMsg(el.pmSaveMsg, "Jadwal berikutnya wajib diisi", "danger");
      return;
    }
    if (el.btnSavePm) el.btnSavePm.disabled = true;
    setMsg(el.pmSaveMsg, "Menyimpan…");
    try {
      const res = await fetch(
        editId ? `/api/pm-schedules/${encodeURIComponent(editId)}` : "/api/pm-schedules",
        {
          method: editId ? "PUT" : "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        }
      );
      const data = await res.json();
      if (!res.ok || !data.ok) throw new Error(data.error || "Gagal menyimpan");
      closePmModal();
      resetPmForm();
      await loadPmSchedules();
    } catch (err) {
      setMsg(el.pmSaveMsg, err.message || "Gagal menyimpan", "danger");
    } finally {
      if (el.btnSavePm) el.btnSavePm.disabled = false;
    }
  }

  async function editPmSchedule(id) {
    const schedule = pmCache.find((s) => s.id === id);
    if (!schedule) throw new Error("Jadwal tidak ditemukan");
    await loadPmChoices();
    fillPmForm(schedule);
    openPmModal();
  }

  async function deletePmSchedule(id) {
    const schedule = pmCache.find((s) => s.id === id);
    const label = schedule?.asset?.name || id;
    if (!window.confirm(`Hapus jadwal PM untuk "${label}" beserta service record-nya?`)) return;
    const res = await fetch(`/api/pm-schedules/${encodeURIComponent(id)}`, { method: "DELETE" });
    const data = await res.json();
    if (!res.ok || !data.ok) throw new Error(data.error || "Gagal menghapus");
    await loadPmSchedules();
  }

  function renderPmDetail(schedule, records) {
    const asset = schedule?.asset || {};
    const due = pmDueLabel(schedule?.due_status);
    if (el.pmDetailTitle) {
      el.pmDetailTitle.textContent = asset.name || "Service Record";
    }
    if (el.pmDetailSub) {
      el.pmDetailSub.textContent = `${schedule?.interval_label || ""} · berikutnya ${formatDateId(schedule?.next_due_date)}`;
    }
    if (el.pmDetailMeta) {
      const contract = contractStatusLabel(schedule?.contract_status || "unset");
      el.pmDetailMeta.innerHTML = `
        <div class="pm-detail-grid">
          <div><span class="muted">Kategori</span><strong>${escapeHtml(asset.category || "—")}</strong></div>
          <div><span class="muted">Lokasi</span><strong>${escapeHtml(asset.location || "—")}</strong></div>
          <div><span class="muted">Service terakhir</span><strong>${escapeHtml(formatDateId(schedule?.last_service_date))}</strong></div>
          <div><span class="muted">Jadwal berikutnya</span><strong>${escapeHtml(formatDateId(schedule?.next_due_date))}</strong>
            <span class="meta-status-badge ${due.cls}">${escapeHtml(due.text)}</span></div>
          <div><span class="muted">Kontrak maintenance</span>
            <span class="meta-status-badge ${contract.cls}">${escapeHtml(contract.text)}</span>
            <span class="meta-until-text">${escapeHtml(schedule?.contract_end_date ? `s/d ${formatDateId(schedule.contract_end_date)}` : "—")}</span>
          </div>
        </div>`;
    }
    fillSelectOptions(
      el.pmRecordTech,
      "— Opsional —",
      pmTechChoices,
      (t) => `${t.name || t.id}${t.skills?.length ? ` · ${(t.skills || []).join(", ")}` : ""}`
    );
    if (el.pmRecordDate) el.pmRecordDate.value = isoDate(new Date());
    if (el.pmRecordNotes) el.pmRecordNotes.value = "";
    setMsg(el.pmRecordMsg, "");
    if (!el.pmRecordsBody) return;
    if (!records?.length) {
      el.pmRecordsBody.innerHTML =
        '<tr><td colspan="5" class="muted">Belum ada service record untuk asset ini.</td></tr>';
      return;
    }
    el.pmRecordsBody.innerHTML = records
      .map((r) => {
        const techName = r.technician?.name || r.technician_id || "—";
        return `<tr>
          <td>${escapeHtml(formatDateId(r.service_date))}</td>
          <td>${escapeHtml(techName)}</td>
          <td><div class="wo-stack">${escapeHtml(r.notes || "—")}</div></td>
          <td>${escapeHtml(formatDateId(r.next_due_after))}</td>
          <td>
            <div class="assets-actions">
              <button type="button" class="danger" data-pm-record-del="${escapeHtml(r.id)}">Hapus</button>
            </div>
          </td>
        </tr>`;
      })
      .join("");
  }

  async function openPmRecords(id) {
    await loadPmChoices();
    const res = await fetch(`/api/pm-schedules/${encodeURIComponent(id)}/records`, {
      cache: "no-store",
    });
    const data = await res.json();
    if (!res.ok || !data.ok) throw new Error(data.error || "Gagal memuat service record");
    pmDetailScheduleId = id;
    renderPmDetail(data.schedule, data.records || []);
    openPmDetailModal();
  }

  async function savePmRecord() {
    if (!pmDetailScheduleId) return;
    const payload = {
      service_date: el.pmRecordDate?.value || "",
      technician_id: el.pmRecordTech?.value || "",
      notes: el.pmRecordNotes?.value?.trim() || "",
    };
    if (!payload.service_date) {
      setMsg(el.pmRecordMsg, "Tanggal service wajib diisi", "danger");
      return;
    }
    if (el.btnSavePmRecord) el.btnSavePmRecord.disabled = true;
    setMsg(el.pmRecordMsg, "Menyimpan…");
    try {
      const res = await fetch(
        `/api/pm-schedules/${encodeURIComponent(pmDetailScheduleId)}/records`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        }
      );
      const data = await res.json();
      if (!res.ok || !data.ok) throw new Error(data.error || "Gagal menyimpan");
      setMsg(el.pmRecordMsg, "Service tercatat", "ok");
      const detailRes = await fetch(
        `/api/pm-schedules/${encodeURIComponent(pmDetailScheduleId)}/records`,
        { cache: "no-store" }
      );
      const detailData = await detailRes.json();
      if (detailRes.ok && detailData.ok) {
        renderPmDetail(detailData.schedule, detailData.records || []);
      }
      await loadPmSchedules();
    } catch (err) {
      setMsg(el.pmRecordMsg, err.message || "Gagal menyimpan", "danger");
    } finally {
      if (el.btnSavePmRecord) el.btnSavePmRecord.disabled = false;
    }
  }

  async function deletePmRecord(recordId) {
    if (!pmDetailScheduleId) return;
    if (!window.confirm("Hapus service record ini?")) return;
    const res = await fetch(
      `/api/pm-schedules/${encodeURIComponent(pmDetailScheduleId)}/records/${encodeURIComponent(recordId)}`,
      { method: "DELETE" }
    );
    const data = await res.json();
    if (!res.ok || !data.ok) throw new Error(data.error || "Gagal menghapus");
    await openPmRecords(pmDetailScheduleId);
    await loadPmSchedules();
  }

  if (el.btnNewPm) {
    el.btnNewPm.addEventListener("click", () => {
      loadPmChoices()
        .then(() => {
          resetPmForm();
          openPmModal();
        })
        .catch((err) => alert(err.message || "Gagal memuat pilihan"));
    });
  }
  if (el.btnSavePm) {
    el.btnSavePm.addEventListener("click", () => savePmSchedule().catch(console.error));
  }
  if (el.pmInterval) {
    el.pmInterval.addEventListener("change", syncPmIntervalUi);
  }
  if (el.pmModal) {
    el.pmModal.addEventListener("click", (e) => {
      if (e.target.closest("[data-pm-close]")) closePmModal();
    });
  }
  if (el.pmDetailModal) {
    el.pmDetailModal.addEventListener("click", (e) => {
      if (e.target.closest("[data-pm-detail-close]")) closePmDetailModal();
    });
  }
  if (el.btnSavePmRecord) {
    el.btnSavePmRecord.addEventListener("click", () => savePmRecord().catch(console.error));
  }
  if (el.pmBody) {
    el.pmBody.addEventListener("click", (e) => {
      const recordsBtn = e.target.closest("[data-pm-records]");
      if (recordsBtn) {
        openPmRecords(recordsBtn.dataset.pmRecords).catch((err) =>
          alert(err.message || "Gagal membuka service record")
        );
        return;
      }
      const editBtn = e.target.closest("[data-pm-edit]");
      if (editBtn) {
        editPmSchedule(editBtn.dataset.pmEdit).catch((err) =>
          alert(err.message || "Gagal membuka form")
        );
        return;
      }
      const delBtn = e.target.closest("[data-pm-del]");
      if (delBtn) {
        deletePmSchedule(delBtn.dataset.pmDel).catch((err) =>
          alert(err.message || "Gagal menghapus")
        );
      }
    });
  }
  if (el.pmRecordsBody) {
    el.pmRecordsBody.addEventListener("click", (e) => {
      const delBtn = e.target.closest("[data-pm-record-del]");
      if (delBtn) {
        deletePmRecord(delBtn.dataset.pmRecordDel).catch((err) =>
          alert(err.message || "Gagal menghapus")
        );
      }
    });
  }

  let techCache = [];

  function selectedTechSkills() {
    if (!el.techSkillOptions) return [];
    return Array.from(el.techSkillOptions.querySelectorAll('input[type="checkbox"]:checked')).map(
      (n) => n.value
    );
  }

  function setTechSkills(skills) {
    if (!el.techSkillOptions) return;
    const set = new Set(skills || []);
    el.techSkillOptions.querySelectorAll('input[type="checkbox"]').forEach((input) => {
      input.checked = set.has(input.value);
    });
  }

  function openTechModal() {
    if (!el.techModal) return;
    el.techModal.hidden = false;
    document.body.style.overflow = "hidden";
    el.techName?.focus();
  }

  function closeTechModal() {
    if (!el.techModal) return;
    el.techModal.hidden = true;
    document.body.style.overflow = "";
    setMsg(el.techSaveMsg, "");
  }

  function resetTechForm() {
    if (el.techEditId) el.techEditId.value = "";
    if (el.techFormTitle) el.techFormTitle.textContent = "Tambah Teknisi";
    if (el.techName) el.techName.value = "";
    if (el.techPhone) el.techPhone.value = "";
    if (el.techEmail) el.techEmail.value = "";
    if (el.techTelegram) el.techTelegram.value = "";
    setTechSkills([]);
    setMsg(el.techSaveMsg, "");
  }

  function fillTechForm(tech) {
    if (!tech) {
      resetTechForm();
      openTechModal();
      return;
    }
    if (el.techEditId) el.techEditId.value = tech.id || "";
    if (el.techFormTitle) el.techFormTitle.textContent = "Edit Teknisi";
    if (el.techName) el.techName.value = tech.name || "";
    if (el.techPhone) el.techPhone.value = tech.phone || "";
    if (el.techEmail) el.techEmail.value = tech.email || "";
    if (el.techTelegram) el.techTelegram.value = tech.telegram_id || "";
    setTechSkills(tech.skills || []);
    setMsg(el.techSaveMsg, "");
    openTechModal();
  }

  function renderTechTable(list) {
    techCache = list || [];
    if (el.techSummary) el.techSummary.textContent = `${techCache.length} teknisi`;
    if (!el.techBody) return;
    if (!techCache.length) {
      el.techBody.innerHTML =
        '<tr><td colspan="6" class="muted">Belum ada teknisi. Klik Tambah Teknisi untuk menambahkan.</td></tr>';
      return;
    }
    el.techBody.innerHTML = techCache
      .map((t) => {
        const skills = (t.skills || [])
          .map((s) => `<span class="skill-tag">${escapeHtml(s)}</span>`)
          .join("") || "—";
        return `<tr>
          <td><div class="report-title">${escapeHtml(t.name || "—")}</div></td>
          <td>${escapeHtml(t.phone || "—")}</td>
          <td>${escapeHtml(t.email || "—")}</td>
          <td>${escapeHtml(t.telegram_id || "—")}</td>
          <td><div class="skill-tags">${skills}</div></td>
          <td>
            <div class="assets-actions">
              <button type="button" data-tech-edit="${escapeHtml(t.id)}">Edit</button>
              <button type="button" class="danger" data-tech-del="${escapeHtml(t.id)}">Hapus</button>
            </div>
          </td>
        </tr>`;
      })
      .join("");
  }

  async function loadTechnicians() {
    const res = await fetch("/api/technicians", { cache: "no-store" });
    const data = await res.json();
    if (!res.ok || !data.ok) throw new Error(data.error || "Gagal memuat teknisi");
    renderTechTable(data.technicians || []);
  }

  async function saveTechnician() {
    const editId = el.techEditId?.value || "";
    const payload = {
      name: el.techName?.value?.trim() || "",
      phone: el.techPhone?.value?.trim() || "",
      email: el.techEmail?.value?.trim() || "",
      telegram_id: el.techTelegram?.value?.trim() || "",
      skills: selectedTechSkills(),
    };
    if (!payload.name) {
      setMsg(el.techSaveMsg, "Nama teknisi wajib diisi", "danger");
      return;
    }
    if (!payload.skills.length) {
      setMsg(el.techSaveMsg, "Pilih minimal satu keahlian", "danger");
      return;
    }
    if (el.btnSaveTech) el.btnSaveTech.disabled = true;
    setMsg(el.techSaveMsg, "Menyimpan…");
    try {
      const url = editId ? `/api/technicians/${encodeURIComponent(editId)}` : "/api/technicians";
      const res = await fetch(url, {
        method: editId ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok || !data.ok) throw new Error(data.error || "Gagal menyimpan");
      setMsg(el.techSaveMsg, "Tersimpan", "ok");
      await loadTechnicians();
      closeTechModal();
      resetTechForm();
    } catch (err) {
      setMsg(el.techSaveMsg, err.message || "Gagal menyimpan", "danger");
    } finally {
      if (el.btnSaveTech) el.btnSaveTech.disabled = false;
    }
  }

  async function deleteTechnician(id) {
    const tech = techCache.find((t) => t.id === id);
    const label = tech?.name || id;
    if (!window.confirm(`Hapus teknisi "${label}"?`)) return;
    const res = await fetch(`/api/technicians/${encodeURIComponent(id)}`, { method: "DELETE" });
    const data = await res.json();
    if (!res.ok || !data.ok) throw new Error(data.error || "Gagal menghapus");
    if (el.techEditId?.value === id) {
      closeTechModal();
      resetTechForm();
    }
    await loadTechnicians();
  }

  if (el.btnSaveTech) {
    el.btnSaveTech.addEventListener("click", () => saveTechnician().catch(console.error));
  }
  if (el.btnNewTech) {
    el.btnNewTech.addEventListener("click", () => {
      resetTechForm();
      openTechModal();
    });
  }
  if (el.techModal) {
    el.techModal.addEventListener("click", (e) => {
      if (e.target.closest("[data-tech-close]")) closeTechModal();
    });
  }
  if (el.techBody) {
    el.techBody.addEventListener("click", (e) => {
      const editBtn = e.target.closest("[data-tech-edit]");
      if (editBtn) {
        fillTechForm(techCache.find((t) => t.id === editBtn.dataset.techEdit));
        return;
      }
      const delBtn = e.target.closest("[data-tech-del]");
      if (delBtn) {
        deleteTechnician(delBtn.dataset.techDel).catch((err) => {
          alert(err.message || "Gagal menghapus");
        });
      }
    });
  }

  function setMsg(node, text, kind) {
    if (!node) return;
    node.textContent = text || "";
    node.className = kind ? `meta-save-msg ${kind}` : "meta-save-msg";
  }

  function collectNotifyPayload() {
    return {
      email: {
        enabled: !!el.emailEnabled?.checked,
        smtp_host: el.emailSmtpHost?.value?.trim() || "smtp.gmail.com",
        smtp_port: Number(el.emailSmtpPort?.value || 587),
        smtp_user: el.emailSmtpUser?.value?.trim() || "",
        smtp_password: el.emailSmtpPassword?.value || "",
        from_name: el.emailFromName?.value?.trim() || "Simplo Monitor",
        from_email: el.emailFromEmail?.value?.trim() || "",
        to_emails: el.emailTo?.value?.trim() || "",
        use_tls: true,
      },
      telegram: {
        enabled: !!el.tgEnabled?.checked,
        bot_token: el.tgBotToken?.value || "",
        chat_ids: el.tgChatIds?.value?.trim() || "",
      },
    };
  }

  function fillNotifySettings(settings) {
    const email = settings?.email || {};
    const tg = settings?.telegram || {};
    if (el.emailEnabled) el.emailEnabled.checked = !!email.enabled;
    if (el.emailSmtpHost) el.emailSmtpHost.value = email.smtp_host || "smtp.gmail.com";
    if (el.emailSmtpPort) el.emailSmtpPort.value = email.smtp_port || 587;
    if (el.emailSmtpUser) el.emailSmtpUser.value = email.smtp_user || "";
    if (el.emailSmtpPassword) {
      el.emailSmtpPassword.value = "";
      el.emailSmtpPassword.placeholder = email.has_password
        ? "App password tersimpan (kosongkan jika tidak diubah)"
        : "xxxx xxxx xxxx xxxx";
    }
    if (el.emailFromName) el.emailFromName.value = email.from_name || "Simplo Monitor";
    if (el.emailFromEmail) el.emailFromEmail.value = email.from_email || "";
    if (el.emailTo) el.emailTo.value = email.to_emails || "";
    if (el.tgEnabled) el.tgEnabled.checked = !!tg.enabled;
    if (el.tgBotToken) {
      el.tgBotToken.value = "";
      el.tgBotToken.placeholder = tg.has_token
        ? "Token tersimpan (kosongkan jika tidak diubah)"
        : "123456:ABC-DEF...";
    }
    if (el.tgChatIds) el.tgChatIds.value = tg.chat_ids || "";
  }

  async function loadNotifySettings() {
    const res = await fetch("/api/settings/notifications", { cache: "no-store" });
    const data = await res.json();
    if (!res.ok || !data.ok) throw new Error(data.error || "Gagal memuat setting");
    fillNotifySettings(data.settings || {});
  }

  async function saveNotifySettings(which) {
    const payload = collectNotifyPayload();
    const msgEl = which === "telegram" ? el.tgSaveMsg : el.emailSaveMsg;
    const btn = which === "telegram" ? el.btnSaveTelegram : el.btnSaveEmail;
    if (btn) btn.disabled = true;
    setMsg(msgEl, "Menyimpan…");
    try {
      const res = await fetch("/api/settings/notifications", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok || !data.ok) throw new Error(data.error || "Gagal menyimpan");
      fillNotifySettings(data.settings || {});
      setMsg(msgEl, "Tersimpan", "ok");
    } catch (err) {
      setMsg(msgEl, err.message || "Gagal menyimpan", "danger");
    } finally {
      if (btn) btn.disabled = false;
    }
  }

  async function testNotify(kind) {
    const payload = collectNotifyPayload();
    const msgEl = kind === "telegram" ? el.tgSaveMsg : el.emailSaveMsg;
    const btn = kind === "telegram" ? el.btnTestTelegram : el.btnTestEmail;
    const url =
      kind === "telegram"
        ? "/api/settings/notifications/test-telegram"
        : "/api/settings/notifications/test-email";
    if (btn) btn.disabled = true;
    setMsg(msgEl, "Mengirim tes…");
    try {
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok || data.ok === false) throw new Error(data.error || "Gagal mengirim tes");
      const dest = (data.sent_to || []).join(", ");
      setMsg(msgEl, dest ? `Tes terkirim ke ${dest}` : "Tes terkirim", "ok");
    } catch (err) {
      setMsg(msgEl, err.message || "Gagal mengirim tes", "danger");
    } finally {
      if (btn) btn.disabled = false;
    }
  }

  let userCache = [];
  let userMenuChoices = [];

  function selectedUserMenus() {
    if (!el.userMenuOptions) return [];
    return Array.from(el.userMenuOptions.querySelectorAll('input[type="checkbox"]:checked')).map(
      (n) => n.value
    );
  }

  function renderUserMenuOptions(selected = []) {
    if (!el.userMenuOptions) return;
    const opts = userMenuChoices.length
      ? userMenuChoices
      : [
          { id: "dashboard", label: "Dashboard" },
          { id: "assets", label: "Manajemen Asset" },
          { id: "wo", label: "Work Order" },
          { id: "pm", label: "Jadwal PM" },
          { id: "team", label: "Tim Teknisi" },
          { id: "statistik", label: "Statistik" },
          { id: "report", label: "Laporan" },
          { id: "notify", label: "Setting Notifikasi" },
        ];
    const selectedSet = new Set(selected || []);
    el.userMenuOptions.innerHTML = opts
      .map(
        (m) => `<label class="skill-chip"><input type="checkbox" value="${escapeHtml(m.id)}" ${
          selectedSet.has(m.id) ? "checked" : ""
        } /> ${escapeHtml(m.label)}</label>`
      )
      .join("");
  }

  function syncUserRoleUi() {
    const isAdmin = el.userRole?.value === "administrator";
    if (el.userMenuBox) el.userMenuBox.hidden = !!isAdmin;
  }

  function openUserModal() {
    if (!el.userModal) return;
    el.userModal.hidden = false;
    document.body.style.overflow = "hidden";
  }

  function closeUserModal() {
    if (!el.userModal) return;
    el.userModal.hidden = true;
    document.body.style.overflow = "";
    setMsg(el.userSaveMsg, "");
  }

  function resetUserForm() {
    if (el.userEditId) el.userEditId.value = "";
    if (el.userUsername) el.userUsername.value = "";
    if (el.userFullName) el.userFullName.value = "";
    if (el.userPassword) {
      el.userPassword.value = "";
      el.userPassword.placeholder = "Minimal 6 karakter";
    }
    if (el.userRole) el.userRole.value = "operator";
    if (el.userActive) el.userActive.checked = true;
    if (el.userFormTitle) el.userFormTitle.textContent = "Tambah User";
    renderUserMenuOptions(["dashboard"]);
    syncUserRoleUi();
    setMsg(el.userSaveMsg, "");
  }

  function fillUserForm(user) {
    if (el.userEditId) el.userEditId.value = user.id || "";
    if (el.userUsername) el.userUsername.value = user.username || "";
    if (el.userFullName) el.userFullName.value = user.full_name || "";
    if (el.userPassword) {
      el.userPassword.value = "";
      el.userPassword.placeholder = "Kosongkan jika tidak diubah";
    }
    if (el.userRole) el.userRole.value = user.role || "operator";
    if (el.userActive) el.userActive.checked = user.active !== false;
    if (el.userFormTitle) el.userFormTitle.textContent = "Edit User";
    renderUserMenuOptions(user.menus || []);
    syncUserRoleUi();
    setMsg(el.userSaveMsg, "");
  }

  function renderUserTable(list) {
    userCache = list || [];
    if (el.userSummary) el.userSummary.textContent = `${userCache.length} user`;
    if (!el.userBody) return;
    if (!userCache.length) {
      el.userBody.innerHTML =
        '<tr><td colspan="6" class="muted">Belum ada user. Klik Tambah User untuk menambah.</td></tr>';
      return;
    }
    el.userBody.innerHTML = userCache
      .map((u) => {
        const roleLabel = u.role === "administrator" ? "Administrator" : "Operator";
        const menus =
          u.role === "administrator"
            ? "Semua menu"
            : (u.menus || []).join(", ") || "—";
        const active = u.active !== false;
        return `<tr>
          <td><div class="report-title">${escapeHtml(u.username || "—")}</div></td>
          <td>${escapeHtml(u.full_name || "—")}</td>
          <td><span class="skill-tag">${escapeHtml(roleLabel)}</span></td>
          <td><div class="wo-stack">${escapeHtml(menus)}</div></td>
          <td><span class="meta-status-badge ${active ? "ok" : "danger"}">${
            active ? "Aktif" : "Nonaktif"
          }</span></td>
          <td>
            <div class="assets-actions">
              <button type="button" data-user-edit="${escapeHtml(u.id)}">Edit</button>
              <button type="button" class="danger" data-user-del="${escapeHtml(u.id)}">Hapus</button>
            </div>
          </td>
        </tr>`;
      })
      .join("");
  }

  async function loadUsers() {
    const res = await fetch("/api/users", { cache: "no-store" });
    const data = await res.json();
    if (!res.ok || !data.ok) throw new Error(data.error || "Gagal memuat user");
    userMenuChoices = data.menu_options || [];
    renderUserTable(data.users || []);
  }

  async function saveUser() {
    const id = el.userEditId?.value || "";
    const payload = {
      username: el.userUsername?.value?.trim() || "",
      full_name: el.userFullName?.value?.trim() || "",
      role: el.userRole?.value || "operator",
      active: !!el.userActive?.checked,
      menus: selectedUserMenus(),
    };
    const password = el.userPassword?.value || "";
    if (password) payload.password = password;
    if (!payload.username) {
      setMsg(el.userSaveMsg, "Username wajib diisi", "danger");
      return;
    }
    if (!id && !password) {
      setMsg(el.userSaveMsg, "Password wajib diisi", "danger");
      return;
    }
    if (payload.role === "operator" && !payload.menus.length) {
      setMsg(el.userSaveMsg, "Pilih minimal satu menu untuk operator", "danger");
      return;
    }
    if (el.btnSaveUser) el.btnSaveUser.disabled = true;
    setMsg(el.userSaveMsg, "Menyimpan…");
    try {
      const res = await fetch(id ? `/api/users/${encodeURIComponent(id)}` : "/api/users", {
        method: id ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok || !data.ok) throw new Error(data.error || "Gagal menyimpan");
      setMsg(el.userSaveMsg, "Tersimpan", "ok");
      await loadUsers();
      closeUserModal();
      resetUserForm();
    } catch (err) {
      setMsg(el.userSaveMsg, err.message || "Gagal menyimpan", "danger");
    } finally {
      if (el.btnSaveUser) el.btnSaveUser.disabled = false;
    }
  }

  async function deleteUser(id) {
    const user = userCache.find((u) => u.id === id);
    const label = user?.username || id;
    if (!window.confirm(`Hapus user "${label}"?`)) return;
    const res = await fetch(`/api/users/${encodeURIComponent(id)}`, { method: "DELETE" });
    const data = await res.json();
    if (!res.ok || !data.ok) throw new Error(data.error || "Gagal menghapus");
    await loadUsers();
  }

  if (el.btnNewUser) {
    el.btnNewUser.addEventListener("click", () => {
      resetUserForm();
      openUserModal();
    });
  }
  if (el.btnSaveUser) {
    el.btnSaveUser.addEventListener("click", () => saveUser().catch(console.error));
  }
  if (el.userRole) {
    el.userRole.addEventListener("change", syncUserRoleUi);
  }
  if (el.userModal) {
    el.userModal.addEventListener("click", (e) => {
      if (e.target.closest("[data-user-close]")) closeUserModal();
    });
  }
  if (el.userBody) {
    el.userBody.addEventListener("click", (e) => {
      const editBtn = e.target.closest("[data-user-edit]");
      if (editBtn) {
        const user = userCache.find((u) => u.id === editBtn.dataset.userEdit);
        if (!user) return;
        fillUserForm(user);
        openUserModal();
        return;
      }
      const delBtn = e.target.closest("[data-user-del]");
      if (delBtn) {
        deleteUser(delBtn.dataset.userDel).catch((err) =>
          alert(err.message || "Gagal menghapus")
        );
      }
    });
  }

  function showView(view) {
    if (!canAccessMenu(view) && view !== "dashboard") {
      view = firstAllowedView();
    }
    if (view === "dashboard" && !canAccessMenu("dashboard")) {
      view = firstAllowedView();
    }
    state.view = view;
    const siteName = state.meta.site_name || "CMMS";
    const site = state.meta.site_site || el.siteSite?.textContent || "Menara SVT";
    el.viewDashboard.hidden = true;
    el.viewReport.hidden = true;
    el.viewStatistik.hidden = true;
    if (el.viewNotify) el.viewNotify.hidden = true;
    if (el.viewAssets) el.viewAssets.hidden = true;
    if (el.viewTeam) el.viewTeam.hidden = true;
    if (el.viewWo) el.viewWo.hidden = true;
    if (el.viewPm) el.viewPm.hidden = true;
    if (el.viewUsers) el.viewUsers.hidden = true;
    el.btnWall.hidden = true;

    document.querySelectorAll(".nav-item").forEach((n) => {
      n.classList.toggle("active", n.dataset.nav === view);
    });

    if (view === "report") {
      el.viewReport.hidden = false;
      el.pageTitle.innerHTML = `Laporan Histori Gangguan — <span id="siteSite">${escapeHtml(site)}</span>`;
      initReportDates();
      loadReports().catch(console.error);
    } else if (view === "statistik") {
      el.viewStatistik.hidden = false;
      el.pageTitle.innerHTML = `Statistik Uptime — <span id="siteSite">${escapeHtml(site)}</span>`;
      initStatDates();
      loadStatistik().catch(console.error);
    } else if (view === "notify") {
      if (el.viewNotify) el.viewNotify.hidden = false;
      el.pageTitle.innerHTML = `Setting Notifikasi — <span id="siteSite">${escapeHtml(site)}</span>`;
      loadNotifySettings().catch((err) => {
        setMsg(el.emailSaveMsg, err.message || "Gagal memuat setting", "danger");
      });
    } else if (view === "assets") {
      if (el.viewAssets) el.viewAssets.hidden = false;
      el.pageTitle.innerHTML = `Manajemen Asset — <span id="siteSite">${escapeHtml(site)}</span>`;
      closeAssetModal();
      loadAssets().catch((err) => {
        if (el.assetsSummary) el.assetsSummary.textContent = err.message || "Gagal memuat aset";
      });
    } else if (view === "team") {
      if (el.viewTeam) el.viewTeam.hidden = false;
      el.pageTitle.innerHTML = `Tim Teknisi — <span id="siteSite">${escapeHtml(site)}</span>`;
      closeTechModal();
      loadTechnicians().catch((err) => {
        if (el.techSummary) el.techSummary.textContent = err.message || "Gagal memuat teknisi";
      });
    } else if (view === "wo") {
      if (el.viewWo) el.viewWo.hidden = false;
      el.pageTitle.innerHTML = `Work Order — <span id="siteSite">${escapeHtml(site)}</span>`;
      closeWoModal();
      loadAutoWoSettings().catch((err) => {
        setMsg(el.woAutoMsg, err.message || "Gagal memuat setting", "danger");
      });
      loadWorkOrders().catch((err) => {
        if (el.woSummary) el.woSummary.textContent = err.message || "Gagal memuat work order";
      });
    } else if (view === "pm") {
      if (el.viewPm) el.viewPm.hidden = false;
      el.pageTitle.innerHTML = `Jadwal PM — <span id="siteSite">${escapeHtml(site)}</span>`;
      closePmModal();
      closePmDetailModal();
      loadPmSchedules().catch((err) => {
        if (el.pmSummary) el.pmSummary.textContent = err.message || "Gagal memuat jadwal PM";
      });
    } else if (view === "users") {
      if (el.viewUsers) el.viewUsers.hidden = false;
      el.pageTitle.innerHTML = `User Management — <span id="siteSite">${escapeHtml(site)}</span>`;
      closeUserModal();
      loadUsers().catch((err) => {
        if (el.userSummary) el.userSummary.textContent = err.message || "Gagal memuat user";
      });
    } else {
      el.viewDashboard.hidden = false;
      el.btnWall.hidden = false;
      el.pageTitle.innerHTML = `${escapeHtml(siteName)} - <span id="siteSite">${escapeHtml(site)}</span>`;
    }
  }

  function isoDate(d) {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${y}-${m}-${day}`;
  }

  function initReportDates() {
    if (!el.reportFrom.value) {
      const to = new Date();
      const from = new Date();
      from.setDate(from.getDate() - 7);
      el.reportFrom.value = isoDate(from);
      el.reportTo.value = isoDate(to);
    }
  }

  function initStatDates() {
    if (!el.statFrom.value) {
      const to = new Date();
      const from = new Date();
      from.setDate(from.getDate() - 7);
      el.statFrom.value = isoDate(from);
      el.statTo.value = isoDate(to);
    }
  }

  function formatDuration(seconds) {
    const s = Math.max(0, Math.round(Number(seconds) || 0));
    const d = Math.floor(s / 86400);
    const h = Math.floor((s % 86400) / 3600);
    const m = Math.floor((s % 3600) / 60);
    if (d > 0) return `${d} hari ${h} jam`;
    if (h > 0) return `${h} jam ${m} mnt`;
    if (m > 0) return `${m} mnt`;
    return `${s} dtk`;
  }

  function pctClass(pct) {
    if (pct >= 95) return "good";
    if (pct >= 80) return "warn";
    return "bad";
  }

  function fillDeviceSelect(selectEl, devices, selected) {
    const current = selected || selectEl.value || "all";
    selectEl.innerHTML =
      `<option value="all">Semua perangkat</option>` +
      (devices || [])
        .map(
          (d) =>
            `<option value="${escapeAttr(d.id)}" ${d.id === current ? "selected" : ""}>${escapeHtml(
              d.name
            )}</option>`
        )
        .join("");
  }

  function renderTimelineRibbon(timeline, filters) {
    const segs = timeline || [];
    if (!segs.length) {
      el.statTimelineRibbon.innerHTML = `<div class="seg empty" title="Tidak ada data"></div>`;
      el.statTimelineAxis.innerHTML = `
        <span>${escapeHtml(filters?.from || "—")}</span>
        <span>${escapeHtml(filters?.to || "—")}</span>`;
      return;
    }

    const total = segs.reduce((acc, s) => acc + (Number(s.seconds) || 0), 0) || 1;
    el.statTimelineRibbon.innerHTML = segs
      .map((s) => {
        const pct = Math.max(((Number(s.seconds) || 0) / total) * 100, 0.15);
        const label = healthLabel[s.state] || s.state;
        const tip = s.healthy_pct != null
          ? `${s.start?.slice(0, 10) || ""} · Sehat ${s.healthy_pct}%`
          : `${formatTs(s.start)} → ${formatTs(s.end)} · ${label} (${formatDuration(s.seconds)})`;
        return `<div class="seg ${escapeAttr(s.state || "healthy")}" style="width:${pct}%" title="${escapeAttr(tip)}"></div>`;
      })
      .join("");

    el.statTimelineAxis.innerHTML = `
      <span>${escapeHtml(filters?.from || segs[0]?.start?.slice(0, 10) || "—")}</span>
      <span>${escapeHtml(filters?.to || segs[segs.length - 1]?.end?.slice(0, 10) || "—")}</span>`;
  }

  function drawDailyChart(daily) {
    const canvas = el.statDailyChart;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    const cssW = canvas.clientWidth || 900;
    const cssH = 220;
    canvas.width = Math.floor(cssW * dpr);
    canvas.height = Math.floor(cssH * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, cssW, cssH);

    const rows = daily || [];
    const pad = { top: 18, right: 12, bottom: 36, left: 40 };
    const plotW = cssW - pad.left - pad.right;
    const plotH = cssH - pad.top - pad.bottom;

    ctx.fillStyle = "#fff";
    ctx.fillRect(0, 0, cssW, cssH);

    // grid
    ctx.strokeStyle = "#e2e8f0";
    ctx.lineWidth = 1;
    ctx.fillStyle = "#6b7a8d";
    ctx.font = "11px Plus Jakarta Sans, Segoe UI, sans-serif";
    ctx.textAlign = "right";
    for (let i = 0; i <= 4; i++) {
      const y = pad.top + (plotH * i) / 4;
      const val = 100 - i * 25;
      ctx.beginPath();
      ctx.moveTo(pad.left, y);
      ctx.lineTo(pad.left + plotW, y);
      ctx.stroke();
      ctx.fillText(`${val}%`, pad.left - 8, y + 3);
    }

    if (!rows.length) {
      ctx.fillStyle = "#6b7a8d";
      ctx.textAlign = "center";
      ctx.font = "13px Plus Jakarta Sans, Segoe UI, sans-serif";
      ctx.fillText("Tidak ada data harian untuk rentang ini", cssW / 2, cssH / 2);
      return;
    }

    const gap = Math.min(10, plotW / rows.length / 4);
    const barW = Math.max(6, plotW / rows.length - gap);
    const colors = { healthy: "#1f9d55", attention: "#f0782a", issue: "#e5484d" };

    rows.forEach((row, idx) => {
      const total =
        (Number(row.healthy_seconds) || 0) +
        (Number(row.attention_seconds) || 0) +
        (Number(row.issue_seconds) || 0) || 1;
      const x = pad.left + idx * (barW + gap) + gap / 2;
      let y = pad.top + plotH;
      const stack = [
        ["issue", row.issue_seconds],
        ["attention", row.attention_seconds],
        ["healthy", row.healthy_seconds],
      ];
      stack.forEach(([key, sec]) => {
        const h = (Number(sec) / total) * plotH;
        y -= h;
        ctx.fillStyle = colors[key];
        ctx.fillRect(x, y, barW, Math.max(h, 0));
      });

      // label
      ctx.fillStyle = "#6b7a8d";
      ctx.textAlign = "center";
      ctx.font = "10px Plus Jakarta Sans, Segoe UI, sans-serif";
      const label = (row.date || "").slice(5); // MM-DD
      ctx.fillText(label, x + barW / 2, cssH - 14);

      // healthy % on top
      ctx.fillStyle = "#1a2433";
      ctx.font = "600 10px Plus Jakarta Sans, Segoe UI, sans-serif";
      ctx.fillText(`${row.healthy_pct ?? 0}%`, x + barW / 2, pad.top - 4);
    });
  }

  function renderStatistik() {
    const data = state.statistik || {};
    const summary = data.summary || {};
    const filters = data.filters || {};
    const devices = data.devices || [];
    const perDevice = data.per_device || [];

    fillDeviceSelect(el.statDevice, devices, filters.device || "all");

    el.kpiHealthyPct.textContent = summary.healthy_pct != null ? summary.healthy_pct : "—";
    el.kpiUptimePct.textContent = summary.uptime_pct != null ? summary.uptime_pct : "—";
    el.kpiDowntimePct.textContent = summary.downtime_pct != null ? summary.downtime_pct : "—";
    el.kpiDeviceCount.textContent = summary.device_count ?? 0;
    el.kpiHealthySub.textContent = `${filters.from || "—"} s/d ${filters.to || "—"}`;
    el.kpiDowntimeSub.textContent = `Gangguan · ${formatDuration(summary.issue_seconds || 0)}`;
    el.kpiRangeLabel.textContent = formatDuration(summary.range_seconds || 0);

    renderTimelineRibbon(data.timeline || [], filters);
    drawDailyChart(data.daily || []);

    el.statSummary.textContent =
      `${perDevice.length} perangkat · Sehat ${summary.healthy_pct ?? 0}% · ` +
      `Uptime ${summary.uptime_pct ?? 0}% · Downtime ${summary.downtime_pct ?? 0}%`;

    if (!perDevice.length) {
      el.statDeviceBody.innerHTML =
        `<tr><td colspan="5" class="muted">Tidak ada data statistik untuk filter ini.</td></tr>`;
      return;
    }

    el.statDeviceBody.innerHTML = perDevice
      .map((d) => {
        const total =
          (Number(d.healthy_seconds) || 0) +
          (Number(d.attention_seconds) || 0) +
          (Number(d.issue_seconds) || 0) || 1;
        const hw = ((d.healthy_seconds || 0) / total) * 100;
        const aw = ((d.attention_seconds || 0) / total) * 100;
        const iw = ((d.issue_seconds || 0) / total) * 100;
        return `
          <tr>
            <td><strong>${escapeHtml(d.name)}</strong></td>
            <td class="pct-cell ${pctClass(d.healthy_pct)}">${d.healthy_pct}%</td>
            <td class="pct-cell ${pctClass(d.uptime_pct)}">${d.uptime_pct}%</td>
            <td class="pct-cell ${d.downtime_pct > 5 ? "bad" : ""}">${d.downtime_pct}%</td>
            <td>
              <div class="dist-bar" title="Sehat ${formatDuration(d.healthy_seconds)} · Perhatian ${formatDuration(d.attention_seconds)} · Gangguan ${formatDuration(d.issue_seconds)}">
                <span class="h" style="width:${hw}%"></span>
                <span class="a" style="width:${aw}%"></span>
                <span class="i" style="width:${iw}%"></span>
              </div>
            </td>
          </tr>`;
      })
      .join("");
  }

  async function loadStatistik() {
    const params = new URLSearchParams();
    if (el.statFrom.value) params.set("from", el.statFrom.value);
    if (el.statTo.value) params.set("to", el.statTo.value);
    if (el.statDevice.value && el.statDevice.value !== "all") {
      params.set("device", el.statDevice.value);
    }
    const res = await fetch(`/api/statistik?${params.toString()}`, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    state.statistik = data;
    if (data.filters?.from) el.statFrom.value = data.filters.from;
    if (data.filters?.to) el.statTo.value = data.filters.to;
    renderStatistik();
  }

  function eventTypeLabel(t) {
    return (
      {
        started: "Gangguan mulai",
        resolved: "Kembali normal",
        attention_started: "Perhatian mulai",
        attention_resolved: "Perhatian selesai",
        detected: "Terdeteksi",
      }[t] || t
    );
  }

  function formatTs(ts) {
    const d = new Date(ts);
    if (Number.isNaN(d.getTime())) return ts || "—";
    return d.toLocaleString("id-ID", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  }

  function renderReport() {
    const logs = state.report.logs || [];
    const devices = state.report.devices || [];
    const selected = el.reportDevice.value || "all";

    el.reportDevice.innerHTML =
      `<option value="all">Semua device</option>` +
      devices
        .map(
          (d) =>
            `<option value="${escapeAttr(d.id)}" ${d.id === selected ? "selected" : ""}>${escapeHtml(
              d.name
            )}</option>`
        )
        .join("");

    el.reportSummary.textContent = `${logs.length} entri histori` +
      (el.reportFrom.value ? ` · ${el.reportFrom.value} s/d ${el.reportTo.value || "—"}` : "");

    if (!logs.length) {
      el.reportBody.innerHTML =
        `<tr><td colspan="6" class="muted">Tidak ada histori gangguan untuk filter ini.</td></tr>`;
      return;
    }

    el.reportBody.innerHTML = logs
      .map((row) => {
        const kind = eventTypeLabel(row.event_type);
        return `
          <tr>
            <td>${escapeHtml(formatTs(row.ts))}</td>
            <td><span class="tag ${escapeAttr(row.event_type)}">${escapeHtml(kind)}</span></td>
            <td><strong>${escapeHtml(row.device_name)}</strong><div class="muted" style="font-size:11px">${escapeHtml(row.ip || "")}</div></td>
            <td>${escapeHtml(row.location || "—")}</td>
            <td class="report-status">${escapeHtml(row.status_from || "-")} → ${escapeHtml(row.status_to || "-")}</td>
            <td>
              <div class="report-title">${escapeHtml(row.title)}</div>
              <div class="report-detail">${escapeHtml(row.detail)}</div>
            </td>
          </tr>`;
      })
      .join("");
  }

  async function loadReports() {
    const params = new URLSearchParams();
    if (el.reportFrom.value) params.set("from", el.reportFrom.value);
    if (el.reportTo.value) params.set("to", el.reportTo.value);
    if (el.reportDevice.value && el.reportDevice.value !== "all") {
      params.set("device", el.reportDevice.value);
    }
    const res = await fetch(`/api/reports?${params.toString()}`, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    state.report = data;
    if (data.filters?.from) el.reportFrom.value = data.filters.from;
    if (data.filters?.to) el.reportTo.value = data.filters.to;
    renderReport();
  }

  el.btnReportApply.addEventListener("click", () => {
    loadReports().catch((err) => {
      el.reportBody.innerHTML = `<tr><td colspan="6" class="muted">Gagal memuat: ${escapeHtml(
        err.message
      )}</td></tr>`;
    });
  });

  el.btnStatApply.addEventListener("click", () => {
    loadStatistik().catch((err) => {
      el.statSummary.textContent = `Gagal memuat: ${err.message}`;
      el.statDeviceBody.innerHTML = `<tr><td colspan="5" class="muted">Gagal memuat: ${escapeHtml(
        err.message
      )}</td></tr>`;
    });
  });

  window.addEventListener("resize", () => {
    if (state.view === "statistik") {
      drawDailyChart(state.statistik?.daily || []);
    }
  });

  el.btnExportPdf.addEventListener("click", () => {
    const params = new URLSearchParams();
    if (el.reportFrom.value) params.set("from", el.reportFrom.value);
    if (el.reportTo.value) params.set("to", el.reportTo.value);
    if (el.reportDevice.value && el.reportDevice.value !== "all") {
      params.set("device", el.reportDevice.value);
    }
    window.location.href = `/api/reports/export.pdf?${params.toString()}`;
  });

  // Boot
  tickClock();
  setInterval(tickClock, 1000);

  async function bootApp() {
    const meRes = await fetch("/api/auth/me", { cache: "no-store" });
    if (!meRes.ok) {
      window.location.replace("/login");
      return;
    }
    const meData = await meRes.json();
    if (!meData.ok || !meData.user) {
      window.location.replace("/login");
      return;
    }
    state.user = meData.user;
    state.menuOptions = meData.menu_options || [];
    applyCurrentUser();
    applyNavAccess();
    showView(firstAllowedView());

    await loadStatus();
    const uiPollMs = 5000;
    setInterval(() => {
      if (state.view === "dashboard" || canAccessMenu("dashboard")) {
        loadStatus().catch(console.error);
      }
    }, uiPollMs);
  }

  bootApp().catch((err) => {
    if (String(err.message || "").includes("login") || err.name === "TypeError") {
      window.location.replace("/login");
      return;
    }
    el.errorBanner.hidden = false;
    el.errorBanner.textContent = `Gagal memuat data: ${err.message}`;
  });
})();

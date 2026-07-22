/* ==========================================================================
   AI 行业情报 · 资讯首页 UI 原型
   纯前端演示：不调用任何真实后端、不抓取、不调用 AI
   ========================================================================== */
"use strict";

/* ---------- 模拟数据（6 条不同长度的资讯） ---------- */
var CATEGORIES = [
  "模型与技术动态",
  "智能体与产品更新",
  "企业成果与应用案例",
  "获奖与优秀案例",
  "奖项与成果征集",
  "政策、标准与行业动态",
  "待分类"
];

var ITEMS = [
  {
    id: 101,
    title: "关于组织开展 2026 年人工智能创新应用先导区建设工作的通知",
    category: "政策、标准与行业动态",
    source: "工业和信息化部",
    publishedAt: "2026-07-21 17:02",
    discoveredAt: "2026-07-21 18:40",
    summary:
      "为深入实施“人工智能+”行动，现组织开展 2026 年人工智能创新应用先导区建设工作。申报单位应围绕制造、医疗、交通等重点领域，形成可复制、可推广的典型应用场景，并于 8 月 31 日前完成网上申报。",
    unread: true,
    favorite: false,
    primaryType: "政策标准",
    verification: "官方确认",
    review: "无需审核",
    provider: "规则分类",
    sourceKind: "正式"
  },
  {
    id: 102,
    title: "通义千问 Qwen3-Max 正式发布：万亿参数规模，推理、代码与智能体能力全面提升",
    category: "模型与技术动态",
    source: "通义千问更新日志",
    publishedAt: "2026-07-22 10:15",
    discoveredAt: "2026-07-22 10:31",
    summary:
      "Qwen3-Max 采用混合专家架构，总参数规模超过一万亿，在数学推理、代码生成和长文本理解基准上取得显著提升；同步开放 API，上下文长度支持至 100 万 token，并提供面向智能体场景的工具调用优化。本次更新还包含 Qwen3-Coder 与 Qwen3-VL 两个专项版本，分别面向编程助手与多模态理解场景，企业用户可通过百炼平台直接调用。",
    unread: true,
    favorite: true,
    primaryType: "产品更新",
    verification: "官方确认",
    review: "无需审核",
    provider: "AI 分类",
    sourceKind: "正式"
  },
  {
    id: 103,
    title: "扣子空间上线多智能体协作模式",
    category: "智能体与产品更新",
    source: "扣子产品动态",
    publishedAt: "2026-07-20 14:00",
    discoveredAt: "2026-07-20 15:12",
    summary:
      "新版本支持在一个空间内编排多个智能体协同完成任务，并提供企业级权限管理与审计日志。",
    unread: false,
    favorite: false,
    primaryType: "产品更新",
    verification: "官方链接",
    review: "无需审核",
    provider: "规则分类",
    sourceKind: "正式"
  },
  {
    id: 104,
    title: "国家电网联合百度智能云落地电力巡检大模型：缺陷识别准确率提升至 98.2%，覆盖 27 个省级电网",
    category: "企业成果与应用案例",
    source: "百度智能云案例库",
    publishedAt: "2026-07-19 09:30",
    discoveredAt: "2026-07-19 11:05",
    summary:
      "该项目将多模态大模型应用于输电线路无人机巡检影像分析，实现销钉缺失、绝缘子破损等 42 类缺陷的自动识别，单架次影像分析时长由 2 小时缩短至 8 分钟。项目已在 27 个省级电网规模化部署，累计分析影像超过 1.2 亿张，减少人工复检工作量约 60%，并沉淀了电力行业视觉缺陷数据集与微调工具链，为发电、变电场景复用奠定基础。",
    unread: false,
    favorite: true,
    primaryType: "案例分析",
    verification: "多源确认",
    review: "已通过",
    provider: "AI 分类",
    sourceKind: "正式"
  },
  {
    id: 105,
    title: "关于征集 2026 年度人工智能赋能新型工业化典型应用案例的通知",
    category: "奖项与成果征集",
    source: "中国信通院",
    publishedAt: "2026-07-18 16:45",
    discoveredAt: "2026-07-18 17:20",
    summary:
      "面向研发设计、生产制造、运营管理等环节征集典型应用案例，入选案例将纳入年度案例集并在行业大会发布。申报截止日期为 2026 年 9 月 15 日。",
    unread: true,
    favorite: false,
    primaryType: "申报机会",
    verification: "官方确认",
    review: "无需审核",
    provider: "规则分类",
    sourceKind: "正式"
  },
  {
    id: 106,
    title: "OpenAI releases GPT-5.2 with improved agentic tool use, a 400k context window, and lower latency for enterprise deployments",
    category: "模型与技术动态",
    source: "OpenAI 官方博客",
    publishedAt: "2026-07-22 06:00",
    discoveredAt: "2026-07-22 08:30",
    summary:
      "GPT-5.2 introduces more reliable multi-step tool calling, a 400k-token context window, and new batch API pricing. OpenAI says the model reduces hallucination rates on long-document reasoning tasks by 38% compared with GPT-5.1, and enterprise customers can now pin model versions for 18 months to simplify compliance reviews and regression testing across large deployments.",
    unread: true,
    favorite: false,
    primaryType: "产品更新",
    verification: "官方确认",
    review: "无需审核",
    provider: "AI 分类",
    sourceKind: "正式"
  }
];

/* ---------- 全局状态 ---------- */
var state = {
  view: "a", // "a" 卡片 / "b" 紧凑
  selected: {}, // id -> true
  readOverride: {}, // id -> bool（演示标记已读/未读）
  favOverride: {}, // id -> bool
  categoryOverride: {}, // id -> 新分类名
  expandedSummary: {}, // id -> true
  openEditor: null, // 当前展开分类编辑器的条目 id
  openMore: null, // 当前展开更多信息的条目 id
  rowExpand: null // 方案 B 当前展开面板的条目 id
};

var TOTAL_COUNT = 290;

/* ---------- 工具 ---------- */
function $(sel, root) {
  return (root || document).querySelector(sel);
}

function $all(sel, root) {
  return Array.prototype.slice.call((root || document).querySelectorAll(sel));
}

function esc(text) {
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function getItem(id) {
  for (var i = 0; i < ITEMS.length; i++) {
    if (ITEMS[i].id === id) return ITEMS[i];
  }
  return null;
}

function isRead(item) {
  if (Object.prototype.hasOwnProperty.call(state.readOverride, item.id)) {
    return state.readOverride[item.id];
  }
  return !item.unread;
}

function isFav(item) {
  if (Object.prototype.hasOwnProperty.call(state.favOverride, item.id)) {
    return state.favOverride[item.id];
  }
  return item.favorite;
}

function categoryOf(item) {
  return state.categoryOverride[item.id] || item.category;
}

function selectedIds() {
  return Object.keys(state.selected).map(Number);
}

/* ---------- Toast ---------- */
var toastTimer = null;
function toast(message) {
  var el = $("#toast");
  el.textContent = message;
  el.hidden = false;
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(function () {
    el.hidden = true;
  }, 2600);
}

/* ==========================================================================
   渲染：方案 A（紧凑卡片）
   ========================================================================== */
function categoryChip(item, extraClass) {
  var cat = categoryOf(item);
  var cls = "category-chip" + (cat === "待分类" ? " is-pending" : "") + (extraClass ? " " + extraClass : "");
  return '<span class="' + cls + '">' + esc(cat) + "</span>";
}

function renderCard(item) {
  var read = isRead(item);
  var fav = isFav(item);
  var summaryExpanded = !!state.expandedSummary[item.id];
  var editorOpen = state.openEditor === item.id;
  var moreOpen = state.openMore === item.id;
  var long = item.summary.length > 90;

  var options = CATEGORIES.map(function (c) {
    var sel = c === categoryOf(item) ? " selected" : "";
    return '<option value="' + esc(c) + '"' + sel + ">" + esc(c) + "</option>";
  }).join("");

  return (
    '<article class="item-card' + (read ? "" : " is-unread") + '" data-id="' + item.id + '">' +
      '<div class="item-check"><input type="checkbox" data-select="' + item.id + '"' +
        (state.selected[item.id] ? " checked" : "") + ' aria-label="选择此条资讯"></div>' +
      '<div class="item-body">' +
        '<div class="item-topline">' +
          categoryChip(item) +
          '<span class="item-times"><span>发布 ' + esc(item.publishedAt) + "</span><span>发现 " + esc(item.discoveredAt) + "</span></span>" +
        "</div>" +
        '<h2 class="item-title">' +
          (read ? "" : '<span class="unread-dot" title="未读"></span>') +
          '<a href="#" data-act="open">' + esc(item.title) + "</a>" +
        "</h2>" +
        '<div class="item-source">来源：' + esc(item.source) + "</div>" +
        '<p class="item-summary' + (summaryExpanded ? " is-expanded" : "") + '">' + esc(item.summary) + "</p>" +
        (long
          ? '<button class="summary-toggle" type="button" data-act="toggle-summary">' +
            (summaryExpanded ? "收起" : "展开全部") + "</button>"
          : "") +
        '<div class="item-actions">' +
          '<a class="text-link" href="#" data-act="open">查看原文</a>' +
          '<span class="divider"></span>' +
          '<button class="action-btn' + (fav ? " is-fav" : "") + '" type="button" data-act="fav">' +
            '<span class="fav-icon">' + (fav ? "★" : "☆") + "</span>" + (fav ? "已收藏" : "收藏") +
          "</button>" +
          '<button class="action-btn" type="button" data-act="toggle-read">' + (read ? "标为未读" : "标为已读") + "</button>" +
          '<span class="divider"></span>' +
          '<button class="action-btn" type="button" data-act="ai-classify">AI 分类</button>' +
          '<button class="action-btn" type="button" data-act="ai-summarize">AI 总结</button>' +
          '<span class="divider"></span>' +
          '<button class="action-btn" type="button" data-act="edit-category">修改分类</button>' +
          '<button class="action-btn" type="button" data-act="toggle-more">更多信息</button>' +
        "</div>" +
        '<div class="category-editor" data-editor ' + (editorOpen ? "" : "hidden") + ">" +
          '<span class="editor-label">人工分类</span>' +
          '<select data-category-select>' +
            '<option value="">清除人工分类</option>' + options +
          "</select>" +
          '<button class="btn btn-primary btn-sm" type="button" data-act="save-category">保存</button>' +
          '<button class="btn btn-text btn-sm" type="button" data-act="cancel-category">取消</button>' +
        "</div>" +
        '<div class="item-more" data-more ' + (moreOpen ? "" : "hidden") + ">" +
          '<span class="more-item">信息形态：<b>' + esc(item.primaryType) + "</b></span>" +
          '<span class="more-item">可信状态：<b>' + esc(item.verification) + "</b></span>" +
          '<span class="more-item">审核状态：<b>' + esc(item.review) + "</b></span>" +
          '<span class="more-item">分类方式：<b>' + esc(item.provider) + "</b></span>" +
          '<span class="more-item">来源类型：<b>' + esc(item.sourceKind) + "</b></span>" +
          '<span class="more-item">条目编号：<b>' + item.id + "</b></span>" +
        "</div>" +
      "</div>" +
    "</article>"
  );
}

/* ==========================================================================
   渲染：方案 B（紧凑行）
   ========================================================================== */
function renderRow(item) {
  var read = isRead(item);
  var fav = isFav(item);
  var expandOpen = state.rowExpand === item.id;

  var options = CATEGORIES.map(function (c) {
    var sel = c === categoryOf(item) ? " selected" : "";
    return '<option value="' + esc(c) + '"' + sel + ">" + esc(c) + "</option>";
  }).join("");

  return (
    '<div class="item-row' + (read ? "" : " is-unread") + '" data-id="' + item.id + '">' +
      '<div class="row-check"><input type="checkbox" data-select="' + item.id + '"' +
        (state.selected[item.id] ? " checked" : "") + ' aria-label="选择此条资讯"></div>' +
      '<div class="row-category">' + categoryChip(item) + "</div>" +
      '<div class="row-main">' +
        '<div class="row-title-line">' +
          (read ? "" : '<span class="unread-dot" title="未读"></span>') +
          '<span class="row-title"><a href="#" data-act="open">' + esc(item.title) + "</a></span>" +
        "</div>" +
        '<div class="row-summary">' + esc(item.summary) + "</div>" +
        '<div class="row-meta">' +
          '<span class="meta-category">' + esc(categoryOf(item)) + "</span>" +
          "<span>" + esc(item.source) + "</span>" +
          "<span>发布 " + esc(item.publishedAt) + "</span>" +
          "<span>发现 " + esc(item.discoveredAt) + "</span>" +
        "</div>" +
      "</div>" +
      '<div class="row-actions">' +
        '<button class="row-action' + (fav ? " is-fav" : "") + '" type="button" data-act="fav" title="' + (fav ? "取消收藏" : "收藏") + '" aria-label="收藏">' + (fav ? "★" : "☆") + "</button>" +
        '<button class="row-action' + (read ? " is-done" : "") + '" type="button" data-act="toggle-read" title="' + (read ? "标为未读" : "标为已读") + '" aria-label="已读状态">' + (read ? "✓" : "○") + "</button>" +
        '<button class="row-action" type="button" data-act="ai-classify" title="AI 分类"><span class="row-action-text">AI</span> 分类</button>' +
        '<button class="row-action" type="button" data-act="ai-summarize" title="AI 总结"><span class="row-action-text">AI</span> 总结</button>' +
        '<button class="row-action" type="button" data-act="toggle-row-more" title="更多" aria-label="更多操作">' + (expandOpen ? "▴" : "▾") + "</button>" +
      "</div>" +
      '<div class="row-expand" data-row-expand ' + (expandOpen ? "" : "hidden") + ">" +
        '<div class="expand-group">' +
          '<span class="editor-label">人工分类</span>' +
          '<select data-category-select><option value="">清除人工分类</option>' + options + "</select>" +
          '<button class="btn btn-primary btn-sm" type="button" data-act="save-category">保存</button>' +
          '<button class="btn btn-text btn-sm" type="button" data-act="cancel-category">取消</button>' +
        "</div>" +
        '<span class="more-item">信息形态：<b>' + esc(item.primaryType) + "</b></span>" +
        '<span class="more-item">可信状态：<b>' + esc(item.verification) + "</b></span>" +
        '<span class="more-item">审核状态：<b>' + esc(item.review) + "</b></span>" +
        '<span class="more-item">分类方式：<b>' + esc(item.provider) + "</b></span>" +
      "</div>" +
    "</div>"
  );
}

/* ---------- 整表渲染 ---------- */
function renderLists() {
  $("#list-a").innerHTML = ITEMS.map(renderCard).join("");
  $("#list-b").innerHTML = ITEMS.map(renderRow).join("");
  syncSelectionUI();
}

/* ==========================================================================
   选择与批量操作
   ========================================================================== */
function syncSelectionUI() {
  var ids = selectedIds();
  var count = ids.length;

  // 批量按钮启用/禁用
  $all("#batch-actions .btn").forEach(function (btn) {
    btn.disabled = count === 0;
  });

  // 已选数量
  var countEl = $("#selected-count");
  countEl.hidden = count === 0;
  countEl.textContent = "已选 " + count + " 条";

  // 全选框状态
  var all = $("#select-all");
  all.checked = count > 0 && count === ITEMS.length;
  all.indeterminate = count > 0 && count < ITEMS.length;

  // 两个列表中的复选框保持一致
  $all("[data-select]").forEach(function (box) {
    box.checked = !!state.selected[Number(box.getAttribute("data-select"))];
  });
}

function setAllSelected(on) {
  state.selected = {};
  if (on) {
    ITEMS.forEach(function (item) {
      state.selected[item.id] = true;
    });
  }
  syncSelectionUI();
}

/* ==========================================================================
   事件绑定
   ========================================================================== */
/* ==========================================================================
   全局页面切换（来源详情等子页面归入父级导航）
   ========================================================================== */
var NAV_PARENT = {
  "source-detail": "sources"
};

function showPage(page) {
  $all(".page").forEach(function (p) {
    p.hidden = p.id !== "page-" + page;
  });
  var navPage = NAV_PARENT[page] || page;
  $all(".main-nav a").forEach(function (a) {
    var active = a.getAttribute("data-page") === navPage;
    a.classList.toggle("is-active", active);
    if (active) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  });
  window.scrollTo({ top: 0 });
}

function bindNav() {
  $all("[data-page]").forEach(function (el) {
    el.addEventListener("click", function (e) {
      e.preventDefault();
      var page = el.getAttribute("data-page");
      if (page) showPage(page);
    });
  });
}

function bindFilters() {
  // 更多筛选展开/收起
  var btn = $("#btn-more-filters");
  var panel = $("#more-filters");
  btn.addEventListener("click", function () {
    var open = panel.hidden;
    panel.hidden = !open;
    btn.setAttribute("aria-expanded", String(open));
    btn.firstChild.textContent = open ? "收起筛选 " : "更多筛选 ";
  });

  // 应用筛选（演示）
  $("#filter-form").addEventListener("submit", function (e) {
    e.preventDefault();
    toast("原型演示：筛选条件已记录，接入后端后以 GET 参数提交到 /");
  });

  // 清除
  $("#btn-clear-filter").addEventListener("click", function () {
    $("#filter-form").reset();
    toast("已清除全部筛选条件");
  });
}

function bindToolbar() {
  // 列表样式切换
  $all(".view-switch button").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var view = btn.getAttribute("data-view");
      if (view === state.view) return;
      state.view = view;
      $all(".view-switch button").forEach(function (b) {
        b.classList.toggle("is-active", b === btn);
      });
      $("#list-a").hidden = view !== "a";
      $("#list-b").hidden = view !== "b";
    });
  });

  // 全选
  $("#select-all").addEventListener("change", function (e) {
    setAllSelected(e.target.checked);
  });

  // 批量操作
  $all("#batch-actions .btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var ids = selectedIds();
      if (ids.length === 0) return;
      var action = btn.getAttribute("data-batch");
      if (action === "read" || action === "unread") {
        ids.forEach(function (id) {
          state.readOverride[id] = action === "read";
        });
        renderLists();
        toast("已将 " + ids.length + " 条资讯标为" + (action === "read" ? "已读" : "未读"));
      } else if (action === "ai-classify") {
        toast("原型演示：将对 " + ids.length + " 条资讯执行 AI 分类（接入后端后 POST /items/batch-ai-classify）");
      } else if (action === "ai-summarize") {
        toast("原型演示：将对 " + ids.length + " 条资讯执行 AI 总结（接入后端后 POST /items/batch-ai-summarize）");
      }
    });
  });

  // 导出
  $all("[data-export]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var format = btn.getAttribute("data-export");
      toast("原型演示：导出当前筛选结果（共 " + TOTAL_COUNT + " 条）为 " + (format === "excel" ? "Excel" : "Word") + "，不生成真实文件");
    });
  });

  // 更新全部启用来源
  $("#btn-update-all").addEventListener("click", function () {
    var btn = this;
    btn.disabled = true;
    btn.textContent = "正在更新…";
    setTimeout(function () {
      btn.disabled = false;
      btn.textContent = "更新全部启用来源";
      toast("原型演示：更新任务已提交（接入后端后 POST /updates），不会真实抓取");
    }, 1200);
  });
}

/* ---------- 列表内部事件（事件委托，两个列表共用） ---------- */
function bindLists() {
  ["#list-a", "#list-b"].forEach(function (sel) {
    $(sel).addEventListener("click", function (e) {
      var host = e.target.closest("[data-id]");
      if (!host) return;
      var id = Number(host.getAttribute("data-id"));
      var item = getItem(id);
      var actEl = e.target.closest("[data-act]");
      if (!actEl) return;
      var act = actEl.getAttribute("data-act");

      switch (act) {
        case "open":
          e.preventDefault();
          state.readOverride[id] = true;
          renderLists();
          toast("原型演示：在新窗口打开原文并标为已读");
          break;

        case "fav":
          state.favOverride[id] = !isFav(item);
          renderLists();
          break;

        case "toggle-read":
          state.readOverride[id] = !isRead(item);
          renderLists();
          break;

        case "ai-classify":
          toast("原型演示：对「" + truncate(item.title, 18) + "」执行 AI 分类（接入后端后 POST /items/" + id + "/ai-classify）");
          break;

        case "ai-summarize":
          toast("原型演示：对「" + truncate(item.title, 18) + "」执行 AI 总结（接入后端后 POST /items/" + id + "/ai-summarize）");
          break;

        case "toggle-summary":
          state.expandedSummary[id] = !state.expandedSummary[id];
          renderLists();
          break;

        case "edit-category":
          state.openEditor = state.openEditor === id ? null : id;
          state.openMore = null;
          renderLists();
          break;

        case "toggle-more":
          state.openMore = state.openMore === id ? null : id;
          state.openEditor = null;
          renderLists();
          break;

        case "toggle-row-more":
          state.rowExpand = state.rowExpand === id ? null : id;
          renderLists();
          break;

        case "save-category": {
          var select = $("[data-category-select]", host);
          var value = select ? select.value : "";
          if (value) {
            state.categoryOverride[id] = value;
            toast("已将分类修改为「" + value + "」（原型演示）");
          } else {
            delete state.categoryOverride[id];
            toast("已清除人工分类（原型演示）");
          }
          state.openEditor = null;
          state.rowExpand = null;
          renderLists();
          break;
        }

        case "cancel-category":
          state.openEditor = null;
          state.rowExpand = null;
          renderLists();
          break;
      }
    });

    // 单条选择
    $(sel).addEventListener("change", function (e) {
      var box = e.target.closest("[data-select]");
      if (!box) return;
      var id = Number(box.getAttribute("data-select"));
      if (box.checked) state.selected[id] = true;
      else delete state.selected[id];
      syncSelectionUI();
    });
  });
}

function truncate(text, n) {
  return text.length > n ? text.slice(0, n) + "…" : text;
}

/* ==========================================================================
   AI 页面
   ========================================================================== */
var AI_JOBS = [
  {
    id: 47, type: "分类", trigger: "自动", status: "已完成", statusKind: "ok",
    total: 12, success: 12, failure: 0, skipped: 0, fallback: 0,
    model: "deepseek-chat", started: "2026-07-22 08:33", duration: "41 秒", error: null
  },
  {
    id: 46, type: "总结", trigger: "手动", status: "部分失败", statusKind: "warn",
    total: 20, success: 17, failure: 2, skipped: 1, fallback: 0,
    model: "deepseek-chat", started: "2026-07-21 16:20", duration: "3 分 05 秒",
    error: "2 条响应超时（超过 30 秒），1 条正文为空已跳过。失败条目可在「AI 总结」区使用「仅重试失败项」重新处理。"
  },
  {
    id: 45, type: "分类", trigger: "手动", status: "已完成", statusKind: "ok",
    total: 8, success: 8, failure: 0, skipped: 0, fallback: 0,
    model: "deepseek-chat", started: "2026-07-21 11:05", duration: "28 秒", error: null
  },
  {
    id: 44, type: "总结", trigger: "自动", status: "已完成", statusKind: "ok",
    total: 9, success: 9, failure: 0, skipped: 0, fallback: 0,
    model: "deepseek-chat", started: "2026-07-21 08:34", duration: "1 分 12 秒", error: null
  },
  {
    id: 43, type: "分类", trigger: "手动", status: "失败", statusKind: "error",
    total: 15, success: 0, failure: 15, skipped: 0, fallback: 15,
    model: "deepseek-chat", started: "2026-07-20 09:12", duration: "52 秒",
    error: "API Key 无效或账户余额不足（HTTP 401）。本次 15 条已全部回退为规则分类，资讯不受影响；更新 Key 后可重新执行 AI 分类。"
  }
];

var aiJobOpen = null;

function statusBadge(text, kind) {
  return '<span class="status status-' + kind + '">' + esc(text) + "</span>";
}

function renderAiJobs() {
  var rows = AI_JOBS.map(function (job) {
    var open = aiJobOpen === job.id;
    var main =
      '<tr class="tr-expandable' + (open ? " is-open" : "") + '" data-job="' + job.id + '">' +
        '<td data-label="类型"><span class="expand-caret"></span>' + esc(job.type) + "</td>" +
        '<td data-label="触发方式">' + esc(job.trigger) + "</td>" +
        '<td data-label="状态">' + statusBadge(job.status, job.statusKind) + "</td>" +
        '<td data-label="处理总数" class="num">' + job.total + "</td>" +
        '<td data-label="成功" class="num">' + job.success + "</td>" +
        '<td data-label="失败" class="num">' + (job.failure || "0") + "</td>" +
        '<td data-label="跳过" class="num col-optional">' + job.skipped + "</td>" +
        '<td data-label="回退" class="num col-optional">' + job.fallback + "</td>" +
        '<td data-label="模型" class="col-optional">' + esc(job.model) + "</td>" +
        '<td data-label="开始时间" class="cell-time">' + esc(job.started) + "</td>" +
        '<td data-label="耗时" class="cell-time">' + esc(job.duration) + "</td>" +
      "</tr>";
    if (!job.error) return main;
    return main +
      '<tr class="tr-expand' + (open ? " is-open" : "") + '">' +
        '<td colspan="11">' +
          '<div class="expand-block">' +
            "<h3>错误详情</h3>" +
            '<div class="error-box">' + esc(job.error) + "</div>" +
          "</div>" +
        "</td>" +
      "</tr>";
  }).join("");

  $("#ai-jobs-table").innerHTML =
    '<div class="table-wrap"><table class="data-table table-cards">' +
      "<thead><tr>" +
        "<th>类型</th><th>触发方式</th><th>状态</th><th>处理总数</th><th>成功</th><th>失败</th>" +
        '<th class="col-optional">跳过</th><th class="col-optional">回退</th>' +
        '<th class="col-optional">模型</th><th>开始时间</th><th>耗时</th>' +
      "</tr></thead><tbody>" + rows + "</tbody></table></div>";
}

function bindAiPage() {
  renderAiJobs();

  // 任务行展开
  $("#ai-jobs-table").addEventListener("click", function (e) {
    var tr = e.target.closest("[data-job]");
    if (!tr) return;
    var id = Number(tr.getAttribute("data-job"));
    aiJobOpen = aiJobOpen === id ? null : id;
    renderAiJobs();
  });

  // 模式选择（单选行）
  function bindMode(listId, extraId) {
    $("#" + listId).addEventListener("change", function (e) {
      var radio = e.target.closest('input[type="radio"]');
      if (!radio) return;
      $all(".option-row", $("#" + listId)).forEach(function (row) {
        row.classList.toggle("is-selected", $("input", row).checked);
      });
      if (extraId) {
        $("#" + extraId).hidden = radio.value !== "auto";
      }
    });
  }
  bindMode("classifier-mode", "classifier-strategy");
  bindMode("summarizer-mode", null);

  // 保存
  $("#ai-save").addEventListener("click", function () {
    $("#ai-current-model").textContent = $("#ai-model").value || "未设置";
    toast("原型演示：AI 设置已保存（接入后端后 POST /ai/save）");
  });

  // 测试连接
  $("#ai-test").addEventListener("click", function () {
    var btn = this;
    var result = $("#ai-test-result");
    btn.disabled = true;
    btn.textContent = "正在测试…";
    result.hidden = true;
    setTimeout(function () {
      btn.disabled = false;
      btn.textContent = "测试连接";
      result.className = "notice is-success";
      result.textContent = "连接成功：模型 " + ($("#ai-model").value || "deepseek-chat") + " 响应正常（耗时 0.8 秒）。（原型演示，未发起真实请求）";
      result.hidden = false;
    }, 1000);
  });

  // 清除 Key（低频危险操作，二次确认）
  $("#ai-clear-key").addEventListener("click", function () {
    if (!window.confirm("确认清除已保存的 API Key？清除后 AI 分类与总结将不可用。")) return;
    var badge = $("#ai-key-status");
    badge.textContent = "Key 未配置";
    badge.className = "status status-muted";
    $("#ai-key").placeholder = "未配置 Key";
    $("#ai-run-classify").disabled = true;
    $("#ai-run-summarize").disabled = true;
    toast("原型演示：Key 已清除（接入后端后 POST /ai/clear-key）");
  });

  // 执行任务
  $("#ai-run-classify").addEventListener("click", function () {
    toast("原型演示：已提交 23 条待分类资讯（接入后端后 POST /ai/classify）");
  });
  $("#ai-run-summarize").addEventListener("click", function () {
    toast("原型演示：已提交 41 条未总结资讯（接入后端后 POST /ai/summarize）");
  });
  $("#ai-retry-summarize").addEventListener("click", function () {
    toast("原型演示：仅重试 2 条失败项（接入后端后 POST /ai/summarize，retry=1）");
  });
}

/* ==========================================================================
   来源页面 + 来源详情
   ========================================================================== */
var SOURCES = [
  {
    id: 1, name: "国家数据局", domain: "www.nda.gov.cn", url: "https://www.nda.gov.cn/xwzx/gzdt.htm",
    type: "官方机构", kindLabel: "RSS 订阅", status: "正常", statusKind: "ok", enabled: true,
    lastChecked: "2026-07-22 08:30", lastResult: "成功", lastResultKind: "ok", lastCount: 6, lastError: null,
    roleLabel: "官方政策发布", reviewLabel: "自动发布", slug: "nda-gov-cn",
    stats: { fetched: 128, accepted: 96, rejected: 32, inserted: 41, updated: 55, failed: 0 },
    recentRuns: [
      { time: "2026-07-22 08:30", trigger: "定时", result: "成功", resultKind: "ok", fetched: 6, inserted: 2 },
      { time: "2026-07-21 08:30", trigger: "定时", result: "成功", resultKind: "ok", fetched: 4, inserted: 1 },
      { time: "2026-07-20 08:30", trigger: "定时", result: "成功", resultKind: "ok", fetched: 5, inserted: 2 }
    ],
    recentItems: [
      { title: "关于组织开展 2026 年数据要素×大赛的通知", time: "2026-07-21 16:02" },
      { title: "《全国数据资源调查报告（2025 年）》正式发布", time: "2026-07-20 10:24" },
      { title: "国家数据局部署 2026 年下半年数据基础设施建设重点工作", time: "2026-07-19 09:15" }
    ]
  },
  {
    id: 2, name: "国家互联网信息办公室（网信办）", domain: "www.cac.gov.cn", url: "https://www.cac.gov.cn/xxfb.htm",
    type: "官方机构", kindLabel: "网页列表", status: "正常", statusKind: "ok", enabled: true,
    lastChecked: "2026-07-22 08:30", lastResult: "成功", lastResultKind: "ok", lastCount: 4, lastError: null,
    roleLabel: "官方政策发布", reviewLabel: "自动发布", slug: "cac-gov-cn",
    stats: { fetched: 96, accepted: 74, rejected: 22, inserted: 33, updated: 41, failed: 0 },
    recentRuns: [
      { time: "2026-07-22 08:30", trigger: "定时", result: "成功", resultKind: "ok", fetched: 4, inserted: 1 },
      { time: "2026-07-21 08:30", trigger: "定时", result: "成功", resultKind: "ok", fetched: 3, inserted: 1 },
      { time: "2026-07-20 08:30", trigger: "定时", result: "成功", resultKind: "ok", fetched: 6, inserted: 2 }
    ],
    recentItems: [
      { title: "关于《人工智能生成合成内容标识办法》配套国家标准的公告", time: "2026-07-21 14:40" },
      { title: "2026 年“清朗”系列专项行动新闻发布会实录", time: "2026-07-19 11:00" }
    ]
  },
  {
    id: 3, name: "中国互联网协会", domain: "www.isc.org.cn", url: "https://www.isc.org.cn/xhdt/",
    type: "官方机构", kindLabel: "RSS 订阅", status: "部分可用", statusKind: "warn", enabled: true,
    lastChecked: "2026-07-22 08:30", lastResult: "部分成功", lastResultKind: "warn", lastCount: 3,
    lastError: "2 个栏目页面结构发生变化，本次已自动跳过；主栏目抓取正常。",
    roleLabel: "行业协会动态", reviewLabel: "自动发布", slug: "isc-org-cn",
    stats: { fetched: 84, accepted: 61, rejected: 23, inserted: 26, updated: 35, failed: 2 },
    recentRuns: [
      { time: "2026-07-22 08:30", trigger: "定时", result: "部分成功", resultKind: "warn", fetched: 3, inserted: 1 },
      { time: "2026-07-21 08:30", trigger: "定时", result: "成功", resultKind: "ok", fetched: 5, inserted: 2 },
      { time: "2026-07-20 08:30", trigger: "定时", result: "成功", resultKind: "ok", fetched: 4, inserted: 1 }
    ],
    recentItems: [
      { title: "关于举办 2026 中国互联网大会的通知", time: "2026-07-21 09:30" },
      { title: "《中国互联网发展报告（2026）》启动编写", time: "2026-07-18 15:20" }
    ]
  },
  {
    id: 4, name: "DeepSeek 官方更新", domain: "github.com/deepseek-ai", url: "https://github.com/deepseek-ai/DeepSeek-V3/releases",
    type: "企业官方", kindLabel: "GitHub Releases", status: "正常", statusKind: "ok", enabled: true,
    lastChecked: "2026-07-22 08:30", lastResult: "成功", lastResultKind: "ok", lastCount: 2, lastError: null,
    roleLabel: "官方产品动态", reviewLabel: "自动发布", slug: "deepseek-releases",
    stats: { fetched: 42, accepted: 40, rejected: 2, inserted: 21, updated: 19, failed: 0 },
    recentRuns: [
      { time: "2026-07-22 08:30", trigger: "定时", result: "成功", resultKind: "ok", fetched: 2, inserted: 1 },
      { time: "2026-07-21 08:30", trigger: "定时", result: "成功", resultKind: "ok", fetched: 1, inserted: 0 },
      { time: "2026-07-20 08:30", trigger: "定时", result: "成功", resultKind: "ok", fetched: 1, inserted: 1 }
    ],
    recentItems: [
      { title: "DeepSeek-V3.2 发布：长上下文与工具调用能力更新", time: "2026-07-21 20:02" },
      { title: "DeepSeek-R2 推理模型技术报告", time: "2026-07-15 18:44" }
    ]
  },
  {
    id: 5, name: "智谱 AI 开放平台更新日志", domain: "docs.bigmodel.cn", url: "https://docs.bigmodel.cn/cn/guide/start/introduction",
    type: "企业官方", kindLabel: "单页更新日志", status: "最近失败", statusKind: "error", enabled: true,
    lastChecked: "2026-07-22 08:30", lastResult: "失败", lastResultKind: "error", lastCount: 0,
    lastError: "连接超时（10 秒），已连续 2 次失败；将按重试策略在下一次更新时再次尝试，历史资讯不受影响。",
    roleLabel: "官方产品动态", reviewLabel: "自动发布", slug: "bigmodel-changelog",
    stats: { fetched: 58, accepted: 51, rejected: 7, inserted: 24, updated: 27, failed: 3 },
    recentRuns: [
      { time: "2026-07-22 08:30", trigger: "定时", result: "失败", resultKind: "error", fetched: 0, inserted: 0 },
      { time: "2026-07-21 08:30", trigger: "定时", result: "失败", resultKind: "error", fetched: 0, inserted: 0 },
      { time: "2026-07-20 08:30", trigger: "定时", result: "成功", resultKind: "ok", fetched: 3, inserted: 1 }
    ],
    recentItems: [
      { title: "GLM-4.6 发布：代码与智能体能力升级", time: "2026-07-17 10:00" },
      { title: "智谱开放平台新增批量推理接口", time: "2026-07-12 16:30" }
    ]
  },
  {
    id: 6, name: "百度千帆大模型平台动态", domain: "qianfan.cloud.baidu.com", url: "https://qianfan.cloud.baidu.com/updates",
    type: "企业官方", kindLabel: "JSON 接口", status: "正常", statusKind: "ok", enabled: true,
    lastChecked: "2026-07-22 08:30", lastResult: "成功", lastResultKind: "ok", lastCount: 5, lastError: null,
    roleLabel: "官方产品动态", reviewLabel: "自动发布", slug: "qianfan-updates",
    stats: { fetched: 73, accepted: 66, rejected: 7, inserted: 30, updated: 36, failed: 0 },
    recentRuns: [
      { time: "2026-07-22 08:30", trigger: "定时", result: "成功", resultKind: "ok", fetched: 5, inserted: 2 },
      { time: "2026-07-21 08:30", trigger: "定时", result: "成功", resultKind: "ok", fetched: 3, inserted: 1 },
      { time: "2026-07-20 08:30", trigger: "定时", result: "成功", resultKind: "ok", fetched: 4, inserted: 2 }
    ],
    recentItems: [
      { title: "千帆平台上线 ERNIE-5.0 系列模型", time: "2026-07-21 12:10" },
      { title: "千帆 AppBuilder 新增企业级知识库组件", time: "2026-07-18 09:45" }
    ]
  },
  {
    id: 7, name: "Kimi 开放平台更新日志", domain: "platform.moonshot.cn", url: "https://platform.moonshot.cn/docs/changelog",
    type: "企业官方", kindLabel: "RSS 订阅", status: "已停用", statusKind: "muted", enabled: false,
    lastChecked: "2026-07-15 09:02", lastResult: "—", lastResultKind: "muted", lastCount: null, lastError: null,
    roleLabel: "官方产品动态", reviewLabel: "自动发布", slug: "kimi-changelog",
    stats: { fetched: 36, accepted: 33, rejected: 3, inserted: 15, updated: 18, failed: 0 },
    recentRuns: [
      { time: "2026-07-15 09:02", trigger: "网页手动", result: "成功", resultKind: "ok", fetched: 2, inserted: 1 },
      { time: "2026-07-14 08:30", trigger: "定时", result: "成功", resultKind: "ok", fetched: 1, inserted: 0 },
      { time: "2026-07-13 08:30", trigger: "定时", result: "成功", resultKind: "ok", fetched: 2, inserted: 1 }
    ],
    recentItems: [
      { title: "Kimi K3 模型上线：Agent 编码能力增强", time: "2026-07-14 19:22" },
      { title: "开放平台上下文缓存价格下调 50%", time: "2026-07-10 11:00" }
    ]
  },
  {
    id: 8, name: "量子位", domain: "www.qbitai.com", url: "https://www.qbitai.com/category/ai",
    type: "媒体", kindLabel: "网页列表", status: "正常", statusKind: "ok", enabled: true,
    lastChecked: "2026-07-22 08:30", lastResult: "成功", lastResultKind: "ok", lastCount: 11, lastError: null,
    roleLabel: "媒体线索（默认待审核）", reviewLabel: "低置信度时审核", slug: "qbitai",
    stats: { fetched: 210, accepted: 96, rejected: 114, inserted: 40, updated: 56, failed: 1 },
    recentRuns: [
      { time: "2026-07-22 08:30", trigger: "定时", result: "成功", resultKind: "ok", fetched: 11, inserted: 3 },
      { time: "2026-07-21 08:30", trigger: "定时", result: "成功", resultKind: "ok", fetched: 9, inserted: 2 },
      { time: "2026-07-20 08:30", trigger: "定时", result: "成功", resultKind: "ok", fetched: 13, inserted: 4 }
    ],
    recentItems: [
      { title: "国产大模型半年盘点：价格战之后拼什么", time: "2026-07-21 22:15" },
      { title: "具身智能融资持续升温，7 月已披露 12 起", time: "2026-07-20 17:40" }
    ]
  },
  {
    id: 9, name: "36氪 AI 频道", domain: "36kr.com", url: "https://36kr.com/information/AI",
    type: "媒体", kindLabel: "网页列表", status: "部分可用", statusKind: "warn", enabled: true,
    lastChecked: "2026-07-22 08:30", lastResult: "部分成功", lastResultKind: "warn", lastCount: 7,
    lastError: "列表页偶发验证码拦截，已自动降低抓取频率并跳过重试。",
    roleLabel: "媒体线索（默认待审核）", reviewLabel: "低置信度时审核", slug: "36kr-ai",
    stats: { fetched: 180, accepted: 72, rejected: 108, inserted: 28, updated: 44, failed: 2 },
    recentRuns: [
      { time: "2026-07-22 08:30", trigger: "定时", result: "部分成功", resultKind: "warn", fetched: 7, inserted: 2 },
      { time: "2026-07-21 08:30", trigger: "定时", result: "成功", resultKind: "ok", fetched: 10, inserted: 3 },
      { time: "2026-07-20 08:30", trigger: "定时", result: "成功", resultKind: "ok", fetched: 8, inserted: 2 }
    ],
    recentItems: [
      { title: "AI 编程工具进入企业采购清单", time: "2026-07-21 18:05" },
      { title: "大模型厂商加速布局政务市场", time: "2026-07-20 13:26" }
    ]
  }
];

var CANDIDATES = [
  {
    id: 110, name: "机器之心", domain: "www.jiqizhixin.com", type: "媒体", kindLabel: "网页列表",
    discovery: "可以使用", discoveryKind: "ok", lastPreview: "2026-07-21 14:20", previewCount: 12,
    note: "检测到稳定的文章列表结构，预览抓取 12 条。"
  }
];

var sourceErrOpen = null;
var detailSourceId = 1;
var sourceFilters = { keyword: "", type: "", status: "", result: "" };

function sourceVisible(s) {
  if (sourceFilters.keyword) {
    var kw = sourceFilters.keyword.toLowerCase();
    if ((s.name + s.domain).toLowerCase().indexOf(kw) === -1) return false;
  }
  if (sourceFilters.type && s.type !== sourceFilters.type) return false;
  if (sourceFilters.status && s.status !== sourceFilters.status) return false;
  if (sourceFilters.result && s.lastResult !== sourceFilters.result) return false;
  return true;
}

function renderSources() {
  var list = SOURCES.filter(sourceVisible);
  if (list.length === 0) {
    $("#sources-table-wrap").innerHTML =
      '<div class="empty-state"><h2>没有符合条件的来源</h2><p>请调整筛选条件后重试。</p></div>';
    return;
  }
  var rows = list.map(function (s) {
    var errOpen = sourceErrOpen === s.id;
    var main =
      '<tr data-source="' + s.id + '">' +
        '<td data-label="来源" class="cell-block"><div class="cell-main">' + esc(s.name) + '</div><div class="cell-sub">' + esc(s.domain) + "</div></td>" +
        '<td data-label="类型" class="cell-block"><div>' + esc(s.type) + '</div><div class="cell-sub">' + esc(s.kindLabel) + "</div></td>" +
        '<td data-label="运行状态">' + statusBadge(s.status, s.statusKind) +
          (s.lastError
            ? '<br><button class="err-toggle" type="button" data-act="toggle-source-err">' + (errOpen ? "收起错误" : "查看错误") + "</button>"
            : "") +
        "</td>" +
        '<td data-label="启用">' +
          '<span class="switch"><input type="checkbox" data-act="toggle-enabled" ' + (s.enabled ? "checked" : "") + ' aria-label="启用或停用"><span class="switch-track"></span></span>' +
        "</td>" +
        '<td data-label="最近更新" class="cell-time">' + esc(s.lastChecked) + "</td>" +
        '<td data-label="最近结果">' + statusBadge(s.lastResult, s.lastResultKind) + "</td>" +
        '<td data-label="本次获取" class="num">' + (s.lastCount === null ? "—" : s.lastCount) + "</td>" +
        '<td data-label="操作"><div class="row-ops">' +
          '<button class="op" type="button" data-act="open-detail">详情</button>' +
          '<button class="op" type="button" data-act="update-one" ' + (s.enabled ? "" : "disabled") + ">更新</button>" +
        "</div></td>" +
      "</tr>";
    if (!s.lastError) return main;
    return main +
      '<tr class="tr-expand' + (errOpen ? " is-open" : "") + '">' +
        '<td colspan="8"><div class="error-box">最近错误：' + esc(s.lastError) + "</div></td>" +
      "</tr>";
  }).join("");

  $("#sources-table-wrap").innerHTML =
    '<div class="table-wrap"><table class="data-table table-cards">' +
      "<thead><tr>" +
        "<th>来源</th><th>类型</th><th>运行状态</th><th>启用</th><th>最近更新</th><th>最近结果</th><th>本次获取</th><th>操作</th>" +
      "</tr></thead><tbody>" + rows + "</tbody></table></div>";
}

function renderCandidates() {
  var rows = CANDIDATES.map(function (c) {
    return (
      '<tr data-candidate="' + c.id + '">' +
        '<td data-label="来源" class="cell-block"><div class="cell-main">' + esc(c.name) + '</div><div class="cell-sub">' + esc(c.domain) + "</div></td>" +
        '<td data-label="类型" class="cell-block"><div>' + esc(c.type) + '</div><div class="cell-sub">' + esc(c.kindLabel) + "</div></td>" +
        '<td data-label="检测结果">' + statusBadge(c.discovery, c.discoveryKind) + '</td>' +
        '<td data-label="最近预览" class="cell-time">' + esc(c.lastPreview) + "</td>" +
        '<td data-label="预览数量" class="num">' + c.previewCount + "</td>" +
        '<td data-label="操作"><div class="row-ops">' +
          '<button class="op" type="button" data-act="preview-candidate">预览</button>' +
          '<button class="op" type="button" data-act="activate-candidate">启用并加入监控</button>' +
        "</div></td>" +
      "</tr>"
    );
  }).join("");

  $("#candidates-table-wrap").innerHTML =
    '<div class="table-wrap"><table class="data-table table-cards">' +
      "<thead><tr>" +
        "<th>来源</th><th>类型</th><th>检测结果</th><th>最近预览</th><th>预览数量</th><th>操作</th>" +
      "</tr></thead><tbody>" + rows + "</tbody></table></div>";
}

/* ---------- 来源详情 ---------- */
function categoryOptions(selected) {
  return CATEGORIES.map(function (c) {
    return '<option' + (c === selected ? " selected" : "") + ">" + esc(c) + "</option>";
  }).join("");
}

function renderSourceDetail() {
  var s = null;
  for (var i = 0; i < SOURCES.length; i++) {
    if (SOURCES[i].id === detailSourceId) s = SOURCES[i];
  }
  if (!s) {
    $("#source-detail-wrap").innerHTML =
      '<div class="empty-state"><h2>未找到来源</h2><p>该来源可能已被移除。</p>' +
      '<button class="btn btn-secondary" type="button" data-page="sources">返回来源列表</button></div>';
    return;
  }

  var runsRows = s.recentRuns.map(function (r) {
    return (
      "<tr><td>" + esc(r.time) + "</td><td>" + esc(r.trigger) + "</td><td>" +
      statusBadge(r.result, r.resultKind) + '</td><td class="num">' + r.fetched +
      '</td><td class="num">' + r.inserted + "</td></tr>"
    );
  }).join("");

  var itemsHtml = s.recentItems.map(function (it) {
    return (
      '<div class="recent-item"><span class="recent-title">' + esc(it.title) +
      '</span><span class="recent-time">' + esc(it.time) + "</span></div>"
    );
  }).join("");

  $("#source-detail-wrap").innerHTML =
    '<button class="back-link" type="button" data-page="sources">‹ 返回来源列表</button>' +
    '<div class="page-head">' +
      '<div class="page-head-text">' +
        '<div class="detail-title-row"><h1>' + esc(s.name) + "</h1>" +
          statusBadge(s.status, s.statusKind) +
          (s.enabled
            ? '<span class="status status-info">已启用</span>'
            : '<span class="status status-muted">已停用</span>') +
        "</div>" +
        '<p><a class="text-link" href="' + esc(s.url) + '" target="_blank" rel="noopener noreferrer">' + esc(s.url) + "</a></p>" +
      "</div>" +
      '<div class="page-head-side page-head-actions">' +
        '<button class="btn btn-secondary" type="button" data-act="detail-toggle-enabled">' + (s.enabled ? "停用来源" : "启用来源") + "</button>" +
        '<button class="btn btn-primary" type="button" data-act="detail-update" ' + (s.enabled ? "" : "disabled") + ">更新此来源</button>" +
      "</div>" +
    "</div>" +

    '<section class="section-card">' +
      '<div class="facts-grid">' +
        '<div class="fact"><div class="fact-label">来源类型</div><div class="fact-value">' + esc(s.type) + "</div></div>" +
        '<div class="fact"><div class="fact-label">采集方式</div><div class="fact-value">' + esc(s.kindLabel) + "</div></div>" +
        '<div class="fact"><div class="fact-label">来源角色</div><div class="fact-value">' + esc(s.roleLabel) + "</div></div>" +
        '<div class="fact"><div class="fact-label">审核策略</div><div class="fact-value">' + esc(s.reviewLabel) + "</div></div>" +
        '<div class="fact"><div class="fact-label">最近检查</div><div class="fact-value">' + esc(s.lastChecked) + "</div></div>" +
        '<div class="fact"><div class="fact-label">最近结果</div><div class="fact-value">' + statusBadge(s.lastResult, s.lastResultKind) + "</div></div>" +
      "</div>" +
    "</section>" +

    '<div class="stats-strip" aria-label="近 30 天处理统计">' +
      '<div class="stat"><span class="stat-num">' + s.stats.fetched + '</span><span class="stat-label">近 30 天抓取</span></div>' +
      '<div class="stat"><span class="stat-num">' + s.stats.accepted + '</span><span class="stat-label">通过准入</span></div>' +
      '<div class="stat"><span class="stat-num">' + s.stats.rejected + '</span><span class="stat-label">未通过准入</span></div>' +
      '<div class="stat"><span class="stat-num">' + s.stats.inserted + '</span><span class="stat-label">新增资讯</span></div>' +
      '<div class="stat"><span class="stat-num">' + s.stats.updated + '</span><span class="stat-label">更新资讯</span></div>' +
      '<div class="stat"><span class="stat-num' + (s.stats.failed > 0 ? " stat-danger" : "") + '">' + s.stats.failed + '</span><span class="stat-label">处理失败</span></div>' +
    "</div>" +

    (s.lastError
      ? '<div class="notice is-error">最近错误：' + esc(s.lastError) + "</div>"
      : "") +

    '<div class="settings-layout">' +
      '<section class="section-card">' +
        '<div class="section-head"><h2>基本信息</h2><p>名称、默认分类与说明可编辑；入口网址与采集配置不可在线修改。</p></div>' +
        '<div class="form-stack">' +
          '<div class="field"><label>来源名称</label><input id="detail-name" value="' + esc(s.name) + '" maxlength="255"></div>' +
          '<div class="field"><label>默认分类</label><select id="detail-category"><option value="">自动判断</option>' + categoryOptions(s.defaultCategory) + "</select></div>" +
          '<div class="field"><label>来源说明</label><textarea id="detail-desc" rows="3" maxlength="2000">' + esc(s.description || "") + "</textarea></div>" +
          '<label class="switch-row"><span class="switch"><input type="checkbox" id="detail-enabled" ' + (s.enabled ? "checked" : "") + '><span class="switch-track"></span></span>' +
            '<span class="switch-text"><b>参与批量更新</b><small>停用后不再自动抓取，历史资讯保留</small></span></label>' +
          '<div class="form-actions"><button class="btn btn-primary" type="button" data-act="detail-save">保存修改</button></div>' +
        "</div>" +
      "</section>" +
      '<section class="section-card">' +
        '<div class="section-head"><h2>最近运行</h2><p>该来源最近 3 次更新结果。</p></div>' +
        '<div class="table-wrap"><table class="mini-table">' +
          "<thead><tr><th>时间</th><th>触发</th><th>结果</th><th>抓取</th><th>新增</th></tr></thead>" +
          "<tbody>" + runsRows + "</tbody></table></div>" +
        '<div class="form-actions"><button class="btn btn-secondary btn-sm" type="button" data-act="detail-redetect">重新检测来源</button></div>' +
      "</section>" +
    "</div>" +

    '<section class="section-card">' +
      '<div class="section-head"><h2>最近抓取的资讯</h2><p>该来源最近入库的资讯。</p></div>' +
      '<div class="recent-items">' + itemsHtml + "</div>" +
      '<div class="form-actions"><button class="btn btn-text" type="button" data-act="detail-view-items">查看该来源全部资讯 →</button></div>' +
    "</section>";
}

function bindSourcesPage() {
  renderSources();
  renderCandidates();

  // 页签
  $all("[data-source-tab]").forEach(function (tab) {
    tab.addEventListener("click", function () {
      var which = tab.getAttribute("data-source-tab");
      $all("[data-source-tab]").forEach(function (t) {
        var active = t === tab;
        t.classList.toggle("is-active", active);
        t.setAttribute("aria-selected", String(active));
      });
      $("#sources-main-pane").hidden = which !== "main";
      $("#sources-candidate-pane").hidden = which !== "candidate";
    });
  });

  // 筛选
  $("#sources-filter-form").addEventListener("submit", function (e) {
    e.preventDefault();
    sourceFilters = {
      keyword: $("#sf-keyword").value.trim(),
      type: $("#sf-type").value,
      status: $("#sf-status").value,
      result: $("#sf-result").value
    };
    renderSources();
  });
  $("#sf-clear").addEventListener("click", function () {
    $("#sources-filter-form").reset();
    sourceFilters = { keyword: "", type: "", status: "", result: "" };
    renderSources();
  });

  // 页头操作
  $("#btn-seed-sources").addEventListener("click", function () {
    toast("原型演示：同步完整来源目录（接入后端后 POST /sources/seed-formal）");
  });
  $("#btn-add-source").addEventListener("click", function () {
    toast("原型演示：添加来源页面未包含在本轮原型中（生产中 GET /sources/new）");
  });

  // 监控中表格操作
  $("#sources-table-wrap").addEventListener("click", function (e) {
    var actEl = e.target.closest("[data-act]");
    if (!actEl) return;
    var tr = e.target.closest("[data-source]");
    if (!tr) return;
    var id = Number(tr.getAttribute("data-source"));
    var s = SOURCES.filter(function (x) { return x.id === id; })[0];
    var act = actEl.getAttribute("data-act");

    if (act === "open-detail") {
      detailSourceId = id;
      renderSourceDetail();
      showPage("source-detail");
    } else if (act === "toggle-source-err") {
      sourceErrOpen = sourceErrOpen === id ? null : id;
      renderSources();
    } else if (act === "update-one") {
      actEl.disabled = true;
      actEl.textContent = "更新中…";
      setTimeout(function () {
        actEl.disabled = false;
        actEl.textContent = "更新";
        toast("原型演示：已提交「" + truncate(s.name, 12) + "」更新（接入后端后 POST /sources/" + id + "/updates）");
      }, 900);
    }
  });

  // 启用开关（change 事件）
  $("#sources-table-wrap").addEventListener("change", function (e) {
    var box = e.target.closest('[data-act="toggle-enabled"]');
    if (!box) return;
    var tr = e.target.closest("[data-source]");
    var id = Number(tr.getAttribute("data-source"));
    var s = SOURCES.filter(function (x) { return x.id === id; })[0];
    s.enabled = box.checked;
    if (s.enabled) {
      s.status = s.prevStatus || "正常";
      s.statusKind = s.status === "正常" ? "ok" : s.status === "部分可用" ? "warn" : s.statusKind;
      s.lastResult = s.lastResult === "—" ? "—" : s.lastResult;
      toast("已启用「" + truncate(s.name, 12) + "」，将参与每次批量更新");
    } else {
      s.prevStatus = s.status === "已停用" ? "正常" : s.status;
      s.status = "已停用";
      s.statusKind = "muted";
      toast("已停用「" + truncate(s.name, 12) + "」，历史资讯保留");
    }
    renderSources();
  });

  // 候选操作
  $("#candidates-table-wrap").addEventListener("click", function (e) {
    var actEl = e.target.closest("[data-act]");
    if (!actEl) return;
    var act = actEl.getAttribute("data-act");
    if (act === "preview-candidate") {
      toast("原型演示：运行时预览候选来源（接入后端后 POST /sources/110/preview，不写入资讯）");
    } else if (act === "activate-candidate") {
      var c = CANDIDATES[0];
      if (!c) return;
      if (!window.confirm("启用「" + c.name + "」并加入监控？启用后将参与每次批量更新，抓取资讯进入首页与导出。")) return;
      CANDIDATES.shift();
      SOURCES.push({
        id: c.id, name: c.name, domain: c.domain, url: "https://" + c.domain + "/",
        type: c.type, kindLabel: c.kindLabel, status: "正常", statusKind: "ok", enabled: true,
        lastChecked: "尚未更新", lastResult: "—", lastResultKind: "muted", lastCount: null, lastError: null,
        roleLabel: "媒体线索（默认待审核）", reviewLabel: "低置信度时审核", slug: "jiqizhixin",
        stats: { fetched: 0, accepted: 0, rejected: 0, inserted: 0, updated: 0, failed: 0 },
        recentRuns: [], recentItems: []
      });
      renderCandidates();
      renderSources();
      $all(".tab-count")[0].textContent = String(SOURCES.length);
      $all(".tab-count")[1].textContent = String(CANDIDATES.length);
      toast("已启用「" + c.name + "」并加入监控");
    }
  });
}

function bindSourceDetail() {
  $("#source-detail-wrap").addEventListener("click", function (e) {
    var actEl = e.target.closest("[data-act]");
    if (!actEl) return;
    var s = SOURCES.filter(function (x) { return x.id === detailSourceId; })[0];
    var act = actEl.getAttribute("data-act");

    if (act === "detail-toggle-enabled") {
      s.enabled = !s.enabled;
      if (s.enabled) {
        s.status = s.prevStatus || "正常";
        s.statusKind = s.status === "正常" ? "ok" : "warn";
        toast("已启用「" + truncate(s.name, 12) + "」");
      } else {
        s.prevStatus = s.status === "已停用" ? "正常" : s.status;
        s.status = "已停用";
        s.statusKind = "muted";
        toast("已停用「" + truncate(s.name, 12) + "」");
      }
      renderSourceDetail();
      renderSources();
    } else if (act === "detail-update") {
      actEl.disabled = true;
      actEl.textContent = "正在更新…";
      setTimeout(function () {
        actEl.disabled = false;
        actEl.textContent = "更新此来源";
        toast("原型演示：更新完成将刷新统计（接入后端后 POST /sources/" + s.id + "/updates）");
      }, 1000);
    } else if (act === "detail-save") {
      s.name = $("#detail-name").value.trim() || s.name;
      s.enabled = $("#detail-enabled").checked;
      toast("原型演示：来源已保存（接入后端后 POST /sources/" + s.id + "/edit）");
      renderSourceDetail();
      renderSources();
    } else if (act === "detail-redetect") {
      toast("原型演示：重新检测将生成独立预览，确认前不覆盖现有配置（接入后端后 POST /sources/" + s.id + "/rediscover）");
    } else if (act === "detail-view-items") {
      toast("原型演示：跳转资讯页并按来源筛选（接入后端后 GET /?source_id=" + s.id + "）");
    }
  });
}

/* ==========================================================================
   设置页面
   ========================================================================== */
function bindSettingsPage() {
  $("#setting-enabled").addEventListener("change", function (e) {
    var on = e.target.checked;
    $all("#schedule-fields input, #schedule-fields select").forEach(function (el) {
      el.disabled = !on;
    });
    $("#scheduler-status").textContent = on ? "等待下一次运行" : "已关闭";
    $("#scheduler-status").className = "status " + (on ? "status-ok" : "status-muted");
  });

  $("#settings-save").addEventListener("click", function () {
    var days = $all("#weekday-chips input:checked").length;
    if (days === 0) {
      toast("请至少选择一个执行星期");
      return;
    }
    toast("原型演示：设置已保存并立即生效（接入后端后 POST /settings）");
  });
}

/* ==========================================================================
   更新记录页面
   ========================================================================== */
var RUNS = [
  {
    id: 86, status: "成功", statusKind: "ok", trigger: "定时",
    started: "2026-07-22 08:30", finished: "08:33", duration: "3 分 12 秒",
    sourcesOk: 9, sourcesTotal: 9,
    fetched: 54, accepted: 41, rejected: 13, classified: 41,
    inserted: 12, updated: 29, duplicate: 8, failed: 0,
    perSource: [
      { name: "国家数据局", result: "成功", resultKind: "ok", fetched: 6, accepted: 5, inserted: 2, note: "" },
      { name: "国家互联网信息办公室（网信办）", result: "成功", resultKind: "ok", fetched: 4, accepted: 3, inserted: 1, note: "" },
      { name: "中国互联网协会", result: "部分成功", resultKind: "warn", fetched: 3, accepted: 2, inserted: 1, note: "2 个栏目结构变化已跳过" },
      { name: "DeepSeek 官方更新", result: "成功", resultKind: "ok", fetched: 2, accepted: 2, inserted: 1, note: "" },
      { name: "量子位", result: "成功", resultKind: "ok", fetched: 11, accepted: 5, inserted: 3, note: "" },
      { name: "36氪 AI 频道", result: "部分成功", resultKind: "warn", fetched: 7, accepted: 3, inserted: 2, note: "验证码拦截，已降频" }
    ],
    rejectReasons: [["内容范围不匹配", 5], ["质量分低于来源门槛", 4], ["未命中来源准入关键词", 4]],
    failReasons: [],
    error: null,
    ai: "自动分类 12 条：成功 12，失败 0（deepseek-chat）"
  },
  {
    id: 85, status: "部分失败", statusKind: "warn", trigger: "定时",
    started: "2026-07-21 08:30", finished: "08:34", duration: "4 分 02 秒",
    sourcesOk: 8, sourcesTotal: 9,
    fetched: 47, accepted: 38, rejected: 9, classified: 36,
    inserted: 9, updated: 27, duplicate: 6, failed: 2,
    perSource: [
      { name: "智谱 AI 开放平台更新日志", result: "失败", resultKind: "error", fetched: 0, accepted: 0, inserted: 0, note: "连接超时（10 秒）" },
      { name: "国家数据局", result: "成功", resultKind: "ok", fetched: 4, accepted: 3, inserted: 1, note: "" },
      { name: "百度千帆大模型平台动态", result: "成功", resultKind: "ok", fetched: 3, accepted: 3, inserted: 1, note: "" },
      { name: "量子位", result: "成功", resultKind: "ok", fetched: 9, accepted: 4, inserted: 2, note: "" }
    ],
    rejectReasons: [["内容范围不匹配", 4], ["质量分低于来源门槛", 3], ["外部链接不允许", 2]],
    failReasons: [["网络抓取失败", 1], ["页面解析或采集器失败", 1]],
    error: "智谱 AI 开放平台更新日志：连接超时（10 秒），本次已跳过该来源，其余来源正常完成。",
    ai: "自动分类 9 条：成功 9，失败 0（deepseek-chat）"
  },
  {
    id: 84, status: "成功", statusKind: "ok", trigger: "网页手动",
    started: "2026-07-20 15:02", finished: "15:04", duration: "2 分 18 秒",
    sourcesOk: 9, sourcesTotal: 9,
    fetched: 49, accepted: 39, rejected: 10, classified: 39,
    inserted: 10, updated: 29, duplicate: 7, failed: 0,
    perSource: [
      { name: "国家数据局", result: "成功", resultKind: "ok", fetched: 5, accepted: 4, inserted: 2, note: "" },
      { name: "DeepSeek 官方更新", result: "成功", resultKind: "ok", fetched: 1, accepted: 1, inserted: 1, note: "" },
      { name: "量子位", result: "成功", resultKind: "ok", fetched: 13, accepted: 6, inserted: 4, note: "" }
    ],
    rejectReasons: [["内容范围不匹配", 6], ["未命中来源准入关键词", 4]],
    failReasons: [],
    error: null,
    ai: null
  },
  {
    id: 83, status: "失败", statusKind: "error", trigger: "定时",
    started: "2026-07-20 08:30", finished: "08:31", duration: "48 秒",
    sourcesOk: 2, sourcesTotal: 9,
    fetched: 6, accepted: 5, rejected: 1, classified: 0,
    inserted: 0, updated: 0, duplicate: 0, failed: 7,
    perSource: [
      { name: "国家数据局", result: "成功", resultKind: "ok", fetched: 4, accepted: 3, inserted: 0, note: "入库阶段中止" },
      { name: "国家互联网信息办公室（网信办）", result: "成功", resultKind: "ok", fetched: 2, accepted: 2, inserted: 0, note: "入库阶段中止" },
      { name: "其余 7 个来源", result: "失败", resultKind: "error", fetched: 0, accepted: 0, inserted: 0, note: "数据库写入失败" }
    ],
    rejectReasons: [["质量分低于来源门槛", 1]],
    failReasons: [["数据库写入失败", 7]],
    error: "本地数据库被锁定（可能由备份任务占用），写入阶段中止，本次未产生新增资讯；已自动释放锁定，下一次定时运行恢复正常。",
    ai: null
  },
  {
    id: 82, status: "成功", statusKind: "ok", trigger: "定时",
    started: "2026-07-19 08:30", finished: "08:33", duration: "3 分 05 秒",
    sourcesOk: 9, sourcesTotal: 9,
    fetched: 58, accepted: 44, rejected: 14, classified: 44,
    inserted: 14, updated: 30, duplicate: 9, failed: 0,
    perSource: [
      { name: "国家数据局", result: "成功", resultKind: "ok", fetched: 5, accepted: 4, inserted: 2, note: "" },
      { name: "36氪 AI 频道", result: "成功", resultKind: "ok", fetched: 10, accepted: 4, inserted: 3, note: "" }
    ],
    rejectReasons: [["内容范围不匹配", 7], ["质量分低于来源门槛", 7]],
    failReasons: [],
    error: null,
    ai: "自动分类 14 条：成功 13，失败 1，回退规则分类 1（deepseek-chat）"
  },
  {
    id: 81, status: "部分失败", statusKind: "warn", trigger: "命令行手动",
    started: "2026-07-18 17:41", finished: "17:44", duration: "3 分 26 秒",
    sourcesOk: 8, sourcesTotal: 9,
    fetched: 45, accepted: 33, rejected: 12, classified: 33,
    inserted: 8, updated: 25, duplicate: 5, failed: 1,
    perSource: [
      { name: "36氪 AI 频道", result: "失败", resultKind: "error", fetched: 0, accepted: 0, inserted: 0, note: "验证码拦截" },
      { name: "量子位", result: "成功", resultKind: "ok", fetched: 12, accepted: 5, inserted: 3, note: "" }
    ],
    rejectReasons: [["内容范围不匹配", 6], ["未命中来源准入关键词", 6]],
    failReasons: [["网络抓取失败", 1]],
    error: "36氪 AI 频道：列表页验证码拦截，本次跳过。",
    ai: null
  }
];

var runOpen = null;
var runFilters = { status: "", trigger: "" };

function renderRuns() {
  var list = RUNS.filter(function (r) {
    if (runFilters.status && r.status !== runFilters.status) return false;
    if (runFilters.trigger && r.trigger !== runFilters.trigger) return false;
    return true;
  });

  if (list.length === 0) {
    $("#runs-table-wrap").innerHTML =
      '<div class="empty-state"><h2>没有符合条件的更新记录</h2><p>请调整筛选条件后重试。</p></div>';
    return;
  }

  var rows = list.map(function (run) {
    var open = runOpen === run.id;
    var main =
      '<tr class="tr-expandable' + (open ? " is-open" : "") + '" data-run="' + run.id + '">' +
        '<td data-label="状态" class="cell-block"><div><span class="expand-caret"></span>' + statusBadge(run.status, run.statusKind) + '</div><div class="cell-sub">#' + run.id + "</div></td>" +
        '<td data-label="触发方式">' + esc(run.trigger) + "</td>" +
        '<td data-label="开始 / 完成" class="cell-block"><div class="cell-time">' + esc(run.started) + '</div><div class="cell-sub">' + esc(run.finished) + " 完成</div></td>" +
        '<td data-label="耗时" class="cell-time col-optional">' + esc(run.duration) + "</td>" +
        '<td data-label="来源" class="num">' + run.sourcesOk + " / " + run.sourcesTotal + "</td>" +
        '<td data-label="抓取" class="num">' + run.fetched + "</td>" +
        '<td data-label="通过准入" class="num">' + run.accepted + "</td>" +
        '<td data-label="拒绝" class="num">' + run.rejected + "</td>" +
        '<td data-label="分类" class="num col-optional">' + run.classified + "</td>" +
        '<td data-label="新增" class="num">' + run.inserted + "</td>" +
        '<td data-label="更新" class="num col-optional">' + run.updated + "</td>" +
        '<td data-label="重复" class="num col-optional">' + run.duplicate + "</td>" +
        '<td data-label="失败" class="num">' + run.failed + "</td>" +
      "</tr>";

    var perSourceRows = run.perSource.map(function (ps) {
      return (
        "<tr><td>" + esc(ps.name) + "</td><td>" + statusBadge(ps.result, ps.resultKind) +
        '</td><td class="num">' + ps.fetched + '</td><td class="num">' + ps.accepted +
        '</td><td class="num">' + ps.inserted + "</td><td>" + esc(ps.note || "—") + "</td></tr>"
      );
    }).join("");

    var rejectItems = run.rejectReasons.map(function (rr) {
      return "<li><span>" + esc(rr[0]) + "</span><b>" + rr[1] + " 条</b></li>";
    }).join("");
    var failItems = run.failReasons.map(function (rr) {
      return "<li><span>" + esc(rr[0]) + "</span><b>" + rr[1] + " 条</b></li>";
    }).join("");

    return main +
      '<tr class="tr-expand' + (open ? " is-open" : "") + '">' +
        '<td colspan="13">' +
          '<div class="expand-grid">' +
            '<div class="expand-block"><h3>各来源结果</h3>' +
              '<div class="table-wrap"><table class="mini-table">' +
                "<thead><tr><th>来源</th><th>结果</th><th>抓取</th><th>准入</th><th>新增</th><th>备注</th></tr></thead>" +
                "<tbody>" + perSourceRows + "</tbody></table></div></div>" +
            '<div class="expand-block"><h3>未通过准入原因</h3>' +
              '<ul class="reason-list">' + rejectItems + "</ul>" +
              (failItems ? '<h3 style="margin-top:12px">处理失败原因</h3><ul class="reason-list">' + failItems + "</ul>" : "") +
            "</div>" +
            '<div class="expand-block"><h3>运行信息</h3>' +
              '<dl class="kv-list">' +
                '<div class="kv-row"><dt>总耗时</dt><dd>' + esc(run.duration) + "</dd></div>" +
                '<div class="kv-row"><dt>触发方式</dt><dd>' + esc(run.trigger) + "</dd></div>" +
                (run.ai ? '<div class="kv-row"><dt>AI 调用</dt><dd>' + esc(run.ai) + "</dd></div>" : "") +
              "</dl>" +
              (run.error ? '<h3 style="margin-top:12px">错误摘要</h3><div class="error-box">' + esc(run.error) + "</div>" : "") +
            "</div>" +
          "</div>" +
        "</td>" +
      "</tr>";
  }).join("");

  $("#runs-table-wrap").innerHTML =
    '<div class="table-wrap"><table class="data-table table-cards">' +
      "<thead><tr>" +
        "<th>状态</th><th>触发方式</th><th>开始 / 完成</th>" +
        '<th class="col-optional">耗时</th><th>来源</th><th>抓取</th><th>通过准入</th><th>拒绝</th>' +
        '<th class="col-optional">分类</th><th>新增</th><th class="col-optional">更新</th>' +
        '<th class="col-optional">重复</th><th>失败</th>' +
      "</tr></thead><tbody>" + rows + "</tbody></table></div>";
}

function bindRunsPage() {
  renderRuns();

  $("#runs-table-wrap").addEventListener("click", function (e) {
    var tr = e.target.closest("[data-run]");
    if (!tr) return;
    var id = Number(tr.getAttribute("data-run"));
    runOpen = runOpen === id ? null : id;
    renderRuns();
  });

  $("#runs-filter-form").addEventListener("submit", function (e) {
    e.preventDefault();
    runFilters = { status: $("#rf-status").value, trigger: $("#rf-trigger").value };
    renderRuns();
  });
  $("#rf-clear").addEventListener("click", function () {
    $("#runs-filter-form").reset();
    runFilters = { status: "", trigger: "" };
    renderRuns();
  });
}

/* ---------- 启动 ---------- */
document.addEventListener("DOMContentLoaded", function () {
  renderLists();
  bindNav();
  bindFilters();
  bindToolbar();
  bindLists();
  bindAiPage();
  bindSourcesPage();
  bindSourceDetail();
  bindSettingsPage();
  bindRunsPage();
});

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
function bindNav() {
  $all(".main-nav a, .brand, [data-page].btn").forEach(function (el) {
    el.addEventListener("click", function (e) {
      e.preventDefault();
      var page = el.getAttribute("data-page");
      if (!page) return;
      $all(".page").forEach(function (p) {
        p.hidden = p.id !== "page-" + page;
      });
      $all(".main-nav a").forEach(function (a) {
        var active = a.getAttribute("data-page") === page;
        a.classList.toggle("is-active", active);
        if (active) a.setAttribute("aria-current", "page");
        else a.removeAttribute("aria-current");
      });
      window.scrollTo({ top: 0 });
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

/* ---------- 启动 ---------- */
document.addEventListener("DOMContentLoaded", function () {
  renderLists();
  bindNav();
  bindFilters();
  bindToolbar();
  bindLists();
});

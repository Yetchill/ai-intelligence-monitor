document.addEventListener("DOMContentLoaded", function() {
  var today = new Date().toISOString().split("T")[0];
  var dateInputs = document.querySelectorAll("input[type='date']");
  dateInputs.forEach(function(input) {
    if (!input.getAttribute("max")) {
      input.setAttribute("max", today);
    }
  });
});
  const form = event.target;
  if (!(form instanceof HTMLFormElement) || !form.matches("[data-update-form]")) return;
  const button = form.querySelector("button[type='submit']");
  if (!(button instanceof HTMLButtonElement)) return;
  button.disabled = true;
  button.textContent = button.dataset.processingText || "处理中…";
  button.setAttribute("aria-busy", "true");
});

window.markRead = function(itemId) {
  fetch("/items/" + itemId + "/read", {
    method: "POST",
    headers: {"Content-Type": "application/x-www-form-urlencoded"},
    body: "is_read=true&return_to=" + encodeURIComponent(window.location.pathname + window.location.search)
  }).then(function() {
    var cb = document.querySelector("input[type='checkbox'][value='" + itemId + "']");
    if (cb) {
      var card = cb.closest("article");
      if (card) card.classList.remove("unread");
    }
  });
};

window.updateBatchSelection = function() {
  var checked = document.querySelectorAll(".item-checkbox:checked");
  var ids = Array.from(checked).map(function(cb) { return cb.value; });
  var input = document.getElementById("batch-item-ids");
  if (input) input.value = ids.join(",");
};

window.batchRead = function(isRead) {
  var checked = document.querySelectorAll(".item-checkbox:checked");
  if (checked.length === 0) { alert("请先勾选需要操作的资讯。"); return; }
  var ids = Array.from(checked).map(function(cb) { return cb.value; });
  document.getElementById("batch-item-ids").value = ids.join(",");
  var readInput = document.querySelector("#batch-read-form input[name='is_read']");
  if (readInput) readInput.value = isRead ? "true" : "false";
  document.getElementById("batch-read-form").submit();
};

window.batchAIClassify = function() {
  var checked = document.querySelectorAll(".item-checkbox:checked");
  if (checked.length === 0) { alert("请先勾选需要操作的资讯。"); return; }
  if (!confirm("确认对勾选的 " + checked.length + " 条资讯执行 AI 分类？")) return;
  var ids = Array.from(checked).map(function(cb) { return cb.value; });
  document.getElementById("batch-ai-item-ids").value = ids.join(",");
  document.getElementById("batch-ai-classify-form").submit();
};

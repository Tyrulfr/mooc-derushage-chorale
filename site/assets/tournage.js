(function () {
  var STORAGE_KEY = "mooc-tournage-suivi-v2";
  var FIELDS = ["filme", "monte", "valide", "implemente"];

  function loadState() {
    try {
      var raw = window.localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : {};
    } catch (err) {
      return {};
    }
  }

  function saveState(state) {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }

  function applyGroup(group, value) {
    var buttons = group.querySelectorAll("button[data-value]");
    buttons.forEach(function (btn) {
      var on = btn.getAttribute("data-value") === value;
      btn.classList.toggle("is-on", on);
      btn.setAttribute("aria-pressed", on ? "true" : "false");
    });
  }

  function groupsFor(id, field) {
    var found = [];
    document.querySelectorAll("[data-tournage-id][data-tournage-field]").forEach(function (group) {
      if (
        group.getAttribute("data-tournage-id") === id &&
        group.getAttribute("data-tournage-field") === field
      ) {
        found.push(group);
      }
    });
    return found;
  }

  function init() {
    var state = loadState();
    document.querySelectorAll("[data-tournage-id][data-tournage-field]").forEach(function (group) {
      var id = group.getAttribute("data-tournage-id");
      var field = group.getAttribute("data-tournage-field");
      if (!id || FIELDS.indexOf(field) === -1) {
        return;
      }
      var current = (state[id] && state[id][field]) || "non";
      applyGroup(group, current);
      group.querySelectorAll("button[data-value]").forEach(function (btn) {
        btn.addEventListener("click", function () {
          var value = btn.getAttribute("data-value") || "non";
          if (!state[id]) {
            state[id] = {};
          }
          state[id][field] = value;
          saveState(state);
          groupsFor(id, field).forEach(function (sibling) {
            applyGroup(sibling, value);
          });
        });
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

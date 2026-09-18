(function () {
  function readView(root, views) {
    var hash = (window.location.hash || "").replace("#", "");
    if (views.indexOf(hash) !== -1) {
      return hash;
    }
    var key = root.getAttribute("data-split-storage") || "";
    if (key) {
      try {
        var stored = window.localStorage.getItem(key);
        if (views.indexOf(stored) !== -1) {
          return stored;
        }
      } catch (err) {
        /* ignore */
      }
    }
    return views[0];
  }

  function applyView(root, views, view) {
    var chosen = views.indexOf(view) !== -1 ? view : views[0];
    root.querySelectorAll("[data-split-view]").forEach(function (btn) {
      var on = btn.getAttribute("data-split-view") === chosen;
      btn.setAttribute("aria-selected", on ? "true" : "false");
    });
    root.querySelectorAll("[data-split-panel]").forEach(function (panel) {
      var on = panel.getAttribute("data-split-panel") === chosen;
      if (on) {
        panel.removeAttribute("hidden");
      } else {
        panel.setAttribute("hidden", "hidden");
      }
    });
    var key = root.getAttribute("data-split-storage") || "";
    if (key) {
      try {
        window.localStorage.setItem(key, chosen);
      } catch (err) {
        /* ignore */
      }
    }
    if ((window.location.hash || "").replace("#", "") !== chosen) {
      if (window.history && window.history.replaceState) {
        window.history.replaceState(null, "", "#" + chosen);
      } else {
        window.location.hash = chosen;
      }
    }
  }

  function initRoot(root) {
    var views = (root.getAttribute("data-split-options") || "video,nom")
      .split(",")
      .map(function (item) {
        return item.trim();
      })
      .filter(Boolean);
    if (!views.length) {
      return;
    }
    applyView(root, views, readView(root, views));
    root.querySelectorAll("[data-split-view]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        applyView(root, views, btn.getAttribute("data-split-view") || views[0]);
      });
    });
    window.addEventListener("hashchange", function () {
      applyView(root, views, readView(root, views));
    });
  }

  function init() {
    document.querySelectorAll("[data-split-views]").forEach(initRoot);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

(function () {
  "use strict";

  const scriptEl = document.getElementById("script-final");
  const panel = document.getElementById("export-word-panel");
  if (!scriptEl || !panel) {
    return;
  }

  const modal = document.getElementById("export-word-modal");
  const openBtn = document.getElementById("export-word-open");
  const cancelBtn = document.getElementById("export-word-cancel");
  const pickDirBtn = document.getElementById("export-word-pick-dir");
  const exportBtn = document.getElementById("export-word-run");
  const filenameInput = document.getElementById("export-word-filename");
  const folderLabel = document.getElementById("export-word-folder");
  const folderField = document.getElementById("export-word-folder-field");
  const browserHint = document.getElementById("export-word-browser-hint");
  const statusEl = document.getElementById("export-word-status");

  const capsuleCode = panel.dataset.capsuleCode || "capsule";
  const capsuleTitle = panel.dataset.capsuleTitle || document.title;

  const capabilities = detectCapabilities();
  let directoryHandle = null;

  const presetFilename = filenameInput.value.trim();
  const defaultFilename = presetFilename || `script_${slugify(capsuleCode)}.doc`;
  filenameInput.value = defaultFilename;

  configureBrowserUi();

  openBtn.addEventListener("click", openModal);
  cancelBtn.addEventListener("click", closeModal);
  pickDirBtn.addEventListener("click", pickDirectory);
  exportBtn.addEventListener("click", runExport);
  modal.addEventListener("click", (event) => {
    if (event.target === modal) {
      closeModal();
    }
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !modal.hidden) {
      closeModal();
    }
  });

  function detectCapabilities() {
    const ua = navigator.userAgent || "";
    const isFirefox = /firefox\//i.test(ua) && !/seamonkey\//i.test(ua);
    return {
      directoryPicker: typeof window.showDirectoryPicker === "function",
      saveFilePicker: typeof window.showSaveFilePicker === "function",
      isFirefox,
      isFileProtocol: window.location.protocol === "file:",
    };
  }

  function configureBrowserUi() {
    if (capabilities.isFirefox) {
      pickDirBtn.disabled = true;
      pickDirBtn.setAttribute("aria-disabled", "true");
      folderLabel.textContent = "Non disponible dans Firefox";
      if (browserHint) {
        browserHint.textContent =
          "Firefox enregistre le fichier via le telechargement du navigateur. " +
          "Vous pouvez choisir le dossier de destination si l'option " +
          "« Toujours demander où enregistrer les fichiers » est activee dans les preferences Firefox.";
      }
      if (folderField) {
        folderField.classList.add("export-folder--disabled");
      }
      return;
    }

    if (!capabilities.directoryPicker) {
      pickDirBtn.disabled = true;
      pickDirBtn.setAttribute("aria-disabled", "true");
      folderLabel.textContent = "Selection de dossier non disponible";
      if (browserHint) {
        browserHint.textContent =
          "Ce navigateur utilisera la boite « Enregistrer sous » ou le telechargement.";
      }
    }
  }

  function openModal() {
    resetStatus();
    if (capabilities.isFileProtocol) {
      setStatus(
        "Page ouverte en file:// : ouvrez le site via un serveur local pour un export fiable dans Firefox.",
        "warn"
      );
    }
    modal.hidden = false;
    openBtn.setAttribute("aria-expanded", "true");
  }

  function closeModal() {
    modal.hidden = true;
    openBtn.setAttribute("aria-expanded", "false");
  }

  function resetStatus() {
    statusEl.textContent = "";
    statusEl.className = "export-status";
  }

  function setStatus(message, kind) {
    statusEl.textContent = message;
    statusEl.className = `export-status ${kind || ""}`.trim();
  }

  function slugify(value) {
    return value
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/^_+|_+$/g, "");
  }

  function escapeHtml(value) {
    return value
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function parseScriptBlocks(text) {
    const lines = text.replace(/\r\n/g, "\n").split("\n");
    const blocks = [];
    let current = null;

    const headerPattern =
      /^\[([^\]]+)\]\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+)$/;

    for (const line of lines) {
      const match = line.match(headerPattern);
      if (match) {
        if (current) {
          current.verbatim = current.verbatim.join("\n").trim();
          blocks.push(current);
        }
        current = {
          id: match[1].trim(),
          chercheur: match[2].trim(),
          source: match[3].trim(),
          timecodes: match[4].trim(),
          verbatim: [],
        };
        continue;
      }
      if (current) {
        current.verbatim.push(line);
      }
    }

    if (current) {
      current.verbatim = current.verbatim.join("\n").trim();
      blocks.push(current);
    }

    return blocks;
  }

  function buildWordDocument(title, blocks, rawScript) {
    const generatedAt = new Date().toLocaleString("fr-FR");
    let body = "";

    if (blocks.length) {
      body = blocks
        .map((block, index) => {
          return `
            <h2 style="font-size:13pt;margin:18pt 0 6pt;">${index + 1}. ${escapeHtml(block.id)} — ${escapeHtml(block.chercheur)}</h2>
            <p class="meta" style="font-size:10pt;color:#555;margin:0 0 8pt;">
              Source : ${escapeHtml(block.source)}<br>
              Timecodes : ${escapeHtml(block.timecodes)}
            </p>
            <p style="margin:0 0 14pt;text-align:justify;">${escapeHtml(block.verbatim).replace(/\n/g, "<br>")}</p>
          `;
        })
        .join("");
    } else {
      body = `<pre style="white-space:pre-wrap;font-family:Calibri,sans-serif;">${escapeHtml(rawScript)}</pre>`;
    }

    return `<!DOCTYPE html>
<html xmlns:o="urn:schemas-microsoft-com:office:office"
      xmlns:w="urn:schemas-microsoft-com:office:word"
      xmlns="http://www.w3.org/TR/REC-html40">
<head>
  <meta charset="utf-8">
  <title>${escapeHtml(title)}</title>
  <!--[if gte mso 9]>
  <xml>
    <w:WordDocument>
      <w:View>Print</w:View>
      <w:Zoom>100</w:Zoom>
      <w:DoNotOptimizeForBrowser/>
    </w:WordDocument>
  </xml>
  <![endif]-->
  <style>
    @page { size: 21cm 29.7cm; margin: 2.5cm; }
    body { font-family: Calibri, Arial, sans-serif; font-size: 11pt; color: #111; }
    h1 { font-size: 18pt; margin: 0 0 8pt; }
    h2 { font-size: 13pt; }
    .subtitle { font-size: 10pt; color: #666; margin: 0 0 18pt; }
  </style>
</head>
<body>
  <h1>${escapeHtml(title)}</h1>
  <p class="subtitle">Script final — exporte le ${escapeHtml(generatedAt)}</p>
  ${body}
</body>
</html>`;
  }

  function buildBlob(title, scriptText) {
    const blocks = parseScriptBlocks(scriptText);
    const html = buildWordDocument(title, blocks, scriptText);
    return new Blob(["\ufeff", html], {
      type: "application/msword",
    });
  }

  function sanitizeFilename(value) {
    const trimmed = value.trim() || defaultFilename;
    const safe = trimmed.replace(/[\\/:*?"<>|]/g, "_");
    return safe.toLowerCase().endsWith(".doc") || safe.toLowerCase().endsWith(".docx")
      ? safe
      : `${safe}.doc`;
  }

  async function pickDirectory() {
    resetStatus();
    if (capabilities.isFirefox || !capabilities.directoryPicker) {
      setStatus(
        "La selection de dossier n'est pas disponible dans ce navigateur.",
        "warn"
      );
      return;
    }
    try {
      directoryHandle = await window.showDirectoryPicker({
        mode: "readwrite",
        id: "derushage-export-word",
      });
      folderLabel.textContent = directoryHandle.name;
      setStatus(`Dossier selectionne : ${directoryHandle.name}`, "ok");
    } catch (error) {
      if (error && error.name === "AbortError") {
        return;
      }
      setStatus(`Impossible d'ouvrir le selecteur de dossier : ${error.message}`, "error");
    }
  }

  async function saveWithDirectoryPicker(blob, filename) {
    const fileHandle = await directoryHandle.getFileHandle(filename, { create: true });
    const writable = await fileHandle.createWritable();
    await writable.write(blob);
    await writable.close();
    return `${directoryHandle.name}/${filename}`;
  }

  async function saveWithSavePicker(blob, filename) {
    const pickerTypes = [
      {
        description: "Document Word",
        accept: {
          "application/msword": [".doc"],
        },
      },
    ];
    const fileHandle = await window.showSaveFilePicker({
      suggestedName: filename,
      types: pickerTypes,
      id: "derushage-export-word-file",
    });
    const writable = await fileHandle.createWritable();
    await writable.write(blob);
    await writable.close();
    return fileHandle.name;
  }

  function saveWithDownload(blob, filename) {
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.style.display = "none";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    window.setTimeout(() => {
      URL.revokeObjectURL(url);
    }, 60000);

    return filename;
  }

  function saveWithObjectUrlFallback(blob, filename) {
    const url = URL.createObjectURL(blob);
    const opened = window.open(url, "_blank", "noopener,noreferrer");
    if (!opened) {
      URL.revokeObjectURL(url);
      throw new Error(
        "Firefox a bloque le telechargement. Autorisez les telechargements pour ce site ou utilisez un serveur local."
      );
    }
    window.setTimeout(() => {
      URL.revokeObjectURL(url);
    }, 120000);
    return filename;
  }

  async function saveExport(blob, filename) {
    if (directoryHandle && capabilities.directoryPicker && !capabilities.isFirefox) {
      return {
        destination: await saveWithDirectoryPicker(blob, filename),
        method: "directory",
      };
    }

    if (capabilities.saveFilePicker && !capabilities.isFirefox) {
      return {
        destination: await saveWithSavePicker(blob, filename),
        method: "save-picker",
      };
    }

    try {
      return {
        destination: saveWithDownload(blob, filename),
        method: "download",
      };
    } catch (error) {
      if (!capabilities.isFirefox) {
        throw error;
      }
      return {
        destination: saveWithObjectUrlFallback(blob, filename),
        method: "tab",
      };
    }
  }

  function successMessage(result) {
    if (result.method === "directory") {
      return `Export reussi : ${result.destination}`;
    }
    if (result.method === "save-picker") {
      return `Export reussi : ${result.destination}`;
    }
    if (result.method === "tab") {
      return (
        `Document ouvert dans un nouvel onglet (${result.destination}). ` +
        "Utilisez Fichier > Enregistrer sous dans Firefox."
      );
    }
    if (capabilities.isFirefox) {
      return (
        `Export lance : ${result.destination}. ` +
        "Verifiez votre dossier Telechargements ou la boite de dialogue Firefox."
      );
    }
    return `Fichier telecharge : ${result.destination}`;
  }

  async function runExport() {
    resetStatus();
    exportBtn.disabled = true;

    const scriptText = scriptEl.textContent.trim();
    if (!scriptText || scriptText === "A construire.") {
      setStatus("Le script final est vide : rien a exporter.", "error");
      exportBtn.disabled = false;
      return;
    }

    const filename = sanitizeFilename(filenameInput.value);
    const title = `${capsuleCode} — ${capsuleTitle}`;
    const blob = buildBlob(title, scriptText);

    try {
      const result = await saveExport(blob, filename);
      setStatus(successMessage(result), "ok");
    } catch (error) {
      if (error && error.name === "AbortError") {
        setStatus("Export annule.", "warn");
      } else {
        setStatus(`Echec de l'export : ${error.message}`, "error");
      }
    } finally {
      exportBtn.disabled = false;
    }
  }
})();

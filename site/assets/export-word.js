(function () {
  "use strict";

  const scriptEl = document.getElementById("script-final");
  const panel = document.getElementById("export-word-panel");
  if (!scriptEl || !panel) {
    return;
  }

  const briefEl = document.getElementById("export-brief-intervenant");
  const syntheseEl = document.getElementById("export-synthese-temoignages");
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
  const defaultFilename = presetFilename || `capsule_${slugify(capsuleCode)}.doc`;
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

  function sectionTitle(el, fallback) {
    if (!el || !el.dataset.sectionTitle) {
      return fallback;
    }
    return el.dataset.sectionTitle;
  }

  function parseScriptBlocks(text) {
    const chunks = text.replace(/\r\n/g, "\n").split(/\n\n+/).filter(Boolean);
    const blocks = [];

    for (const chunk of chunks) {
      const lines = chunk.split("\n");
      const header = lines[0] || "";
      const body = lines.slice(1).join("\n").trim();
      const extractMatch = header.match(/^\[([^\]]+)\]\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+)$/);

      if (extractMatch) {
        blocks.push({
          kind: "extract",
          id: extractMatch[1].trim(),
          chercheur: extractMatch[2].trim(),
          source: extractMatch[3].trim(),
          timecodes: extractMatch[4].trim(),
          verbatim: body,
        });
        continue;
      }

      if (header.startsWith("[CADRAGE")) {
        blocks.push({
          kind: "cadrage",
          header,
          verbatim: body,
        });
        continue;
      }

      blocks.push({
        kind: "raw",
        header,
        verbatim: body ? `${header}\n${body}`.trim() : header,
      });
    }

    return blocks;
  }

  function renderScriptBlocks(blocks, rawScript) {
    if (!blocks.length) {
      return `<pre style="white-space:pre-wrap;font-family:Calibri,sans-serif;">${escapeHtml(rawScript)}</pre>`;
    }

    let extractIndex = 0;
    return blocks
      .map((block) => {
        if (block.kind === "extract") {
          extractIndex += 1;
          return `
            <h3 style="font-size:13pt;margin:16pt 0 6pt;">${extractIndex}. ${escapeHtml(block.id)} — ${escapeHtml(block.chercheur)}</h3>
            <p class="meta" style="font-size:10pt;color:#555;margin:0 0 8pt;">
              Source : ${escapeHtml(block.source)}<br>
              Timecodes : ${escapeHtml(block.timecodes)}
            </p>
            <p style="margin:0 0 14pt;text-align:justify;">${escapeHtml(block.verbatim).replace(/\n/g, "<br>")}</p>
          `;
        }
        if (block.kind === "cadrage") {
          return `
            <h3 style="font-size:12pt;margin:16pt 0 6pt;color:#0b6e77;">${escapeHtml(block.header)}</h3>
            <p style="margin:0 0 14pt;font-style:italic;">${escapeHtml(block.verbatim).replace(/\n/g, "<br>")}</p>
          `;
        }
        return `<p style="margin:0 0 12pt;white-space:pre-wrap;">${escapeHtml(block.verbatim).replace(/\n/g, "<br>")}</p>`;
      })
      .join("");
  }

  function renderPlainSection(title, text) {
    if (!text) {
      return "";
    }
    return `
      <h2 style="font-size:15pt;margin:24pt 0 10pt;border-top:1pt solid #ccc;padding-top:16pt;">${escapeHtml(title)}</h2>
      <pre style="white-space:pre-wrap;font-family:Calibri,sans-serif;font-size:11pt;margin:0;">${escapeHtml(text)}</pre>
    `;
  }

  function buildWordDocument(title, payload) {
    const generatedAt = new Date().toLocaleString("fr-FR");
    const scriptBlocks = parseScriptBlocks(payload.script);
    const scriptHtml = renderScriptBlocks(scriptBlocks, payload.script);
    const syntheseHtml = renderPlainSection(payload.syntheseTitle, payload.synthese);
    const briefHtml = renderPlainSection(payload.briefTitle, payload.brief);

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
    h2 { font-size: 15pt; }
    h3 { font-size: 13pt; }
    .subtitle { font-size: 10pt; color: #666; margin: 0 0 18pt; }
  </style>
</head>
<body>
  <h1>${escapeHtml(title)}</h1>
  <p class="subtitle">Dossier capsule — exporte le ${escapeHtml(generatedAt)}</p>
  <h2 style="font-size:15pt;margin:18pt 0 10pt;">Script final chorale</h2>
  ${scriptHtml}
  ${syntheseHtml}
  ${briefHtml}
</body>
</html>`;
  }

  function buildBlob(title, payload) {
    const html = buildWordDocument(title, payload);
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

  function collectPayload() {
    const script = scriptEl.textContent.trim();
    const brief = briefEl ? briefEl.textContent.trim() : "";
    const synthese = syntheseEl ? syntheseEl.textContent.trim() : "";
    return {
      script,
      brief,
      synthese,
      briefTitle: sectionTitle(
        briefEl,
        "Proposition de cadrage pour la video expert"
      ),
      syntheseTitle: sectionTitle(syntheseEl, "Synthese des temoignages"),
    };
  }

  async function runExport() {
    resetStatus();
    exportBtn.disabled = true;

    const payload = collectPayload();
    const hasScript = payload.script && payload.script !== "A construire.";
    const hasBrief = Boolean(payload.brief);
    const hasSynthese = Boolean(payload.synthese);

    if (!hasScript && !hasBrief && !hasSynthese) {
      setStatus("Aucun contenu a exporter pour cette capsule.", "error");
      exportBtn.disabled = false;
      return;
    }

    const filename = sanitizeFilename(filenameInput.value);
    const title = `${capsuleCode} — ${capsuleTitle}`;
    const blob = buildBlob(title, payload);

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

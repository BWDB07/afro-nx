import { readDisc } from "./disc.mjs";
import { writeGameZip } from "./zip.mjs?v=3";
import { openDownload, prepareDownload } from "./download.mjs?v=3";

const disc = document.querySelector("#disc");
const dropZone = document.querySelector("#drop-zone");
const fileLabel = document.querySelector("#file-label");
const save = document.querySelector("#save");
const cancel = document.querySelector("#cancel");
const status = document.querySelector("#status");
const progress = document.querySelector("#progress");
let selected = null;
let selection = 0;
let controller = null;
const nativePicker = typeof window.showSaveFilePicker === "function";
let browserDownload = Boolean(prepareDownload());

function updateSaveButton() {
  save.textContent = browserDownload ? "Create Switch ZIP" : "Choose save location";
  save.disabled = !selected || Boolean(controller) || !(browserDownload || nativePicker);
}

function downloadUnavailable() {
  return "Open this page in desktop Chrome or Edge with downloads enabled.";
}

function announce(message, error = false) {
  status.textContent = message;
  status.toggleAttribute("data-error", error);
}

async function inspect(file) {
  if (!file || controller) return;
  const request = ++selection;
  selected = null;
  save.disabled = true;
  progress.hidden = true;
  fileLabel.textContent = file.name;
  announce("Checking the disc image…");
  try {
    const manifest = await readDisc(file);
    if (request !== selection) return;
    selected = { file, manifest };
    updateSaveButton();
    const total = (manifest.bytes / 2 ** 30).toFixed(2);
    announce(browserDownload || nativePicker
      ? `Supported disc · ${manifest.files.toLocaleString()} files · ${total} GiB`
      : `Disc verified. ${downloadUnavailable()}`, !(browserDownload || nativePicker));
  } catch (error) {
    if (request === selection) announce(error.message, true);
  }
}

disc.addEventListener("change", () => { void inspect(disc.files[0]); });
dropZone.addEventListener("dragover", (event) => {
  event.preventDefault();
  if (!controller) dropZone.classList.add("dragging");
});
dropZone.addEventListener("dragleave", () => dropZone.classList.remove("dragging"));
dropZone.addEventListener("drop", (event) => {
  event.preventDefault();
  dropZone.classList.remove("dragging");
  void inspect(event.dataTransfer.files[0]);
});
cancel.addEventListener("click", () => controller?.abort());

function generateSwitchFiles(file, manifest, signal) {
  const xex = manifest.entries.find((entry) => !entry.directory && entry.path.toLowerCase() === "default.xex");
  const worker = new Worker(new URL("shader-worker.mjs?v=8", import.meta.url), { type: "module" });
  function stop() { worker.terminate(); }
  return new Promise((resolve, reject) => {
    if (signal.aborted) {
      reject(signal.reason);
      return;
    }
    signal.addEventListener("abort", () => reject(signal.reason), { once: true });
    worker.addEventListener("error", (event) => reject(new Error(event.message || "Shader tools failed to start.")));
    worker.addEventListener("message", ({ data }) => {
      if (data.error) reject(new Error(data.error));
      else if (data.files) resolve(data.files);
      else {
        progress.value = data.fraction;
        announce(data.message);
      }
    });
    worker.postMessage(file.slice(xex.offset, xex.offset + xex.size));
  }).finally(stop);
}

save.addEventListener("click", async () => {
  if (!selected || controller) return;
  const chosen = selected;
  const { file, manifest } = chosen;
  controller = new AbortController();
  const streamed = browserDownload;
  updateSaveButton();
  disc.disabled = true;
  dropZone.setAttribute("aria-disabled", "true");
  let sink;
  let startingDownload = false;
  try {
    if (!streamed) {
      announce("Choose a folder in the Save As window.");
      const destination = await window.showSaveFilePicker({
        suggestedName: "AFRO-nx.zip",
        startIn: "downloads",
        types: [{ description: "ZIP archive", accept: { "application/zip": [".zip"] } }],
      });
      sink = await destination.createWritable();
    }
    progress.hidden = false;
    progress.value = 0;
    cancel.hidden = false;
    if (!chosen.runtime) {
      announce("Preparing the NRO and generating shaders from your ISO…");
      chosen.runtime = await generateSwitchFiles(file, manifest, controller.signal);
    }
    controller.signal.throwIfAborted();
    if (streamed) {
      startingDownload = true;
      announce("Starting the browser download…");
      sink = await openDownload(controller.signal);
    }
    progress.value = 0;
    announce("Writing the ZIP. Keep this tab open.");
    let lastPercent = -1;
    await writeGameZip(file, manifest, sink, controller.signal, (written, total) => {
      const fraction = written / total;
      const percent = Math.floor(fraction * 100);
      progress.value = fraction;
      if (percent !== lastPercent) {
        lastPercent = percent;
        announce(`Writing the ZIP · ${percent}%`);
      }
    }, chosen.runtime);
    controller.signal.throwIfAborted();
    cancel.hidden = true;
    announce("Finalizing the ZIP…");
    await sink.close();
    announce(streamed
      ? "ZIP sent to your browser downloads. Once it finishes, extract it to the root of your SD card."
      : "ZIP saved. Extract it to the root of your SD card.");
  } catch (error) {
    if (sink) await sink.abort().catch(() => {});
    progress.hidden = true;
    if (controller.signal.aborted) announce("ZIP creation cancelled.");
    else if (startingDownload && nativePicker) {
      browserDownload = false;
      announce("The browser download stopped. Select Choose save location to try saving directly.", true);
    } else if (error.name === "AbortError") {
      announce("No save location selected. Try again and choose a folder such as Downloads.");
    } else {
      announce(`Couldn't save the ZIP. ${error.message || downloadUnavailable()}`, true);
    }
  } finally {
    controller = null;
    cancel.hidden = true;
    disc.disabled = false;
    dropZone.removeAttribute("aria-disabled");
    updateSaveButton();
  }
});

if (!(browserDownload || nativePicker)) announce(downloadUnavailable(), true);

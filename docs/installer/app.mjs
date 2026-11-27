import { readDisc } from "./disc.mjs";
import { writeGameZip } from "./zip.mjs";

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
const supported = typeof window.showSaveFilePicker === "function";

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
    save.disabled = !supported;
    const total = (manifest.bytes / 2 ** 30).toFixed(2);
    announce(supported
      ? `Supported disc · ${manifest.files.toLocaleString()} files · ${total} GiB`
      : "Disc verified. Open this page in desktop Chrome or Edge to save the ZIP.");
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

save.addEventListener("click", async () => {
  if (!selected || controller) return;
  const { file, manifest } = selected;
  controller = new AbortController();
  save.disabled = true;
  disc.disabled = true;
  dropZone.setAttribute("aria-disabled", "true");
  let sink;
  try {
    const destination = await window.showSaveFilePicker({
      suggestedName: "AFRO-nx-game-files.zip",
      types: [{ description: "ZIP archive", accept: { "application/zip": [".zip"] } }],
    });
    sink = await destination.createWritable();
    progress.hidden = false;
    progress.value = 0;
    cancel.hidden = false;
    announce("Writing the ZIP. Keep this tab open.");
    let lastPercent = -1;
    await writeGameZip(file, manifest, sink, controller.signal, (written) => {
      const fraction = written / manifest.bytes;
      const percent = Math.floor(fraction * 100);
      progress.value = fraction;
      if (percent !== lastPercent) {
        lastPercent = percent;
        announce(`Writing the ZIP · ${percent}%`);
      }
    });
    controller.signal.throwIfAborted();
    cancel.hidden = true;
    announce("Finalizing the ZIP…");
    await sink.close();
    announce("ZIP saved. Extract it to the root of your SD card.");
  } catch (error) {
    if (sink) await sink.abort().catch(() => {});
    progress.hidden = true;
    if (error.name === "AbortError") announce("ZIP creation cancelled.");
    else announce(`Couldn't save the ZIP. ${error.message}`, true);
  } finally {
    controller = null;
    cancel.hidden = true;
    disc.disabled = false;
    dropZone.removeAttribute("aria-disabled");
    save.disabled = !supported;
  }
});

if (!supported) announce("Use desktop Chrome or Edge to save the ZIP.");

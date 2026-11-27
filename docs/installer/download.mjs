const NAME = "AFRO-nx.zip";
const serviceWorker = navigator.serviceWorker;
let registration;

export function prepareDownload() {
  if (!serviceWorker || !window.TransformStream) return;
  registration ??= serviceWorker.register("./download-worker.js?v=3");
  // A disabled service worker leaves the native file picker available.
  void registration.catch(() => {});
  return registration;
}

async function controllingWorker() {
  if (serviceWorker.controller) return serviceWorker.controller;
  return new Promise((resolve, reject) => {
    function cleanup() {
      clearTimeout(timer);
      serviceWorker.removeEventListener("controllerchange", changed);
    }
    function changed() {
      if (serviceWorker.controller) {
        cleanup();
        resolve(serviceWorker.controller);
      }
    }
    const timer = setTimeout(() => {
      cleanup();
      reject(new Error("The browser download helper did not start."));
    }, 6000);
    serviceWorker.addEventListener("controllerchange", changed);
    changed();
  });
}

function waitForDownload(port, state, signal) {
  return new Promise((resolve, reject) => {
    function cleanup() {
      port.onmessage = null;
      clearTimeout(timer);
      signal.removeEventListener("abort", cancelled);
    }
    function cancelled() {
      cleanup();
      reject(signal.reason);
    }
    const timer = setTimeout(() => {
      cleanup();
      reject(new Error("The browser did not start the download."));
    }, 8000);
    port.onmessage = (event) => {
      if (event.data === state) {
        cleanup();
        resolve();
      }
    };
    signal.addEventListener("abort", cancelled, { once: true });
    if (signal.aborted) cancelled();
  });
}

export async function openDownload(signal) {
  const pending = prepareDownload();
  if (!pending) throw new Error("This browser does not support streamed downloads.");
  const workerRegistration = await pending;
  const worker = await controllingWorker();
  signal.throwIfAborted();

  const id = crypto.randomUUID();
  const { readable, writable } = new TransformStream();
  const writer = writable.getWriter();
  const channel = new MessageChannel();
  signal.addEventListener("abort", () => { void writer.abort(signal.reason).catch(() => {}); }, { once: true });

  try {
    worker.postMessage({ kind: "zip", id, readable }, [channel.port2, readable]);
    await waitForDownload(channel.port1, "ready", signal);
    signal.throwIfAborted();
    const started = waitForDownload(channel.port1, "started", signal);
    const frame = document.createElement("iframe");
    frame.hidden = true;
    frame.title = NAME;
    frame.src = new URL(`__download/${id}`, workerRegistration.scope).href;
    document.body.append(frame);
    try {
      await started;
    } finally {
      // Attachment responses are handed to the browser's download manager.
      // Leave the frame attached until the stream closes or is cancelled.
      void writer.closed.finally(() => frame.remove()).catch(() => {});
    }
    return {
      write: (value) => writer.write(new Uint8Array(value.buffer, value.byteOffset, value.byteLength)),
      close: () => writer.close(),
      abort: (reason) => writer.abort(reason),
    };
  } catch (error) {
    void writer.abort(error).catch(() => {});
    throw error;
  } finally {
    channel.port1.close();
  }
}

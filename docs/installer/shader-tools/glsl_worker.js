// banjo-nx-installer: one GLSL worker (lib/glsl_job.js) on a Web Worker; worker.js runs several (lib/pool.js).
import createDxcModule from './wasm/dxc_web.mjs';
import createSpirvCrossModule from './wasm/spirv_cross.mjs';
import { loadPyodide } from './vendor/pyodide/pyodide.mjs';
import { glslJob } from './lib/glsl_job.js?v=7';

const handle = await glslJob({
  createDxc: createDxcModule,
  createSpirvCross: createSpirvCrossModule,
  loadPyodide,
  pyodideIndex: new URL('./vendor/pyodide/', import.meta.url).href,
  readPy: async (n) => {
    const r = await fetch(new URL(`./py/${n}?v=5`, import.meta.url));
    if (!r.ok) throw new Error(`py/${n}: HTTP ${r.status}`);
    return r.text();
  },
});
self.onmessage = ({ data }) => {
  const reply = handle(data);
  postMessage(reply, reply.glsl ? [reply.glsl.buffer] : []);
};
postMessage({ ready: true });

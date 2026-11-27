import makeTranslator from "./shader-tools/wasm/renut_hlsl.mjs";
import makeLzx from "./shader-tools/wasm/lzx.mjs";
import { compileVariants, makeGlsl, packageShaders, variantJobs } from "./shader-tools/lib/build.js";
import { gameContainers, sha256 } from "./shader-tools/lib/sources.js";
import { nroShaders } from "./shader-tools/lib/nro.js";
import { glslMaker, uamCompile, workerPool } from "./shader-tools/lib/pool.js";
import { parseVariants } from "./shader-tools/lib/variants.js";

const runtime = new URL("runtime/v0.1.0/", import.meta.url);
const say = (message, fraction) => postMessage({ message, fraction });
const quiet = () => ({ print() {}, printErr() {} });

async function get(name, expected) {
  const response = await fetch(new URL(name, runtime));
  if (!response.ok) throw new Error(`Could not load ${name} (HTTP ${response.status}).`);
  const bytes = new Uint8Array(await response.arrayBuffer());
  if (expected && await sha256(bytes) !== expected) throw new Error(`Checksum mismatch for ${name}.`);
  return bytes;
}

async function withPool(script, count, adapter, run) {
  const workers = [];
  try {
    const fatal = new Promise((_, reject) => {
      for (let i = 0; i < count; i++) {
        const worker = new Worker(new URL(script, import.meta.url), { type: "module" });
        workers.push(worker);
        worker.addEventListener("error", (error) => reject(
          new Error(error.message || "A shader compiler stopped unexpectedly.")));
      }
    });
    const ready = workers.map((worker) => new Promise((resolve) => {
      worker.addEventListener("message", ({ data }) => {
        if (data.ready) resolve(worker);
      });
    }));
    await Promise.race([Promise.all(ready), fatal]);
    const pool = workerPool(workers.map((worker) => ({
      post: (message, transfer) => worker.postMessage(message, transfer),
      onMessage: (callback) => worker.addEventListener("message", ({ data }) => callback(data)),
    })));
    return await Promise.race([run(adapter(pool)), fatal]);
  } finally {
    for (const worker of workers) worker.terminate();
  }
}

async function makeSwitchFiles(xexFile) {
  say("Loading the shader tools…", 0);
  const manifest = JSON.parse(new TextDecoder().decode(await get("manifest.json")));
  const xex = new Uint8Array(await xexFile.arrayBuffer());
  const hash = await sha256(xex);
  const build = manifest.builds.find((entry) => entry.xex_sha256 === hash);
  if (!build) throw new Error("This executable differs from the supported European disc.");

  const [nro, config, header, variants, translator, lzx] = await Promise.all([
    get(build.nro, build.nro_sha256),
    get(build.files[0].source, build.files[0].sha256),
    get("shader_common.h", manifest.shader_common_sha256),
    get("variants.txt", build.variants_sha256),
    makeTranslator(quiet()),
    makeLzx(quiet()),
  ]);
  const containers = await gameContainers([], xex, build.shaders, lzx);
  const count = Math.max(1, Math.min(3, (navigator.hardwareConcurrency || 2) - 1));
  say(`Translating ${containers.length} shaders from your disc…`, 0);
  const errors = [];
  const { shaders, failed } = await withPool("./shader-tools/glsl_worker.js", count, glslMaker,
    (translate) => makeGlsl(containers, translator, translate, header, undefined,
      (fraction) => say("Translating Xbox 360 shaders", fraction * 0.7),
      (error) => errors.push(error)));
  if (failed) throw new Error(errors[0] || `${failed} shaders could not be translated.`);
  const glsl = packageShaders(shaders);
  const shadersByName = new Map(shaders.map((shader) => [shader.name, shader.glsl]));
  for (const [name, text] of nroShaders(nro)) {
    if (!shadersByName.has(name)) shadersByName.set(name, text);
  }
  const { jobs } = variantJobs(parseVariants(new TextDecoder().decode(variants)), shadersByName);
  say(`Compiling ${jobs.length} Switch shader variants…`, 0.7);
  const compiled = await withPool("./shader-tools/uam_worker.js", count, uamCompile,
    (compile) => compileVariants(jobs, compile, count, (fraction) =>
      say("Compiling Switch shaders", 0.7 + fraction * 0.3)));
  if (compiled.failures.length) throw new Error(`Switch shader compilation failed. ${compiled.failures[0].error}`);

  return [
    { path: "AFRO-nx.nro", bytes: nro },
    { path: "renut.toml", bytes: config },
    { path: "deko3d_glsl.bin", bytes: glsl },
    { path: "deko3d_shaders.bin", bytes: compiled.cache },
  ];
}

self.addEventListener("message", async ({ data }) => {
  try {
    const files = await makeSwitchFiles(data);
    postMessage({ files }, [...new Set(files.map((file) => file.bytes.buffer))]);
  } catch (error) {
    postMessage({ error: error.message || String(error) });
  }
}, { once: true });

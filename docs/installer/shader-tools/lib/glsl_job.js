// One GLSL worker translates a shader through DXC, SPIRV-Cross and the reNut GLSL converter.
import { hlslToGlsl } from './chain.js';
import { loadPython } from './py.js?v=5';

const quiet = () => ({ print: () => {}, printErr: () => {} });

function matchAfroShaderInterface(name, hlsl) {
  // The native renderer uses the base sampler from SharedConstants.
  const source = hlsl.replace(/\(([A-Za-z_]\w*_SamplerDescriptorIndex) \+ \d+\)/g, '$1');
  if (!name.startsWith('vs_')) return source;

  // Remove the newer translator's unused exports before DXC assigns locations.
  // POSITION2 would shift POINTCOORD and POINTSIZE away from the runtime slots.
  return source
    .replace(/^\s*\tout float4 oPosition2 : POSITION2,\r?\n/m, '')
    .replace(/^\s*\t, out float oUserClip0 : SV_ClipDistance0\r?\n/m, '')
    .replace(/^\s*\toPosition2 = 0\.0;\r?\n/m, '')
    .replace(/^\s*\toUserClip0 = dot\(oPos, g_UserClipPlane\);\r?\n/m, '');
}

// tools: { createDxc, createSpirvCross } (Emscripten factories), loadPyodide, pyodideIndex, readPy(name) -> text.
// Returns handle(message) -> reply for { id, name, hlsl }: { id, glsl } (UTF-8 bytes) or { id, error }.
export async function glslJob({ createDxc, createSpirvCross, loadPyodide, pyodideIndex, readPy }) {
  // A fresh options object per module: Emscripten makes the object it is given the module itself.
  const modules = { dxc: await createDxc(quiet()), spirvCross: await createSpirvCross(quiet()) };
  const py = await loadPython(loadPyodide, pyodideIndex, readPy);
  const enc = new TextEncoder();
  return ({ id, name, hlsl }) => {
    try {
      const compatible = matchAfroShaderInterface(name, hlsl);
      const source = name === 'ps_069459B4C78435DC' ? py.lowerAfro(compatible) : compatible;
      return { id, glsl: enc.encode(hlslToGlsl(name, source, modules, py)) };
    } catch (e) {
      return { id, error: e.message || String(e) };
    }
  };
}

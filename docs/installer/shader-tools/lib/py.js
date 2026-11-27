// Reuse the reNut GLSL converter and alpha-test specialization pass in Pyodide.
export const PY_FILES = ['deko3d_glsl.py', 'deko3d_glsl_opt.py', 'afro_shader_control_flow.py'];

// These are the seven pixel shaders specialized in the native 30 FPS build.
const AFRO_ALPHA_SHADERS = new Set([
  '163BD6A60480DDE9',
  '467EB749EAC3E347',
  '4997278A08C8E6CC',
  '608ED747D8FC6BFD',
  '843E440D7537603D',
  '8B2CB556335D82C3',
  '8B40A121CE9265DB',
]);

export async function loadPython(loadPyodide, indexURL, readFile) {
  const pyodide = await loadPyodide({ indexURL });
  pyodide.FS.mkdirTree('/py');
  for (const name of PY_FILES) pyodide.FS.writeFile('/py/' + name, await readFile(name));
  pyodide.runPython(`
import sys
sys.path.insert(0, '/py')
import deko3d_glsl, deko3d_glsl_opt
from afro_shader_control_flow import lower as lower_afro

def _convert(text, stage):
    out, _ = deko3d_glsl.convert(text, stage, deko3d_glsl.DEFAULT_UBO_MAP, 'handle')
    return out

def _specialize_alpha(text):
    return deko3d_glsl_opt.pass_alpha(text)
`);
  const convert = pyodide.globals.get('_convert');
  const lowerAfro = pyodide.globals.get('lower_afro');
  const specializeAlpha = pyodide.globals.get('_specialize_alpha');
  return {
    lowerAfro: (text) => lowerAfro(text, 'threshold'),
    convert: (text, stage) => convert(text, stage),
    optimise: (text, stage, name) => (
      stage === 'frag' && AFRO_ALPHA_SHADERS.has(name) ? specializeAlpha(text) : text
    ),
  };
}

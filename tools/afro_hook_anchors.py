#!/usr/bin/env python3
"""Move only statically identified Afro D3D hook declarations.

These addresses come from docs/afro-d3d-census.md. Registration stays off
until the native bodies pass their device-layout audit. No inferred hook is
included. The script preserves source line endings and is idempotent.
"""
import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ANCHORS = {
    'Direct3D_CreateDevice_hook': '823649B8',
    'D3DDevice_Release_hook': '82364A68',
    'D3DDevice_AddRef_hook': '82364A50',
    'D3D_XenonGpu_Initialize_hook': '8236E820',
    'D3D_InitializeApiState_hook': '8236E0A8',
    'D3D_InitializePresentationParameters_hook': '8236E318',
    'D3D_CDevice_Uninitialize_hook': '8236EC28',
    'KickOff_hook': '82362E38',
    'BlockOnFence_hook': '823631E8',
    'D3DDevice_SetRingBufferParameters_hook': '82363A80',
    'D3DDevice_Swap_hook': '8236D4E0',
    'D3DDevice_Present_hook': '8236DB28',
    'D3DDevice_SetVertexShader_hook': '8234B408',
    'D3DDevice_SetPixelShader_hook': '8234AFA0',
    'D3DDevice_SetStreamSource_hook': '823486B8',
    'D3DDevice_SetIndices_hook': '82348860',
    'D3DDevice_SetViewport_hook': '82348630',
    'D3D_SetViewport_hook': '82345D38',
    'D3DDevice_SetScissorRect_hook': '82348490',
    'D3DDevice_SetDepthStencilSurface_hook': '82348C78',
    'D3DDevice_SetRenderTarget_hook': '82348930',
    'D3DDevice_CreateSurface_hook': '82357D78',
    'D3DDevice_Resolve_hook': '82371698',
    'D3DDevice_GetDeviceCaps_hook': '82359568',
    'D3DDevice_GetDisplayMode_hook': '82359598',
    'D3DDevice_CreateTexture_hook': '82357C58',
    'D3DDevice_CreateVertexBuffer_hook': '82354490',
    'D3DDevice_CreateIndexBuffer_hook': '82354788',
    'D3DDevice_CreatePixelShader_hook': '8234AE68',
    'D3DDevice_CreateVertexShader_hook': '8234B2D0',
    'D3DDevice_CreateVertexDeclaration_hook': '8234B820',
    'D3DDevice_ClearF_hook': '82370500',
    'D3DDevice_Clear_hook': '82370C70',
    'D3DResource_AddRef_hook': '823542A0',
    'D3DResource_Release_hook': '82354318',
    'D3DResource_GetType_hook': '82354400',
    'D3DResource_Destroy_hook': '82353B40',
    'D3D_UnlockResource_hook': '82354060',
    'LockResource_hook': '82353D68',
    'D3DDevice_SetGammaRamp_hook': '82349648',
    'D3DDevice_SetPWLGamma_hook': '82349730',
    'D3DDevice_DrawVertices_hook': '823FB998',
    'D3DDevice_DrawIndexedVertices_hook': '823FBD88',
    'D3DDevice_SetTexture_hook': '82358098',
    'D3DDevice_SetVertexDeclaration_hook': '8234B6A0',
    'D3DDevice_SetShaderGPRAllocation_hook': '8234BC48',
    'D3D_SetSurfaceClip_hook': '82345A08',
    'D3D_ResetAllState_hook': '82345880',
    'D3D_SetSurfaceInfo_hook': '82345978',
    'D3DDevice_SetScreenExtentQueryMode_hook': '8235A600',
}
DECL = re.compile(r'BANJO_RENUT_HOOK\(sub_([0-9A-F]{8}),\s*(\w+)\);')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    a = ap.parse_args()
    init = (ROOT / 'app/generated/renut_init.cpp').read_text(encoding='utf-8')
    starts = set(re.findall(r'\{ 0x([0-9A-F]{8}), sub_[0-9A-F]{8} \}', init))
    missing = sorted(set(ANCHORS.values()) - starts)
    if missing:
        raise SystemExit(f'not generated function starts: {missing}')
    found = set()
    changes = []
    for rel in ('app/src/renut_engine/gpu/d3d/hooks/device.cpp',
                'app/src/renut_engine/gpu/d3d/hooks/draw.cpp',
                'app/src/renut_engine/gpu/d3d/hooks/state.cpp',
                'app/src/renut_engine/gpu/d3d/hooks/resource.cpp',
                'app/src/renut_engine/gpu/d3d/hooks/shader.cpp'):
        path = ROOT / rel
        source = path.read_bytes().decode('utf-8')

        def remap(match):
            old, name = match.groups()
            new = ANCHORS.get(name)
            if new is None:
                return match.group(0)
            if name in found:
                raise SystemExit(f'duplicate hook name: {name}')
            found.add(name)
            if old != new:
                changes.append((name, old, new))
            return match.group(0).replace('sub_' + old, 'sub_' + new, 1)

        rewritten = DECL.sub(remap, source)
        if a.apply and rewritten != source:
            path.write_bytes(rewritten.encode('utf-8'))
    absent = sorted(set(ANCHORS) - found)
    if absent:
        raise SystemExit(f'missing hook declarations: {absent}')
    for name, old, new in changes:
        print(f'{name}: sub_{old} -> sub_{new}')
    print(f'{len(found)} anchors checked; {len(changes)} need changes'
          + (' (applied)' if a.apply else ' (dry run)'))


if __name__ == '__main__':
    main()

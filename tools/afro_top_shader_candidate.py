#!/usr/bin/env python3
"""Build a separate GLSL candidate for console-profiled Afro pixel shaders."""

import argparse
import collections
import pathlib
import shutil

import deko3d_glsl_opt as opt
import deko3d_shader_stats as stats
import deko3d_variant_cache as variants


HEAVY = ("608ED747D8FC6BFD", "4997278A08C8E6CC")

# The diffuse lookup and alpha calculation are independent of lighting in these shaders.
# Use exact statements so a regenerated shader with different inputs requires review.
ALPHA_QUAD_INPUTS = {
    "608ED747D8FC6BFD": (
        "    vec4 _131 = vec4(_130.x, _130.y, vec4(0.0).z, vec4(0.0).w);",
        "    vec4 _441 = texture(dk_tex_b5, _131.yx);",
        "    float _449 = _441.w * g_UboPixel.v[28u].w;",
        "_449",
    ),
    "4997278A08C8E6CC": (
        "    vec2 _136 = mix(_111.ww, in_var_TEXCOORD1.ww, equal(_126.xy, vec2(0.0))).yx;",
        "    vec4 _446 = texture(dk_tex_b5, _136);",
        "    float _464 = _446.w * g_UboPixel.v[28u].w;",
        "_464",
    ),
    "8B2CB556335D82C3": (
        "    vec4 _110 = vec4(vec2(in_var_TEXCOORD1.w, in_var_TEXCOORD0.w).x, "
        "vec2(in_var_TEXCOORD1.w, in_var_TEXCOORD0.w).y, vec4(0.0).z, vec4(0.0).w);",
        "    vec4 _165 = texture(dk_tex_b3, _110.yx);",
        "    float _179 = _165.w * g_UboPixel.v[28u].w;",
        "_179",
    ),
}


def early_alpha_quad(source, shader):
    """Skip lighting for an entire quad when its GREATER alpha test fails."""
    inputs = ALPHA_QUAD_INPUTS.get(shader)
    if inputs is None:
        raise SystemExit(f"no reviewed quad alpha test for {shader}")
    anchor, fetch, alpha, value = inputs
    if not all(source.count(line + "\n") == 1 for line in (anchor, fetch, alpha)):
        raise SystemExit(f"quad alpha test anchors changed for {shader}")
    if not all(part in source for part in (f"DK_ALPHA_FUNC == 4u) ? ({value} > ", "g_banjoAlphaFunc")):
        raise SystemExit(f"quad alpha test requires the specialized GREATER path for {shader}")

    for line in (fetch, alpha):
        source = source.replace(line + "\n", "#if SPIRV_CROSS_CONSTANT_ID_903 != 5u\n" + line + "\n#endif\n", 1)

    # Keep the late per-fragment test. For mixed quads its neighbors must still supply
    # the implicit texture derivatives. A comparison against NaN fails in both tests.
    quad_test = (
        "#if SPIRV_CROSS_CONSTANT_ID_903 == 5u\n"
        f"{fetch}\n{alpha}\n"
        f"    float afroAlphaFailed = ({value} > uintBitsToFloat(g_UboShared.v[34u].z)) ? 0.0 : 1.0;\n"
        "    float afroFailedDx = dFdxFine(afroAlphaFailed);\n"
        "    float afroFailedPair = (afroAlphaFailed == 1.0 && afroFailedDx == 0.0) ? 1.0 : 0.0;\n"
        "    float afroFailedDy = dFdyFine(afroFailedPair);\n"
        "    if (afroFailedPair == 1.0 && afroFailedDy == 0.0) {\n"
        "        discard;\n"
        "        return;\n"
        "    }\n"
        "#endif\n"
    )
    return source.replace(anchor + "\n", anchor + "\n" + quad_test, 1)


def main():
    stats.TABLE = stats.opcode_table()
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=pathlib.Path, required=True)
    ap.add_argument("--output", type=pathlib.Path, required=True)
    ap.add_argument("--passes", default=opt.DEFAULT,
                    help="comma-separated GLSL passes, or alphaquad for the reviewed Afro shaders")
    ap.add_argument("--pipeline-list", type=pathlib.Path)
    ap.add_argument("--shaders", default=",".join(HEAVY))
    ap.add_argument("--uam", type=pathlib.Path, default=pathlib.Path(stats.UAM),
                    help="host uam executable from the Switch build's compiler source")
    args = ap.parse_args()
    shaders = tuple(s.strip().upper() for s in args.shaders.split(","))
    if not shaders or any(len(s) != 16 or any(c not in "0123456789ABCDEF" for c in s) for s in shaders):
        raise SystemExit("--shaders requires comma-separated 16-digit hex hashes")
    if args.output.exists():
        raise SystemExit(f"output exists: {args.output}")
    shutil.copytree(args.source, args.output)
    if args.pipeline_list:
        counts = collections.Counter()
        for (_, ps), spec in variants.read_list(str(args.pipeline_list), True):
            if ps in shaders:
                counts[(ps, spec.get(903, 0))] += 1
        print(f"pipeline alpha function counts: {dict(counts)}")
    for hash_ in shaders:
        name = f"ps_{hash_}.glsl"
        path = args.output / name
        source = path.read_text(encoding="utf-8")
        candidate = (early_alpha_quad(source, hash_) if args.passes == "alphaquad"
                     else opt.optimise(source, args.passes, "frag", hash_))
        if candidate == source:
            raise SystemExit(f"no optimization for {name}")
        for label, text in (("raw", source), ("candidate", candidate)):
            for alpha in (0, 5, 7, 8):
                define = f"#define SPIRV_CROSS_CONSTANT_ID_903 {alpha}u\n" if alpha else ""
                text_variant = variants.variant_text(text, define).encode("utf-8")
                _, result, error = stats.compile_stats((name, "frag", text_variant), uam=args.uam)
                if error:
                    raise SystemExit(f"{name} {label} alpha={alpha}: {error}")
                print(f"{name} {label} alpha={alpha}: {result['instr']} instructions, "
                      f"{result['gprs']} GPR, {result['scratch']} scratch, "
                      f"{result['classes'].get('tex', 0)} texture instructions")
        path.write_text(candidate, encoding="utf-8", newline="\n")
    print(f"candidate GLSL: {args.output}")


if __name__ == "__main__":
    main()

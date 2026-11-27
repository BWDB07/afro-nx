# AFRO-nx shader tools

The WebAssembly modules, worker scripts, supporting JavaScript, and Python passes in this directory are from the reNut base installer at commit `851bf8fea21a3ce0fdba32d4000b5ddd482fcc54`. The upstream tree contains the WebAssembly build scripts and test harness. See [NOTICES.md](NOTICES.md) and [LICENSE](LICENSE) for attribution and licensing. [Upstream source](https://github.com/ChanseyIsTheBest/renut_nx_ultimate_installer/tree/851bf8fea21a3ce0fdba32d4000b5ddd482fcc54)

AFRO-nx supplies its own shader header and shader container checksums in the versioned runtime folder. It applies the port's threshold pass to shader `069459B4C78435DC` before translation, then builds the GLSL library and DKSH cache from the player's executable.

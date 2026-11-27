// Extract validated Xenos shader containers from Afro's decoded XEX image.
// Output files are game-derived and must stay in ignored out/ paths.
// Build: clang++ -std=c++20 -O2 -Iapp/thirdparty/reblue-XenosRecomp/thirdparty/xxHash
//        tools/afro_image_shaders.cpp -o out/tools/afro_image_shaders.exe
#include <cstdint>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <string>
#include <vector>

#define XXH_INLINE_ALL
#include <xxhash.h>

static uint32_t Be32(const uint8_t* p) {
  return uint32_t(p[0]) << 24 | uint32_t(p[1]) << 16 | uint32_t(p[2]) << 8 | p[3];
}

int main(int argc, char** argv) {
  if (argc != 3) {
    std::fprintf(stderr, "usage: afro_image_shaders <decoded image> <ignored output dir>\n");
    return 2;
  }
  const std::filesystem::path out(argv[2]);
  std::filesystem::create_directories(out);
  std::ifstream input(argv[1], std::ios::binary);
  if (!input) return 1;
  const std::vector<uint8_t> data((std::istreambuf_iterator<char>(input)), {});
  size_t vertex = 0, pixel = 0, duplicates = 0;
  for (size_t i = 0; i + 0x24 <= data.size(); i += 4) {
    const uint32_t magic = Be32(&data[i]);
    if ((magic & 0xFFFFFF00u) != 0x102A1100u) continue;
    const uint32_t virt = Be32(&data[i + 4]), phys = Be32(&data[i + 8]);
    const uint32_t ct = Be32(&data[i + 0x10]), dt = Be32(&data[i + 0x14]);
    const uint32_t so = Be32(&data[i + 0x18]);
    if (virt < 0x24 || virt >= 0x10000 || phys == 0 || phys >= 0x100000 ||
        i + size_t(virt) + phys > data.size() || ct >= virt || dt >= virt ||
        so < 0x24 || so >= virt - 8) continue;
    if (Be32(&data[i + so]) + Be32(&data[i + so + 4]) != phys) continue;
    const bool vs = magic & 1;
    const uint64_t hash = XXH3_64bits(&data[i], size_t(virt) + phys);
    char name[40];
    std::snprintf(name, sizeof(name), "%s_%016llx.bin", vs ? "vs" : "ps",
                  static_cast<unsigned long long>(hash));
    const auto path = out / name;
    if (std::filesystem::exists(path)) {
      ++duplicates;
      continue;
    }
    std::ofstream file(path, std::ios::binary);
    file.write(reinterpret_cast<const char*>(&data[i]), size_t(virt) + phys);
    if (!file) return 1;
    (vs ? vertex : pixel)++;
  }
  std::printf("%zu vertex, %zu pixel, %zu duplicate containers -> %s\n", vertex, pixel,
              duplicates, out.string().c_str());
}

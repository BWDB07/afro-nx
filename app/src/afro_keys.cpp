// AFRO-nx (2026-10-30): the keys of banjo-nx files this port does not build, because their code is written for
// N&B's addresses (cpu/banjo_reverb_native.cpp, cpu/banjo_xaudio_native.cpp, cpu/banjo_hot_guest.cpp,
// renut_engine/hooks.cpp, renut_engine/frameHooks.cpp). banjo-nx's enhancement table (cpu/banjo_enhancements.cpp) and
// Renut's renderer still read them by name, so they are defined here, off: nothing in this build uses their code.
// Each comes back with its own file once it has been moved to Afro Samurai's functions (docs/katamari-notes.md).

#include <rex/cvar.h>
#include <rex/ppc.h>

#include <algorithm>
#include <array>
#include <atomic>
#include <charconv>
#include <chrono>
#include <cstdint>
#include <string>
#include <thread>

#include "profiler/profiler.h"

// N&B's XAudio natives (its reverb and sample-rate converter at N&B's addresses).
REXCVAR_DEFINE_BOOL(banjo_native_reverb, false, "Afro Samurai/Not built", "N&B's native XAudio reverb (not in this port)")
    .lifecycle(rex::cvar::Lifecycle::kInitOnly);
REXCVAR_DEFINE_BOOL(banjo_native_reverb_verify, false, "Afro Samurai/Not built", "Verify mode of the above (not in this port)")
    .lifecycle(rex::cvar::Lifecycle::kInitOnly);
REXCVAR_DEFINE_BOOL(banjo_native_xaudio_src, false, "Afro Samurai/Not built", "N&B's native XAudio SRC (not in this port)")
    .lifecycle(rex::cvar::Lifecycle::kInitOnly);
REXCVAR_DEFINE_BOOL(banjo_native_xaudio_src_verify, false, "Afro Samurai/Not built", "Verify mode of the above (not in this port)")
    .lifecycle(rex::cvar::Lifecycle::kInitOnly);

// The hand-written natives' keys and banjo_hot_count are cpu/banjo_hot_guest.cpp's (Afro Samurai's natives: memset and the
// matrix routines, cpu/hot/banjo_hand_natives.h).

// renut_engine/hooks.cpp's MSAA switch, which Renut's renderer reads (render/surfaces and the tuning): N&B's own key.
// Afro Samurai's MSAA is what the game asks for.
REXCVAR_DEFINE_BOOL(disable_msaa, false, "Afro Samurai/Graphics", "Draw the game's MSAA targets with one sample (not exact)");

REXCVAR_DEFINE_STRING(frame_cap, "Off", "Afro Samurai/Performance",
                      "Frame rate cap: Off or a positive number of frames per second")
    .lifecycle(rex::cvar::Lifecycle::kInitOnly);

void renutFrameLimit() {
  using Clock = std::chrono::steady_clock;
  static const auto interval = [] {
    const auto& value = REXCVAR_GET(frame_cap);
    const auto* end = value.data() + value.size();
    int fps = 0;
    const auto parsed = std::from_chars(value.data(), end, fps);
    if (parsed.ec != std::errc{} || parsed.ptr != end || fps <= 0)
      return Clock::duration::zero();
    return std::chrono::duration_cast<Clock::duration>(std::chrono::duration<double>(1.0 / fps));
  }();
  if (interval == Clock::duration::zero())
    return;
  static thread_local Clock::time_point deadline;
  const auto now = Clock::now();
  if (now >= deadline) {
    deadline = now + interval;
    banjo::profiler::RecordLimiterWait(0.0);
    return;
  }
  std::this_thread::sleep_until(deadline);
  deadline += interval;
  banjo::profiler::RecordLimiterWait(
      std::chrono::duration<double, std::milli>(Clock::now() - now).count());
}

REXCVAR_DEFINE_BOOL(afro_60fps_timing, false, "Afro Samurai/Performance",
                    "Scale fixed 30 Hz game steps to the measured update cadence up to 60 Hz")
    .lifecycle(rex::cvar::Lifecycle::kInitOnly);

namespace {
constexpr float kOriginalStep = 1.0f / 30.0f;
constexpr float kMinimumStep = 1.0f / 60.0f;
constexpr auto kMinimumInterval = std::chrono::nanoseconds(16'666'667);
std::atomic<float> g_afro_frame_step{kOriginalStep};
}

void AfroScaleSimulationStep(PPCRegister& step) {
  if (!REXCVAR_GET(afro_60fps_timing))
    return;

  using Clock = std::chrono::steady_clock;
  auto now = Clock::now();
  static auto previous = now - std::chrono::milliseconds(34);
  static std::array<float, 4> intervals{kOriginalStep, kOriginalStep, kOriginalStep, kOriginalStep};
  static unsigned interval_index = 0;
  const auto next_update = previous + kMinimumInterval;
  if (now < next_update) {
    std::this_thread::sleep_until(next_update);
    now = Clock::now();
  }
  const float elapsed = std::chrono::duration<float>(now - previous).count();
  previous = now;

  // Smooth scheduling jitter but discard the elapsed gap after loading or a stall.
  if (elapsed > 0.25f)
    intervals.fill(kOriginalStep);
  else
    intervals[interval_index++ % intervals.size()] = elapsed;
  const float average = (intervals[0] + intervals[1] + intervals[2] + intervals[3]) / intervals.size();
  const float frame_step = std::clamp(average, kMinimumStep, kOriginalStep);
  g_afro_frame_step.store(frame_step, std::memory_order_relaxed);
  // Multiply the game's existing step to preserve Focus and other time scales.
  if (frame_step < kOriginalStep)
    step.f64 = static_cast<float>(step.f64) * (frame_step / kOriginalStep);
}

void AfroUseFrameStep(PPCRegister& step) {
  if (REXCVAR_GET(afro_60fps_timing))
    step.f64 = g_afro_frame_step.load(std::memory_order_relaxed);
}

// banjo-nx's PM4 renderer's D3D-level fast paths (me/banjo_d3d_clear.h, me/banjo_d3d_native.h, defined there because
// banjo_me_hooks.cpp includes them): its hooks are N&B's, so off here (masseffect_renderer_native stays false anyway).
REXCVAR_DEFINE_BOOL(banjo_d3d_api_clear, false, "Afro Samurai/Not built", "banjo-nx's PM4 renderer: Clear markers (not in this port)")
    .lifecycle(rex::cvar::Lifecycle::kInitOnly);
REXCVAR_DEFINE_BOOL(banjo_d3d_api_resolve, false, "Afro Samurai/Not built", "banjo-nx's PM4 renderer: Resolve markers (not in this port)")
    .lifecycle(rex::cvar::Lifecycle::kInitOnly);
REXCVAR_DEFINE_BOOL(banjo_d3d_native_draw_indexed, false, "Afro Samurai/Not built", "banjo-nx's PM4 renderer: native DrawIndexed (not in this port)")
    .lifecycle(rex::cvar::Lifecycle::kInitOnly);
REXCVAR_DEFINE_BOOL(banjo_d3d_native_draw_vertices, false, "Afro Samurai/Not built", "banjo-nx's PM4 renderer: native DrawVertices (not in this port)")
    .lifecycle(rex::cvar::Lifecycle::kInitOnly);

// Game frames presented (banjo-nx counted them in banjo_me_hooks.cpp's Swap hook): Renut's Present hook counts them
// here (d3d/hooks/draw.cpp); the captures' video waits on it.
std::atomic<uint64_t> g_banjo_game_frames{0};


// g_banjo_store_cards (whether the generated code marks the store cards) is cpu/banjo_hot_guest.cpp's again.

// renut_engine/cvar_menu.cpp's toml writer (N&B's in-game settings menu, not built): the keyboard controls dialog
// calls it after a rebind. Not written here: the toml a test or the user wrote stays as it is.
void RenutSaveConfig() {}

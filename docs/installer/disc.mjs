const SECTOR = 2048;
const DESCRIPTOR = 32 * SECTOR;
const MAGIC = "MICROSOFT*XBOX*MEDIA";
const BASES = [0, 0x0FD90000, 0x02080000, 0x18300000];
const TITLE = 0x4e4d07d8;
const MEDIA = 0x4efd55c4;

async function windowOf(iso, offset, length) {
  if (offset < 0 || length < 0 || offset + length > iso.size) {
    throw new Error("The disc image is incomplete or has invalid file offsets.");
  }
  return new DataView(await iso.slice(offset, offset + length).arrayBuffer());
}

function hasMagic(bytes, offset) {
  for (let i = 0; i < MAGIC.length; i++) {
    if (bytes.getUint8(offset + i) !== MAGIC.charCodeAt(i)) return false;
  }
  return true;
}

async function locate(iso) {
  for (const base of BASES) {
    if (base + DESCRIPTOR + SECTOR <= iso.size) {
      const descriptor = await windowOf(iso, base + DESCRIPTOR, SECTOR);
      if (hasMagic(descriptor, 0)) return { base, descriptor };
    }
  }
  const end = Math.min(iso.size, 2 ** 30);
  const step = 8 * 2 ** 20;
  for (let start = DESCRIPTOR; start + SECTOR <= end; start += step) {
    const chunk = await windowOf(iso, start, Math.min(step, end - start));
    for (let i = 0; i + SECTOR <= chunk.byteLength; i += SECTOR) {
      if (hasMagic(chunk, i)) {
        const descriptor = new DataView(chunk.buffer, i, SECTOR);
        if (hasMagic(descriptor, 0x7ec)) return { base: start + i - DESCRIPTOR, descriptor };
      }
    }
  }
  throw new Error("No Xbox disc filesystem found. Select an uncompressed Xbox 360 ISO.");
}

function nameOf(table, offset, length) {
  if (!length || offset + length > table.byteLength) {
    throw new Error("An entry in the disc directory is damaged.");
  }
  const name = String.fromCharCode(...new Uint8Array(table.buffer, table.byteOffset + offset, length));
  if (/[<>:"/\\|?*\x00-\x1f\x7f]/.test(name) || /[. ]$/.test(name) ||
      /^(con|prn|aux|nul|com[1-9¹²³]|lpt[1-9¹²³])(?:\.|$)/i.test(name)) {
    throw new Error("The disc image contains a filename that cannot be safely extracted.");
  }
  return name;
}

async function readDirectories(iso, base, descriptor) {
  const entries = [];
  const paths = new Set();
  const tables = new Set();
  const pending = [{
    offset: base + descriptor.getUint32(0x14, true) * SECTOR,
    size: descriptor.getUint32(0x18, true),
    path: "",
    depth: 0,
  }];
  while (pending.length) {
    const { offset, size, path, depth } = pending.pop();
    if (size === 0) continue;
    if (size > 32 * 2 ** 20 || depth > 64 || tables.has(offset)) {
      throw new Error("The disc directory contains invalid or circular references.");
    }
    tables.add(offset);
    const table = await windowOf(iso, offset, size);
    const nodes = [0];
    const seen = new Set();
    while (nodes.length) {
      const at = nodes.pop();
      if (seen.has(at) || at + 14 > size) {
        throw new Error("The disc directory table is damaged.");
      }
      seen.add(at);
      for (const index of [table.getUint16(at, true), table.getUint16(at + 2, true)]) {
        if (index !== 0 && index !== 0xffff) nodes.push(index * 4);
      }
      const name = nameOf(table, at + 14, table.getUint8(at + 13));
      const entry = {
        path: path ? `${path}/${name}` : name,
        offset: base + table.getUint32(at + 4, true) * SECTOR,
        size: table.getUint32(at + 8, true),
        directory: Boolean(table.getUint8(at + 12) & 0x10),
      };
      const normalized = entry.path.toLowerCase();
      if (paths.has(normalized) || entries.length >= 65534) {
        throw new Error("The disc image contains duplicate file names or too many entries.");
      }
      paths.add(normalized);
      if (entry.size && (entry.offset < base || entry.offset + entry.size > iso.size)) {
        throw new Error("A disc entry points outside the image. Check whether the ISO is complete.");
      }
      entries.push(entry);
      if (entry.directory) pending.push({ ...entry, depth: depth + 1 });
    }
  }
  return entries;
}

async function verifyExecutable(iso, entry) {
  if (!entry || entry.size < 24) throw new Error("The disc image is missing default.xex.");
  const xex = iso.slice(entry.offset, entry.offset + entry.size);
  const header = await windowOf(xex, 0, 24);
  const count = header.getUint32(20);
  if (header.getUint32(0) !== 0x58455832 || count > 1024) {
    throw new Error("The disc executable has an invalid Xbox 360 header.");
  }
  const optional = await windowOf(xex, 24, count * 8);
  for (let i = 0; i < count; i++) {
    if (optional.getUint32(i * 8) !== 0x00040006) continue;
    const info = await windowOf(xex, optional.getUint32(i * 8 + 4), 16);
    if (info.getUint32(12) !== TITLE) throw new Error("This disc is for a different game.");
    if (info.getUint32(0) !== MEDIA) throw new Error("This preview expects the tested European Afro Samurai disc.");
    return;
  }
  throw new Error("The disc executable is missing Xbox 360 title information.");
}

export async function readDisc(iso) {
  const { base, descriptor } = await locate(iso);
  const entries = await readDirectories(iso, base, descriptor);
  await verifyExecutable(iso, entries.find((entry) =>
    !entry.directory && entry.path.toLowerCase() === "default.xex"));
  let bytes = 0;
  let files = 0;
  for (const entry of entries) {
    if (!entry.directory) {
      bytes += entry.size;
      files++;
    }
  }
  return { entries, bytes, files };
}

const MAX32 = 0xffffffff;
const FLAGS = 0x0808;
const DOS_DATE = 0x0021;
const PREFIX = "switch/AFRO-nx/";
const encoder = new TextEncoder();
const crcTable = Uint32Array.from({ length: 256 }, (_, byte) => {
  for (let bit = 0; bit < 8; bit++) byte = (byte >>> 1) ^ ((byte & 1) ? 0xedb88320 : 0);
  return byte;
});

function record(size, signature) {
  const data = new DataView(new ArrayBuffer(size));
  data.setUint32(0, signature, true);
  return data;
}

function localHeader(name, flags) {
  const data = record(30, 0x04034b50);
  data.setUint16(4, 20, true);
  data.setUint16(6, flags, true);
  data.setUint16(12, DOS_DATE, true);
  data.setUint16(26, name.length, true);
  return data;
}

function descriptor(crc, size) {
  const data = record(16, 0x08074b50);
  data.setUint32(4, crc, true);
  data.setUint32(8, size, true);
  data.setUint32(12, size, true);
  return data;
}

function centralHeader(entry) {
  const { name, directory, offset, crc, size, flags } = entry;
  const data = record(46, 0x02014b50);
  data.setUint16(4, 20, true);
  data.setUint16(6, 20, true);
  data.setUint16(8, flags, true);
  data.setUint16(14, DOS_DATE, true);
  data.setUint32(16, crc, true);
  data.setUint32(20, size, true);
  data.setUint32(24, size, true);
  data.setUint16(28, name.length, true);
  data.setUint32(38, directory ? 0x10 : 0, true);
  data.setUint32(42, offset, true);
  return data;
}

export async function writeGameZip(iso, manifest, sink, signal, report = () => {}, runtime = []) {
  const files = [
    ...runtime.map(({ path, bytes }) => ({ path, offset: 0, size: bytes.length, source: new Blob([bytes]) })),
    ...manifest.entries.map((entry) => ({ ...entry, path: "game_root/" + entry.path, source: iso })),
  ];
  const members = files.map((entry) => ({
    ...entry,
    name: encoder.encode(PREFIX + entry.path + (entry.directory ? "/" : "")),
    flags: entry.directory ? 0x0800 : FLAGS,
  }));
  const overhead = members.reduce((total, entry) =>
    total + 76 + 2 * entry.name.length + (entry.directory ? 0 : 16), 22);
  const total = manifest.bytes + runtime.reduce((size, file) => size + file.bytes.length, 0);
  if (total + overhead >= MAX32) {
    throw new Error("The extracted files are too large for this ZIP format.");
  }
  let position = 0;
  let written = 0;
  async function append(value) {
    signal.throwIfAborted();
    await sink.write(value);
    position += value.byteLength;
  }
  const central = [];
  for (const entry of members) {
    const source = entry.source;
    const offset = position;
    const { directory, flags, name } = entry;
    const size = directory ? 0 : entry.size;
    await append(localHeader(name, flags));
    await append(name);
    let crc = 0xffffffff;
    if (!directory) {
      for (let start = 0; start < size; start += 2 ** 20) {
        signal.throwIfAborted();
        const block = new Uint8Array(await source.slice(
          entry.offset + start, entry.offset + Math.min(start + 2 ** 20, size),
        ).arrayBuffer());
        for (const byte of block) crc = (crc >>> 8) ^ crcTable[(crc ^ byte) & 255];
        await append(block);
        written += block.byteLength;
        report(written, total);
      }
      await append(descriptor((crc ^ 0xffffffff) >>> 0, size));
    }
    central.push({ name, directory, flags, offset, size, crc: (crc ^ 0xffffffff) >>> 0 });
  }
  const start = position;
  for (const entry of central) {
    await append(centralHeader(entry));
    await append(entry.name);
  }
  const end = record(22, 0x06054b50);
  end.setUint16(8, central.length, true);
  end.setUint16(10, central.length, true);
  end.setUint32(12, position - start, true);
  end.setUint32(16, start, true);
  await append(end);
}

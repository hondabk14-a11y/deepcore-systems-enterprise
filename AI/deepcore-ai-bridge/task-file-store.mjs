import fs from 'node:fs';
import path from 'node:path';
import { createHash, randomUUID } from 'node:crypto';

const checksum = (payload) => createHash('sha256').update(payload).digest('hex');
const MAX_BYTES = 8 * 1024 * 1024;

/** Single-writer POSIX local-filesystem store. Directory must be trusted and private. */
export function openTaskFileStore(directory) {
  if (process.platform === 'win32') throw new Error('Task file store requires POSIX');
  if (typeof directory !== 'string' || !path.isAbsolute(directory)) throw new Error('Absolute storage directory required');
  fs.mkdirSync(directory, { mode: 0o700, recursive: true });
  const dir = fs.lstatSync(directory);
  if (!dir.isDirectory() || dir.isSymbolicLink() || (dir.mode & 0o077) !== 0 || dir.uid !== process.getuid()) throw new Error('Task storage directory must be private and owned by this user');
  const filename = path.join(directory, 'tasks.json');
  const lock = path.join(directory, '.writer-lock');
  try { fs.mkdirSync(lock, { mode: 0o700 }); } catch { throw new Error('Task store locked; verify writer shutdown before manual recovery'); }
  let closed = false;
  let failed = false;
  let loaded = false;
  const healthy = () => { if (closed || failed) throw new Error('Task store unavailable'); };
  const syncDirectory = () => {
    const fd = fs.openSync(directory, fs.constants.O_RDONLY | fs.constants.O_DIRECTORY);
    try { fs.fsyncSync(fd); } finally { fs.closeSync(fd); }
  };
  return Object.freeze({
    load() {
      healthy();
      if (loaded) throw new Error('Task store already attached');
      loaded = true;
      let fd;
      try {
        try { fd = fs.openSync(filename, fs.constants.O_RDONLY | fs.constants.O_NOFOLLOW); }
        catch (e) { if (e.code === 'ENOENT') return []; throw e; }
        const stat = fs.fstatSync(fd);
        if (!stat.isFile() || stat.size > MAX_BYTES || (stat.mode & 0o077) !== 0 || stat.uid !== process.getuid()) throw new Error('Invalid snapshot file');
        const data = JSON.parse(fs.readFileSync(fd, 'utf8'));
        if (data.version !== 1 || typeof data.payload !== 'string' || checksum(data.payload) !== data.checksum || Object.keys(data).sort().join() !== 'checksum,payload,version') throw new Error('Invalid snapshot');
        const tasks = JSON.parse(data.payload);
        if (!Array.isArray(tasks)) throw new Error('Invalid snapshot');
        return tasks;
      } catch {
        failed = true;
        throw new Error('Task snapshot unreadable or corrupt; recovery required');
      } finally { if (fd !== undefined) fs.closeSync(fd); }
    },
    save(tasks) {
      healthy();
      if (!loaded) throw new Error('Load task store before saving');
      const temporary = path.join(directory, `.tasks-${randomUUID()}.tmp`);
      let fd;
      try {
        const payload = JSON.stringify(tasks);
        const data = JSON.stringify({ version: 1, checksum: checksum(payload), payload });
        if (Buffer.byteLength(data) > MAX_BYTES) throw new Error('Snapshot too large');
        fd = fs.openSync(temporary, 'wx', 0o600);
        fs.writeFileSync(fd, data);
        fs.fsyncSync(fd);
        fs.closeSync(fd);
        fd = undefined;
        fs.renameSync(temporary, filename);
        syncDirectory();
      } catch {
        failed = true;
        throw new Error('Task snapshot write failed; reopen and inspect storage');
      } finally {
        if (fd !== undefined) fs.closeSync(fd);
        try { fs.unlinkSync(temporary); } catch (e) { if (e.code !== 'ENOENT') failed = true; }
      }
    },
    close() {
      if (closed) return;
      closed = true;
      fs.rmdirSync(lock);
    },
  });
}

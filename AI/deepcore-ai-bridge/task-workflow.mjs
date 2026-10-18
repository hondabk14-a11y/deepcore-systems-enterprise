import { createHash } from 'node:crypto';

const digest = (value) => createHash('sha256').update(value).digest('hex');
const required = (value) => typeof value === 'string' && value.trim().length > 0;
const hash = (value) => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
const event = (task, type) => task.history.push({ sequence: task.history.length + 1, type });
const snapshot = (task) => structuredClone(task);

function validate(tasks) {
  if (!Array.isArray(tasks)) throw new Error('Invalid task snapshot');
  const ids = new Set();
  for (const t of tasks) {
    if (!t || !required(t.id) || !required(t.fileName) || ids.has(t.id) || !hash(t.sourceHash) || !hash(t.instructionsHash)) throw new Error('Invalid task snapshot');
    ids.add(t.id);
    const reviewed = ['awaiting_approval', 'approved', 'rejected'].includes(t.state);
    const decided = ['approved', 'rejected'].includes(t.state);
    const expected = ['submitted'];
    if (t.state !== 'submitted') expected.push('reviewing');
    if (reviewed) expected.push('review_completed');
    if (decided) expected.push(t.state);
    if (t.state === 'failed') {
      if (!['REVIEW_FAILED', 'REVIEW_INTERRUPTED'].includes(t.error)) throw new Error('Invalid task failure');
      expected.push(t.error === 'REVIEW_FAILED' ? 'review_failed' : 'review_interrupted');
    } else if (!['submitted', 'reviewing', 'awaiting_approval', 'approved', 'rejected'].includes(t.state) || 'error' in t) throw new Error('Invalid task state');
    if (!Array.isArray(t.history) || t.history.length !== expected.length || t.history.some((e, i) => !e || e.sequence !== i + 1 || e.type !== expected[i] || Object.keys(e).sort().join() !== 'sequence,type')) throw new Error('Invalid task history');
    if (reviewed ? (!required(t.proposal) || digest(t.proposal) !== t.proposalHash) : ('proposal' in t || 'proposalHash' in t)) throw new Error('Invalid task proposal');
    if (decided) {
      const d = t.decision;
      if (!d || !required(d.actor) || d.approved !== (t.state === 'approved') || d.sourceHash !== t.sourceHash || d.proposalHash !== t.proposalHash || Object.keys(d).sort().join() !== 'actor,approved,proposalHash,sourceHash') throw new Error('Invalid task decision');
    } else if ('decision' in t) throw new Error('Unexpected decision');
    const keys = ['id', 'fileName', 'sourceHash', 'instructionsHash', 'state', 'history', ...(reviewed ? ['proposal', 'proposalHash'] : []), ...(decided ? ['decision'] : []), ...(t.state === 'failed' ? ['error'] : [])];
    if (Object.keys(t).sort().join() !== keys.sort().join()) throw new Error('Unexpected task fields');
  }
}

/** Advisory workflow with an optional synchronous, exclusively owned snapshot store. */
export function createTaskWorkflow({ adapter, store } = {}) {
  if (typeof adapter?.review !== 'function') throw new Error('Review adapter required');
  if (store && (typeof store.load !== 'function' || typeof store.save !== 'function')) throw new Error('Invalid task store');
  let poisoned = false;
  const healthy = () => { if (poisoned) throw new Error('Task storage unavailable; restart required'); };
  const persist = (values) => {
    if (!store) return;
    try {
      const result = store.save(snapshot(values));
      if (result?.then) throw new Error('Store must be synchronous');
    } catch {
      poisoned = true;
      throw new Error('Task storage unavailable; restart required');
    }
  };
  const restored = store ? store.load() : [];
  validate(restored);
  const tasks = new Map(restored.map(t => [t.id, snapshot(t)]));
  let recovered = false;
  for (const t of tasks.values()) {
    if (t.state === 'reviewing') {
      t.state = 'failed';
      t.error = 'REVIEW_INTERRUPTED';
      event(t, 'review_interrupted');
      recovered = true;
    }
  }
  if (recovered) persist([...tasks.values()]);
  const read = (id) => {
    healthy();
    if (!tasks.has(id)) throw new Error('Unknown task');
    return snapshot(tasks.get(id));
  };
  const commit = (task) => {
    healthy();
    const next = new Map(tasks);
    next.set(task.id, task);
    persist([...next.values()]);
    tasks.set(task.id, snapshot(task));
    return snapshot(task);
  };
  return Object.freeze({
    submit({ id, fileName, source, instructions } = {}) {
      healthy();
      if (![id, fileName, source, instructions].every(required)) throw new Error('Invalid task');
      if (tasks.has(id)) throw new Error('Duplicate task');
      const task = { id, fileName, sourceHash: digest(source), instructionsHash: digest(instructions), state: 'submitted', history: [] };
      event(task, 'submitted');
      return commit(task);
    },
    get(id) { return read(id); },
    async review(id, { source, instructions } = {}) {
      const task = read(id);
      if (task.state !== 'submitted') throw new Error('Task is not ready for review');
      if (!required(source) || !required(instructions) || digest(source) !== task.sourceHash || digest(instructions) !== task.instructionsHash) throw new Error('Task content changed');
      task.state = 'reviewing';
      event(task, 'reviewing');
      commit(task); // Persist intent before any external request.
      let proposal;
      try {
        proposal = await adapter.review({ fileName: task.fileName, source, instructions });
        if (!required(proposal)) throw new Error('Invalid proposal');
      } catch {
        task.state = 'failed';
        task.error = 'REVIEW_FAILED';
        event(task, 'review_failed');
        return commit(task);
      }
      task.proposal = proposal;
      task.proposalHash = digest(proposal);
      task.state = 'awaiting_approval';
      event(task, 'review_completed');
      return commit(task);
    },
    decide(id, { approved, proposalHash, sourceHash, actor } = {}) {
      const task = read(id);
      if (task.state !== 'awaiting_approval') throw new Error('Task is not awaiting approval');
      if (typeof approved !== 'boolean' || !required(actor)) throw new Error('Invalid decision');
      if (proposalHash !== task.proposalHash || sourceHash !== task.sourceHash) throw new Error('Decision content mismatch');
      task.state = approved ? 'approved' : 'rejected';
      task.decision = { actor, proposalHash, sourceHash, approved };
      event(task, task.state);
      return commit(task);
    },
  });
}

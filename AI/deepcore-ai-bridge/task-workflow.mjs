import { createHash } from 'node:crypto';

const digest = (value) => createHash('sha256').update(value).digest('hex');
const required = (value) => typeof value === 'string' && value.trim().length > 0;

/** In-memory advisory workflow. Not an authorization service or authoritative ledger. */
export function createTaskWorkflow({ adapter } = {}) {
  if (typeof adapter?.review !== 'function') throw new Error('Review adapter required');
  const tasks = new Map();
  const read = (id) => {
    if (!tasks.has(id)) throw new Error('Unknown task');
    return tasks.get(id);
  };
  const event = (task, type) => task.history.push({ sequence: task.history.length + 1, type });
  const snapshot = (task) => structuredClone(task);
  return Object.freeze({
    submit({ id, fileName, source, instructions } = {}) {
      if (![id, fileName, source, instructions].every(required)) throw new Error('Invalid task');
      if (tasks.has(id)) throw new Error('Duplicate task');
      const task = { id, fileName, sourceHash: digest(source), instructionsHash: digest(instructions), state: 'submitted', history: [] };
      event(task, 'submitted');
      tasks.set(id, task);
      return snapshot(task);
    },
    get(id) { return snapshot(read(id)); },
    async review(id, { source, instructions } = {}) {
      const task = read(id);
      if (task.state !== 'submitted') throw new Error('Task is not ready for review');
      if (!required(source) || !required(instructions) || digest(source) !== task.sourceHash || digest(instructions) !== task.instructionsHash) throw new Error('Task content changed');
      task.state = 'reviewing';
      event(task, 'reviewing');
      try {
        const proposal = await adapter.review({ fileName: task.fileName, source, instructions });
        if (!required(proposal)) throw new Error('Invalid proposal');
        task.proposal = proposal;
        task.proposalHash = digest(proposal);
        task.state = 'awaiting_approval';
        event(task, 'review_completed');
      } catch {
        task.state = 'failed';
        task.error = 'REVIEW_FAILED';
        event(task, 'review_failed');
      }
      return snapshot(task);
    },
    decide(id, { approved, proposalHash, sourceHash, actor } = {}) {
      const task = read(id);
      if (task.state !== 'awaiting_approval') throw new Error('Task is not awaiting approval');
      if (typeof approved !== 'boolean' || !required(actor)) throw new Error('Invalid decision');
      if (proposalHash !== task.proposalHash || sourceHash !== task.sourceHash) throw new Error('Decision content mismatch');
      task.state = approved ? 'approved' : 'rejected';
      task.decision = { actor, proposalHash, sourceHash, approved };
      event(task, task.state);
      return snapshot(task);
    },
  });
}

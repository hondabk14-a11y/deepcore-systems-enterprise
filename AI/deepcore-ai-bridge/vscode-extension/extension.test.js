const test = require('node:test');
const assert = require('node:assert/strict');
const Module = require('node:module');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

function fixture() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'deepcore-vscode-'));
  const script = path.join(root, 'AI', 'deepcore-ai-bridge', 'src', 'deepcore-ai-bridge.mjs');
  fs.mkdirSync(path.dirname(script), { recursive: true });
  fs.writeFileSync(script, '');
  let command;
  const executed = [];
  const errors = [];
  const warnings = [];
  const vscode = {
    workspace: { workspaceFolders: [{ uri: { fsPath: root } }] },
    commands: {
      registerCommand: (_id, action) => {
        command = action;
        return { dispose() {} };
      }
    },
    window: {
      activeTextEditor: { document: { uri: { scheme: 'file', fsPath: path.join(root, 'example.py') } } },
      showWarningMessage: value => warnings.push(value),
      showErrorMessage: value => errors.push(value)
    },
    TaskScope: { Workspace: 2 },
    Task: class {
      constructor(definition, scope, name, source, execution) {
        Object.assign(this, { definition, scope, name, source, execution });
      }
    },
    ProcessExecution: class {
      constructor(process, args, options) {
        Object.assign(this, { process, args, options });
      }
    },
    tasks: { executeTask: async task => { executed.push(task); } }
  };

  const originalLoad = Module._load;
  delete require.cache[require.resolve('./extension.js')];
  try {
    Module._load = function (request, parent, isMain) {
      if (request === 'vscode') return vscode;
      return originalLoad.apply(this, arguments);
    };
    require('./extension.js').activate({ subscriptions: [] });
  } finally {
    Module._load = originalLoad;
  }
  return {
    root, script, vscode, executed, errors, warnings,
    execute: () => command(),
    cleanup: () => {
      delete require.cache[require.resolve('./extension.js')];
      fs.rmSync(root, { recursive: true, force: true });
    }
  };
}

test('launches the exact filename as an argument without a shell', async t => {
  const f = fixture();
  t.after(f.cleanup);
  const filename = path.join(f.root, 'weird $(touch injected) ; name.py');
  f.vscode.window.activeTextEditor.document.uri.fsPath = filename;
  await f.execute();
  assert.equal(f.executed.length, 1);
  const task = f.executed[0];
  assert.equal(task.execution.process, 'node');
  assert.deepEqual(task.execution.args, [f.script, filename]);
  assert.equal(task.execution.options.cwd, path.dirname(path.dirname(f.script)));
  assert.equal(task.definition.file, filename);
});

test('does not execute when no editor is active', async t => {
  const f = fixture();
  t.after(f.cleanup);
  f.vscode.window.activeTextEditor = null;
  await f.execute();
  assert.equal(f.executed.length, 0);
  assert.equal(f.warnings.length, 1);
});

test('rejects non-file documents before starting a process', async t => {
  const f = fixture();
  t.after(f.cleanup);
  f.vscode.window.activeTextEditor.document.uri.scheme = 'untitled';
  await f.execute();
  assert.equal(f.executed.length, 0);
  assert.equal(f.warnings.length, 1);
});

test('reports when the bridge script is unavailable', async t => {
  const f = fixture();
  t.after(f.cleanup);
  fs.unlinkSync(f.script);
  await f.execute();
  assert.equal(f.executed.length, 0);
  assert.equal(f.errors.length, 1);
});

test('reports process-start failures', async t => {
  const f = fixture();
  t.after(f.cleanup);
  f.vscode.tasks.executeTask = async () => { throw new Error('runner unavailable'); };
  await f.execute();
  assert.equal(f.errors.length, 1);
  assert.match(f.errors[0], /runner unavailable/);
});

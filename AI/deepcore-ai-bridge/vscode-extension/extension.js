const vscode = require('vscode');
const fs = require('fs');
const path = require('path');

function findBridgeScript() {
  const folders = vscode.workspace.workspaceFolders || [];
  for (const folder of folders) {
    const candidate = path.join(
      folder.uri.fsPath,
      'AI',
      'deepcore-ai-bridge',
      'src',
      'deepcore-ai-bridge.mjs'
    );
    if (fs.existsSync(candidate)) {
      return candidate;
    }
  }
  return null;
}

function activate(context) {
  const command = vscode.commands.registerCommand('deepcore.reviewFile', async () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
      vscode.window.showWarningMessage('DeepCore: open a file before starting a review.');
      return;
    }
    if (editor.document.uri.scheme !== 'file') {
      vscode.window.showWarningMessage('DeepCore: save the file locally before starting a review.');
      return;
    }

    const script = findBridgeScript();
    if (!script) {
      vscode.window.showErrorMessage(
        'DeepCore: repository bridge not found. Open the DeepCore Systems Enterprise repository as the VS Code workspace.'
      );
      return;
    }

    const filePath = editor.document.uri.fsPath;
    const bridgeRoot = path.dirname(path.dirname(script));
    const task = new vscode.Task(
      { type: 'deepcore-review', file: filePath },
      vscode.TaskScope.Workspace,
      'DeepCore AI Review',
      'deepcore',
      new vscode.ProcessExecution('node', [script, filePath], { cwd: bridgeRoot })
    );
    try {
      await vscode.tasks.executeTask(task);
    } catch (error) {
      vscode.window.showErrorMessage(
        'DeepCore: unable to start review: ' + (error instanceof Error ? error.message : String(error))
      );
    }
  });

  context.subscriptions.push(command);
}

function deactivate() {}

module.exports = { activate, deactivate };

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
  const command = vscode.commands.registerCommand('deepcore.reviewFile', () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
      vscode.window.showWarningMessage('DeepCore: open a file before starting a review.');
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
    const terminal = vscode.window.createTerminal({ name: 'DeepCore AI Review' });
    terminal.show(true);
    terminal.sendText(`node ${JSON.stringify(script)} review ${JSON.stringify(filePath)}`);
  });

  context.subscriptions.push(command);
}

function deactivate() {}

module.exports = { activate, deactivate };

const vscode = require('vscode');
const cp = require('child_process');
const path = require('path');

function activate(context) {
  const command = vscode.commands.registerCommand('deepcore.reviewFile', () => {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
      vscode.window.showWarningMessage('DeepCore: open a file before starting a review.');
      return;
    }

    const filePath = editor.document.uri.fsPath;
    const bridgeDir = path.resolve(context.extensionPath, '..');
    const script = path.join(bridgeDir, 'src', 'deepcore-ai-bridge.mjs');

    const terminal = vscode.window.createTerminal({ name: 'DeepCore AI Review' });
    terminal.show(true);
    terminal.sendText(`node ${JSON.stringify(script)} review ${JSON.stringify(filePath)}`);
  });

  context.subscriptions.push(command);
}

function deactivate() {}

module.exports = { activate, deactivate };

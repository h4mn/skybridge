// release.config.js
// Configuração do Semantic Release para Skybridge
// Formato: [`hash`](url) assunto ([#PR](url)) [`@autor`](url)

module.exports = {
  branches: ['main', '+([0-9])?(.{0,9})?.x'],

  plugins: [
    '@semantic-release/commit-analyzer',
    // CHANGELOG.md é gerado manualmente com runtime/changelog.py
    // Removido @semantic-release/changelog para preservar formato Sky
    [
      '@semantic-release/git',
      {
        assets: ['package.json'],  // Apenas package.json (CHANGELOG é manual)
        message: 'chore(release): ${nextRelease.version} [skip ci]\n\n${nextRelease.notes}'
      }
    ],
    '@semantic-release/github',
  ],
};

// "A disciplina dos changelogs é o respeito ao tempo de quem os lê" – made by Sky

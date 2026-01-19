// release.config.js
// Configuração do Semantic Release para Skybridge
// Formato: [`hash`](url) assunto ([#PR](url)) [`@autor`](url)

module.exports = {
  branches: ['main', '+([0-9])?(.{0,9})?.x'],

  plugins: [
    '@semantic-release/commit-analyzer',
    [
      '@semantic-release/release-notes-generator',
      {
        preset: 'conventionalcommits',
        presetConfig: {
          // Seções em PT-BR com Emojis
          types: [
            { type: 'feat', section: '✨ Novidades' },
            { type: 'fix', section: '🐛 Correções' },
            { type: 'docs', section: '📚 Documentação' },
            { type: 'style', section: '💅 Estilos', hidden: false },
            { type: 'refactor', section: '♻️ Refatoração', hidden: false },
            { type: 'perf', section: '⚡ Performance' },
            { type: 'test', section: '✅ Testes', hidden: false },
            { type: 'build', section: '📦 Build', hidden: false },
            { type: 'ci', section: '👷 CI', hidden: false },
            { type: 'chore', section: '🧹 Tarefas', hidden: false },
            { type: 'revert', section: '⏪ Reverter', hidden: false },
          ],
        },
        writerOpts: {
          // Formato customizado: [`hash`](url) assunto ([#PR](url)) [`@autor`](url)
          commitPartial: `* [\`{{hash}}\`]({{href}}) {{#if scope}}**{{scope}}:** {{/if}}{{subject}} {{#if references}}({{references}}) {{/if}}[\`@{{author}}\`](https://github.com/{{author}})
`,

          // Transformação para pegar o autor do commit
          transform: (commit, context) => {
            // Extrair username do email ou usar padrão
            let author = commit.author?.name || 'h4mn';

            // Se for email, extrair a parte antes do @
            if (author.includes('<')) {
              author = author.match(/<(.+)>/)?.[1]?.split('@')[0] || 'h4mn';
            }

            // Criar link completo do commit
            const repo = 'https://github.com/h4mn/skybridge';
            commit.href = `${repo}/commits/${commit.hash}`;

            return { ...commit, author };
          },
        },
      },
    ],
    [
      '@semantic-release/changelog',
      {
        changelogFile: 'CHANGELOG.md',
        changelogTitle: '# Changelog\n\nTodas as alterações notáveis do Skybridge serão documentadas neste arquivo.\n\nO formato é baseado no [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),\ne este projeto adere ao [Semantic Versioning](https://semver.org/spec/v2.0.0.html).\n',
      }
    ],
    [
      '@semantic-release/git',
      {
        assets: ['CHANGELOG.md', 'package.json'],
        message: 'chore(release): ${nextRelease.version} [skip ci]\n\n${nextRelease.notes}'
      }
    ],
    '@semantic-release/github',
  ],
};

// "A disciplina dos changelogs é o respeito ao tempo de quem os lê" – made by Sky

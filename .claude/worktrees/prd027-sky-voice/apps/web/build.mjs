#!/usr/bin/env node
/**
 * Script de build com auto-install de dependências.
 *
 * Verifica se node_modules existe antes de fazer o build,
 * e executa npm install se necessário.
 */

import { existsSync } from 'fs';
import { execSync } from 'child_process';

const nodeModulesExists = existsSync('node_modules');

if (!nodeModulesExists) {
  console.log('⚠️  node_modules não encontrado. Executando npm install...');
  try {
    execSync('npm install', { stdio: 'inherit' });
    console.log('✅ Dependências instaladas com sucesso!');
  } catch (error) {
    console.error('❌ Falha ao instalar dependências:', error.message);
    process.exit(1);
  }
}

console.log('🔨 Iniciando build...');
try {
  execSync('tsc && vite build', { stdio: 'inherit' });
  console.log('✅ Build concluído com sucesso!');
} catch (error) {
  console.error('❌ Falha no build:', error.message);
  process.exit(1);
}

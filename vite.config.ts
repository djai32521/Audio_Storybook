import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import fs from 'fs';
import path from 'path';
import {defineConfig, loadEnv} from 'vite';

function isPlaceholder(val?: string): boolean {
  if (!val || typeof val !== 'string') return true;
  const t = val.trim();
  if (!t) return true;
  const u = t.toUpperCase();
  return (
    u === 'MY_GEMINI_API_KEY' ||
    u === 'YOUR_GEMINI_API_KEY' ||
    u === 'YOUR_API_KEY' ||
    u === 'GEMINI_API_KEY' ||
    u === 'PLACEHOLDER'
  );
}

export default defineConfig(({mode}) => {
  const env = loadEnv(mode, '.', '');
  let devEnvKey = '';
  try {
    if (fs.existsSync('/app/.dev.env.json')) {
      const devEnv = JSON.parse(fs.readFileSync('/app/.dev.env.json', 'utf-8'));
      devEnvKey = devEnv?.API_KEY || devEnv?.GEMINI_API_KEY || '';
    }
  } catch {
    // Ignore if unreadable
  }
  const candidates = [
    env.API_KEY,
    env.GEMINI_API_KEY,
    process.env.API_KEY,
    process.env.GEMINI_API_KEY,
    devEnvKey,
  ];
  const validKey = candidates.find((k) => !isPlaceholder(k))?.trim() || '';
  return {
    base: './',
    plugins: [react(), tailwindcss()],
    define: {
      'process.env.GEMINI_API_KEY': JSON.stringify(validKey),
      'process.env.API_KEY': JSON.stringify(validKey),
    },
    resolve: {
      alias: {
        '@': path.resolve('.'),
      },
    },
    server: {
      port: 3000,
      host: '0.0.0.0',
      hmr: process.env.DISABLE_HMR !== 'true',
    },
  };
});

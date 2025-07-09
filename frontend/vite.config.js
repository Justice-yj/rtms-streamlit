import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  // ⛔ external 옵션 제거!
  // build: {
  //   rollupOptions: {
  //     external: ['@mui/material'],
  //   },
  // },
});

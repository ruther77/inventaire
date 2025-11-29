import { mergeConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default {
  stories: ['../src/**/*.stories.@(js|jsx|mdx)'],
  addons: ['@storybook/addon-essentials', '@storybook/addon-links', '@storybook/addon-interactions'],
  framework: {
    name: '@storybook/react-vite',
    options: {},
  },
  viteFinal: async (config) =>
    mergeConfig(config, {
      plugins: [react()],
    }),
};

import type { CapacitorConfig } from '@capacitor/cli';

// Development identifier; replace with the verified publisher's identifier before signing.
const config: CapacitorConfig = {
  appId: 'com.rapid8d.app',
  appName: 'Rapid 8D',
  webDir: 'dist',
  server: { androidScheme: 'https' },
};
export default config;

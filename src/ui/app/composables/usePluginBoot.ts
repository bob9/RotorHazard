/**
 * Start-up progress of plugin add-ons that draw a bar above the page (classic-bridge.client.ts):
 * whether the plugin panel lists are still on their way, and how many site-wide loader
 * scripts are still loading. The layout uses it to place such a bar before the page shows.
 */
export const usePluginBoot = () => useState('rh.pluginBoot', () => ({ panelsPending: true, scripts: 0 }))

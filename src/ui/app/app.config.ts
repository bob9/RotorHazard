export default defineAppConfig({
  ui: {
    colors: {
      primary: 'rh',
      neutral: 'zinc'
    },
    button: { slots: { base: 'font-medium' } },
    card: { slots: { root: 'rounded-2xl' } },
    // panels fill the space left below banners and plugin bars, not the full screen height
    dashboardPanel: { slots: { root: 'relative flex flex-col min-w-0 min-h-0 lg:not-last:border-e lg:not-last:border-default shrink-0' } }
  }
})

// Text on a tinted (soft/subtle/outline) background uses a deeper shade than the colour itself, so
// it reads at 4.5:1 or more in light mode (amber or green text on a 10% tint is only about 2:1).
// Class names are written out in full so Tailwind finds them.
const TINT_TEXT = {
  primary: 'text-primary-700 dark:text-primary-300',
  secondary: 'text-secondary-700 dark:text-secondary-300',
  success: 'text-success-800 dark:text-success-300',
  info: 'text-info-700 dark:text-info-300',
  warning: 'text-warning-800 dark:text-warning-300',
  error: 'text-error-700 dark:text-error-300'
} as const
// buttons keep the brand orange; the other colours deepen in light mode only
const BUTTON_TEXT = {
  success: 'text-success-700 dark:text-success',
  info: 'text-info-700 dark:text-info',
  warning: 'text-warning-700 dark:text-warning',
  error: 'text-error-700 dark:text-error'
} as const
type Color = keyof typeof TINT_TEXT

const tinted = (variants: string[], slot?: string) => (Object.keys(TINT_TEXT) as Color[]).flatMap(color =>
  variants.map(variant => ({ color, variant, class: slot ? { [slot]: TINT_TEXT[color] } : TINT_TEXT[color] })))

export default defineAppConfig({
  ui: {
    colors: {
      primary: 'rh',
      neutral: 'zinc'
    },
    button: {
      slots: { base: 'font-medium' },
      compoundVariants: (Object.keys(BUTTON_TEXT) as (keyof typeof BUTTON_TEXT)[]).flatMap(color =>
        ['outline', 'soft', 'subtle', 'ghost', 'link'].map(variant => ({ color, variant, class: BUTTON_TEXT[color] })))
    },
    badge: { compoundVariants: tinted(['soft', 'subtle', 'outline']) },
    alert: { compoundVariants: tinted(['soft', 'subtle', 'outline'], 'root') },
    card: { slots: { root: 'rounded-2xl' } },
    // panels fill the space left below banners and plugin bars, not the full screen height
    dashboardPanel: { slots: { root: 'relative flex flex-col min-w-0 min-h-0 lg:not-last:border-e lg:not-last:border-default shrink-0' } }
  }
})

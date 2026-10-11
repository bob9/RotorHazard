// Copies the generated SPA into the server's 'webapp' folder so the
// RotorHazard server can serve it without Node.js being installed.
import { cpSync, rmSync, existsSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const root = dirname(dirname(fileURLToPath(import.meta.url)))
const src = join(root, '.output', 'public')
const dest = join(root, '..', 'server', 'webapp')

if (!existsSync(join(src, 'index.html'))) {
  console.error('No build output found at', src)
  process.exit(1)
}
rmSync(dest, { recursive: true, force: true })
cpSync(src, dest, { recursive: true })
console.log('Published web app to', dest)

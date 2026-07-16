import { readFile, readdir } from "node:fs/promises"
import path from "node:path"

import { readNavigationPages, storyPathToRoute } from "./docs-navigation.mjs"

const root = process.cwd()
const navigationSource = await readFile(
  path.join(root, ".storybook", "docsNavigation.ts"),
  "utf8",
)
const navigationPages = await readNavigationPages(root)
const navigationPaths = new Set(navigationPages.map((page) => page.path))
const navigationRoutes = new Set(navigationPages.map((page) => storyPathToRoute(page.path)))
const failures = []

const previewSource = await readFile(path.join(root, ".storybook", "preview.ts"), "utf8")
const previewOrderMatch = previewSource.match(/order:\s*\[(.*?)\],\s*\n\s*\},/s)
const navigationTitles = [...navigationSource.matchAll(/title:\s*"([^"]+)"/g)].map(
  (match) => match[1],
)
const previewTitles = previewOrderMatch
  ? [...previewOrderMatch[1].matchAll(/"([^"]+)"/g)].map((match) => match[1])
  : []

if (JSON.stringify(previewTitles) !== JSON.stringify(navigationTitles)) {
  failures.push("Storybook's inline story order does not match the documentation manifest.")
}

if (navigationPages.length === 0) {
  failures.push("The documentation navigation manifest contains no pages.")
}

if (navigationPaths.size !== navigationPages.length) {
  failures.push("The documentation navigation manifest contains duplicate paths.")
}

const pagesDirectory = path.join(root, "pages")
const docsFiles = (await readdir(pagesDirectory, { recursive: true }))
  .filter((file) => file.endsWith(".mdx"))
  .sort()
const sourcePages = new Map()

for (const file of docsFiles) {
  const source = await readFile(path.join(pagesDirectory, file), "utf8")
  const metaMatch = source.match(/<Meta\s+title="([^"]+)"\s*\/>/)
  if (!metaMatch) {
    failures.push(`${file}: missing a single-line <Meta title="Section/Page" /> declaration.`)
    continue
  }

  const storyPath = slugify(metaMatch[1])
  if (sourcePages.has(storyPath)) {
    failures.push(`${file}: duplicate Storybook documentation path ${storyPath}.`)
  }
  sourcePages.set(storyPath, file)

  const nextPrevMatch = source.match(/<NextPrev\s+current="([^"]+)"\s*\/>/)
  if (storyPath !== "overview-introduction" && !nextPrevMatch) {
    failures.push(`${file}: every page except Introduction must include NextPrev.`)
  }
  if (nextPrevMatch && nextPrevMatch[1] !== storyPath) {
    failures.push(`${file}: NextPrev current path does not match ${storyPath}.`)
  }

  if (source.includes("?path=/docs/")) {
    failures.push(`${file}: internal documentation links must use canonical /docs/ routes.`)
  }

  const linkedRoutes = new Set([...source.matchAll(/\/docs\/[a-z0-9][a-z0-9/-]*/g)].map((match) => match[0]))
  for (const route of linkedRoutes) {
    if (!navigationRoutes.has(route)) {
      failures.push(`${file}: internal documentation link is not a canonical route: ${route}.`)
    }
  }
}

for (const page of navigationPages) {
  if (!sourcePages.has(page.path)) {
    failures.push(`Navigation page ${page.path} has no MDX source.`)
  }
}

for (const [storyPath, file] of sourcePages) {
  if (!navigationPaths.has(storyPath)) {
    failures.push(`${file}: page ${storyPath} is missing from the navigation manifest.`)
  }
}

if (process.argv.includes("--built")) {
  const index = JSON.parse(
    await readFile(path.join(root, "storybook-static", "index.json"), "utf8"),
  )
  const builtIds = new Set(Object.keys(index.entries))

  for (const page of navigationPages) {
    const storyId = `${page.path}--docs`
    if (!builtIds.has(storyId)) {
      failures.push(`Built Storybook index is missing ${storyId}.`)
    }

    const routeEntry = path.join(root, "storybook-static", storyPathToRoute(page.path), "index.html")
    try {
      const routeHtml = await readFile(routeEntry, "utf8")
      const baseIndex = routeHtml.indexOf('<base href="/" />')
      const firstRelativeAssetIndex = routeHtml.search(/(?:href|src)="\.\//)

      if (baseIndex === -1 || (firstRelativeAssetIndex !== -1 && baseIndex > firstRelativeAssetIndex)) {
        failures.push(`Built documentation route loads relative assets before its base URL: ${storyPathToRoute(page.path)}.`)
      }
      if (!routeHtml.includes("restoreStorybookRoute")) {
        failures.push(`Built documentation route is missing its Storybook bootstrap: ${storyPathToRoute(page.path)}.`)
      }
    } catch {
      failures.push(`Built documentation route is missing ${storyPathToRoute(page.path)}.`)
    }
  }
}

if (failures.length > 0) {
  for (const failure of failures) {
    console.error(`docs error: ${failure}`)
  }
  process.exitCode = 1
} else {
  console.log(`Documentation checks passed for ${navigationPages.length} pages.`)
}

function slugify(value) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
}

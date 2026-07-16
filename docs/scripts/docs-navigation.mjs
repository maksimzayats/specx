import { readFile } from "node:fs/promises"
import path from "node:path"

const pagePattern = /\{\s*title:\s*"([^"]+)",\s*path:\s*"([^"]+)",?\s*\}/g

export const readNavigationPages = async (root) => {
  const source = await readFile(path.join(root, ".storybook", "docsNavigation.ts"), "utf8")

  return [...source.matchAll(pagePattern)].map((match) => ({
    path: match[2],
    title: match[1],
  }))
}

export const storyPathToRoute = (storyPath) => {
  const sectionSeparator = storyPath.indexOf("-")

  if (sectionSeparator === -1) {
    throw new Error(`Documentation path must include a section: ${storyPath}`)
  }

  return `/docs/${storyPath.slice(0, sectionSeparator)}/${storyPath.slice(sectionSeparator + 1)}/`
}

import { spawn } from "node:child_process"
import { mkdir, readFile, writeFile } from "node:fs/promises"
import path from "node:path"

import { readNavigationPages, storyPathToRoute } from "./docs-navigation.mjs"

const root = process.cwd()
const arguments_ = process.argv.slice(2)
const outputDirectory = findOutputDirectory(arguments_)
const storybook = path.join(root, "node_modules", ".bin", "storybook")
const exitCode = await run(storybook, ["build", "--disable-telemetry", ...arguments_])

if (exitCode !== 0) {
  process.exit(exitCode ?? 1)
}

const outputPath = path.resolve(root, outputDirectory)
const managerEntry = path.join(outputPath, "index.html")
const managerHtml = await readFile(managerEntry, "utf8")
const routedManagerHtml = managerHtml
  .replace('<base href="/" />', "")
  .replace("<head>", '<head>\n    <base href="/" />')
const pages = await readNavigationPages(root)

for (const page of pages) {
  const routeDirectory = path.join(outputPath, storyPathToRoute(page.path))
  await mkdir(routeDirectory, { recursive: true })
  await writeFile(path.join(routeDirectory, "index.html"), routedManagerHtml)
}

console.log(`Generated ${pages.length} canonical documentation routes.`)

function findOutputDirectory(args) {
  const inlineOption = args.find((argument) => argument.startsWith("--output-dir="))
  if (inlineOption) {
    return inlineOption.slice("--output-dir=".length)
  }

  const optionIndex = args.findIndex((argument) => argument === "--output-dir" || argument === "-o")
  if (optionIndex === -1) {
    return "storybook-static"
  }

  const outputDirectory = args[optionIndex + 1]
  if (!outputDirectory || outputDirectory.startsWith("-")) {
    throw new Error("--output-dir requires a directory path")
  }

  return outputDirectory
}

function run(command, args) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, { stdio: "inherit" })
    child.on("error", reject)
    child.on("exit", resolve)
  })
}

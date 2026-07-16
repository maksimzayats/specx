import { addons } from "@storybook/manager-api"

import { init as initThemeAddon } from "./addon-theme"
import { docsHref, docsPages } from "./docsNavigation"

addons.setConfig({
  navSize: 230,
  toolbar: {
    copy: { hidden: true },
    eject: { hidden: true },
    fullscreen: { hidden: true },
    createStory: { hidden: true },
  },
  sidebar: {
    showRoots: true,
    collapsedRoots: [],
  },
})

initThemeAddon()

addons.register("view-mode", (api) => {
  const channel = addons.getChannel()
  const documentationPaths = new Set(docsPages.map((page) => page.path))
  const storybookLinkSelector = 'a[href*="?path=/docs/"]'

  const setViewMode = (mode: "story" | "docs") => {
    document.documentElement.dataset.viewMode = mode
  }

  const showCanonicalDocsUrl = () => {
    const { storyId, viewMode } = api.getUrlState()

    if (viewMode !== "docs" || !storyId?.endsWith("--docs")) {
      return
    }

    const documentationPath = storyId.slice(0, -"--docs".length)
    if (!documentationPaths.has(documentationPath)) {
      return
    }

    const url = new URL(window.location.href)
    url.pathname = docsHref(documentationPath)
    url.searchParams.delete("path")
    window.history.replaceState(window.history.state, "", `${url.pathname}${url.search}${url.hash}`)
  }

  const useCanonicalDocsLinks = () => {
    for (const link of document.querySelectorAll<HTMLAnchorElement>(storybookLinkSelector)) {
      const url = new URL(link.href)
      const storyId = url.searchParams.get("path")?.match(/^\/docs\/(.+)--docs$/)?.[1]

      if (storyId && documentationPaths.has(storyId)) {
        link.href = docsHref(storyId)
        link.dataset.canonicalDocsLink = ""
      }
    }
  }

  const navigationObserver = new MutationObserver(useCanonicalDocsLinks)
  navigationObserver.observe(document.documentElement, { childList: true, subtree: true })
  useCanonicalDocsLinks()

  document.addEventListener(
    "click",
    (event) => {
      if (!(event.target instanceof Element)) {
        return
      }

      const link = event.target.closest<HTMLAnchorElement>("a[data-canonical-docs-link]")
      if (!link || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
        return
      }

      event.preventDefault()
      event.stopImmediatePropagation()
      window.location.assign(link.href)
    },
    { capture: true },
  )

  setViewMode(api.getUrlState().viewMode === "docs" ? "docs" : "story")
  channel.on("docsRendered", () => {
    setViewMode("docs")
    showCanonicalDocsUrl()
  })
  channel.on("storyRendered", () => {
    setViewMode(api.getUrlState().viewMode === "docs" ? "docs" : "story")
  })
})

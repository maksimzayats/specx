import { addons } from "@storybook/manager-api"
import "@fontsource/jetbrains-mono/latin-400.css"
import "@fontsource/jetbrains-mono/latin-600.css"

import { init as initThemeAddon } from "./addon-theme"

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

  const setViewMode = (mode: "story" | "docs") => {
    document.documentElement.dataset.viewMode = mode
  }

  setViewMode(api.getUrlState().viewMode === "docs" ? "docs" : "story")
  channel.on("docsRendered", () => setViewMode("docs"))
  channel.on("storyRendered", () => {
    setViewMode(api.getUrlState().viewMode === "docs" ? "docs" : "story")
  })
})

import { addons, types } from "@storybook/manager-api"
import React from "react"

import { Tool } from "./Tool"
import { THEMES } from "./themes"
import { applyManagerTheme, getThemeStore } from "./themeStore"

export const init = () => {
  const initialTheme = getThemeStore()
  applyManagerTheme(initialTheme)
  addons.setConfig({ theme: THEMES[initialTheme] })

  addons.register("specx-storybook/theme-toggle", (api) => {
    addons.add("specx-storybook/theme-toggle", {
      title: "Theme toggle",
      type: types.TOOL,
      match: ({ viewMode }) => viewMode === "story" || viewMode === "docs",
      render: () => <Tool api={api} />,
    })
  })
}

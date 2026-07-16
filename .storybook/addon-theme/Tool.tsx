import { IconButton } from "@storybook/components"
import { type API, useGlobals } from "@storybook/manager-api"
import React, { memo, useLayoutEffect, useState } from "react"

import type { Theme } from "./constants"
import { THEMES } from "./themes"
import { applyManagerTheme, getThemeStore, setThemeStore } from "./themeStore"

export const Tool = memo(({ api }: { api: API }) => {
  const [, updateGlobals] = useGlobals()
  const [theme, setTheme] = useState<Theme>(getThemeStore())

  const applyTheme = (nextTheme: Theme) => {
    setTheme(nextTheme)
    setThemeStore(nextTheme)
    applyManagerTheme(nextTheme)
    api.setOptions({ theme: THEMES[nextTheme] })
  }

  const toggleTheme = () => {
    const nextTheme = theme === "light" ? "dark" : "light"
    updateGlobals({ theme: nextTheme })
    applyTheme(nextTheme)
  }

  useLayoutEffect(() => {
    applyManagerTheme(theme)
  }, [theme])

  return (
    <IconButton
      active={false}
      aria-label={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
      title={`Switch to ${theme === "light" ? "Dark" : "Light"} Mode`}
      onClick={toggleTheme}
    >
      {theme === "light" ? <LightModeIcon /> : <DarkModeIcon />}
    </IconButton>
  )
})

const LightModeIcon = () => (
  <svg aria-hidden="true" fill="currentColor" viewBox="0 0 24 24" width="16" height="16">
    <path
      clipRule="evenodd"
      fillRule="evenodd"
      d="M12 1a1 1 0 0 1 1 1v1a1 1 0 1 1-2 0V2a1 1 0 0 1 1-1ZM1 12a1 1 0 0 1 1-1h1a1 1 0 1 1 0 2H2a1 1 0 0 1-1-1Zm19 0a1 1 0 0 1 1-1h1a1 1 0 1 1 0 2h-1a1 1 0 0 1-1-1Zm-8 8a1 1 0 0 1 1 1v1a1 1 0 1 1-2 0v-1a1 1 0 0 1 1-1Zm0-12a4 4 0 1 0 0 8 4 4 0 0 0 0-8Zm-6 4a6 6 0 1 1 12 0 6 6 0 0 1-12 0Zm-.364-7.778a1 1 0 1 0-1.414 1.414l.707.707A1 1 0 0 0 6.343 4.93l-.707-.707ZM4.222 18.364a1 1 0 1 0 1.414 1.414l.707-.707a1 1 0 1 0-1.414-1.414l-.707.707ZM17.657 4.929a1 1 0 1 0 1.414 1.414l.707-.707a1 1 0 0 0-1.414-1.414l-.707.707Zm1.414 12.728a1 1 0 1 0-1.414 1.414l.707.707a1 1 0 0 0 1.414-1.414l-.707-.707Z"
    />
  </svg>
)

const DarkModeIcon = () => (
  <svg aria-hidden="true" fill="currentColor" viewBox="0 0 24 24" width="16" height="16">
    <path
      clipRule="evenodd"
      fillRule="evenodd"
      d="M12.784 2.47a1 1 0 0 1 .047.975A8 8 0 0 0 20 15h.057a1 1 0 0 1 .902 1.445A10 10 0 0 1 12 22C6.477 22 2 17.523 2 12c0-5.499 4.438-9.961 9.928-10a1 1 0 0 1 .856.47ZM10.41 4.158a8 8 0 1 0 7.942 12.707C13.613 16.079 10 11.96 10 7c0-.986.143-1.94.41-2.842Z"
    />
  </svg>
)

import { DEFAULT_THEME, type Theme } from "./constants"

const STORAGE_KEY = "specx-storybook-theme"

const getThemeFromUrl = (): Theme | undefined => {
  const globals = new URL(window.location.href).searchParams.get("globals")
  const theme = globals
    ?.split(";")
    .map((pair) => pair.split(":"))
    .find(([key]) => key === "theme")?.[1]

  return theme === "light" || theme === "dark" ? theme : undefined
}

export const setThemeStore = (theme: Theme) => {
  window.localStorage.setItem(STORAGE_KEY, theme)
}

export const getThemeStore = (): Theme => {
  const themeFromUrl = getThemeFromUrl()
  if (themeFromUrl) {
    setThemeStore(themeFromUrl)
    return themeFromUrl
  }

  const storedTheme = window.localStorage.getItem(STORAGE_KEY)
  return storedTheme === "light" || storedTheme === "dark" ? storedTheme : DEFAULT_THEME
}

export const applyManagerTheme = (theme: Theme) => {
  document.documentElement.dataset.theme = theme
  document.documentElement.style.colorScheme = theme
}

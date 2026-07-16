import type { Preview } from "@storybook/react"

import { getThemeStore } from "./addon-theme/themeStore"
import { CustomDocsContainer, WithTheme } from "./components/StorybookApp"
import "./preview.css"

const preview: Preview = {
  parameters: {
    options: {
      storySort: {
        order: ["Overview", ["Introduction", "*"]],
      },
    },
    docs: {
      container: CustomDocsContainer,
      toc: {
        contentsSelector: ".sbdocs-content",
        headingSelector: "h2, h3",
        ignoreSelector: ".sbdocs-subtitle, .specx-card h3",
        title: "",
      },
    },
  },
  decorators: [WithTheme],
  initialGlobals: {
    theme: getThemeStore(),
  },
}

export default preview

import type { Preview } from "@storybook/react"

import "./preview.css"

const preview: Preview = {
  parameters: {
    options: {
      storySort: {
        order: ["Overview", ["Introduction", "*"]],
      },
    },
    docs: {
      toc: {
        contentsSelector: ".sbdocs-content",
        headingSelector: "h2, h3",
        ignoreSelector: ".sbdocs-subtitle, .specx-card h3",
        title: "",
      },
    },
  },
}

export default preview

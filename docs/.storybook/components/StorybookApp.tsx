import { DocsContainer, type DocsContainerProps } from "@storybook/blocks"
import { MDXProvider } from "@mdx-js/react"
import type { Decorator } from "@storybook/react"
import React, { type ComponentPropsWithoutRef, type PropsWithChildren, useLayoutEffect } from "react"

import { DEFAULT_THEME, type Theme } from "../addon-theme/constants"
import { THEMES } from "../addon-theme/themes"
import { CodeBlock } from "./CodeBlock"

type DocsContextWithGlobals = DocsContainerProps & {
  context: DocsContainerProps["context"] & {
    store?: { userGlobals?: { globals?: { theme?: Theme } } }
  }
}

const applyDocumentTheme = (theme: Theme) => {
  document.documentElement.dataset.theme = theme
  document.documentElement.style.colorScheme = theme
}

const DocsAnchor = ({ href, target, ...props }: ComponentPropsWithoutRef<"a">) => (
  <a {...props} href={href} target={href?.startsWith("/docs/") ? "_top" : target} />
)

export const WithTheme: Decorator = (Story, context) => {
  const theme = (context.globals.theme as Theme | undefined) ?? DEFAULT_THEME

  useLayoutEffect(() => applyDocumentTheme(theme), [theme])
  return <Story />
}

export const CustomDocsContainer = ({
  children,
  context,
}: PropsWithChildren<DocsContextWithGlobals>) => {
  const theme = context.store?.userGlobals?.globals?.theme ?? DEFAULT_THEME

  useLayoutEffect(() => applyDocumentTheme(theme), [theme])
  return (
    <MDXProvider components={{ a: DocsAnchor, pre: CodeBlock }}>
      <DocsContainer context={context} theme={THEMES[theme]}>
        {children}
      </DocsContainer>
    </MDXProvider>
  )
}

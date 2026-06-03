import * as React from "react"

const QUERY = "(prefers-color-scheme: dark)"

const subscribe = (onStoreChange: () => void) => {
  const mediaQuery = window.matchMedia(QUERY)
  mediaQuery.addEventListener("change", onStoreChange)

  return () => {
    mediaQuery.removeEventListener("change", onStoreChange)
  }
}

const getSnapshot = () => window.matchMedia(QUERY).matches
const getServerSnapshot = () => false

export const useTheme = () => {
  return React.useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot)
}

export default useTheme

import { type FC } from "react"

export const Layout: FC<{ children: JSX.Element | JSX.Element[] }> = ({ children }) => (
  <div className="size-full !overflow-x-hidden overflow-y-scroll [&>div]:h-full">{children}</div>
)

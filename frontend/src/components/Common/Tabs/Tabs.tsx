import clsx from "clsx"
import { isArray } from "lodash-es"
import { type FC, type ReactElement, useEffect } from "react"

import { useDeepCompareEffect } from "~/hooks"
import { LIGHT_THEME } from "~/styles/themes"

import { type TabItemProps } from "./TabItem"
import { useTabsStore } from "./tabs-store"
import { Tooltip } from "../Tooltip/Tooltip"

type TabItemChild = ReactElement<TabItemProps>

interface TabsProps {
  children: TabItemChild | TabItemChild[]
  forcedActiveTab?: string
  classNames?: string
  fixed?: boolean
}

export const Tabs: FC<TabsProps> = ({ children, forcedActiveTab, classNames, fixed }) => {
  const { activeTab, setActiveTab, tabItems, setTabItems } = useTabsStore()

  useDeepCompareEffect(() => {
    const initState = forcedActiveTab ?? activeTab ?? tabItems?.[0]?.label
    setActiveTab(initState)
  }, [tabItems])

  useEffect(() => {
    const newTabItems = isArray(children) ? children : [children]
    setTabItems(newTabItems.map((child) => child.props))
  }, [children])

  const handleClick = (newActiveTab: string) => {
    setActiveTab(newActiveTab)
  }

  const zIndex: Record<number, string> = tabItems.reduce(
    (accu, _, index) => ({
      ...accu,
      [index]: (tabItems.length - index) * 10,
    }),
    {}
  )

  const left: Record<number, string> = tabItems.reduce(
    (accu, _, index) => ({
      ...accu,
      [index]: `-${index * 8}px`,
    }),
    {}
  )

  const getButtonClasses = (label: string) =>
    clsx(
      "size-full flex flex-1 items-center justify-center p-2 text-gray-700 font-medium rounded-t-[10px] bg-accent dark:bg-base-100 relative border border-base-200",
      {
        "border-b-2 border-b-accent": activeTab === label,
      },
      activeTab === label ? `border-[${LIGHT_THEME.colors?.accent}]` : ""
    )

  return (
    <div className={`w-full ${classNames}`}>
      <div className="fixed  w-full bg-base-100">
        <div className="flex max-h-[40px] w-full border-gray-300 bg-transparent lg:max-h-[50px]">
          {tabItems.map((tabItem: TabItemProps, index) => {
            const { label, showTooltip, hideLabel, icon } = tabItem

            return (
              <Tooltip
                key={label}
                content={showTooltip ? label : ""}
                position="daisytooltip-bottom"
                wrapperClasses="!w-full"
              >
                <button
                  style={{
                    zIndex: activeTab === label ? 1000 : zIndex[index],
                    left: left[index],
                    borderBottom: activeTab === label ? `4px solid $${LIGHT_THEME.colors?.accent}` : undefined,
                  }}
                  className={getButtonClasses(label)}
                  onClick={() => handleClick(label)}
                >
                  {icon ? <span className={hideLabel ? "p-1 [&>svg]:text-xl" : "p-1"}>{icon}</span> : null}
                  {!hideLabel ? label : ""}
                </button>
              </Tooltip>
            )
          })}
        </div>
      </div>
      <div className="h-full !overflow-y-auto lg:mt-[40px]">
        {tabItems.map((tabItem: TabItemProps) => {
          const { label, children } = tabItem

          if (label === activeTab) {
            return (
              <div key={label} className="visible h-full">
                {children}
              </div>
            )
          }

          return (
            <div key={label} className="hidden h-full">
              {children}
            </div>
          )
        })}
      </div>
    </div>
  )
}

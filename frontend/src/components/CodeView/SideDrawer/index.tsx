import { useState } from "react"

import { type ExecutionResult } from "~/api-client"
import { Drawer } from "~/components/Common"
import Icon from "~/components/CustomIcons/Icon"
import { checkStatementIsSelect, getMessageFromExecutionResult } from "~/utils"

const SideDrawer = () => {
  const [executionResult, setExecutionResult] = useState<ExecutionResult | undefined>(undefined)
  const [statement, setStatement] = useState<string>("")
  const [isLoading, setIsLoading] = useState(false)
  const [images, setImages] = useState<Image[]>([])
  const executionMessage = executionResult ? getMessageFromExecutionResult(executionResult) : ""
  const showExecutionWarningBanner = statement.trim() && !checkStatementIsSelect(statement)

  return (
    <Drawer
      isOpen={false}
      side="right"
      contentWrapperClasses="w-full md:max-w-[400px] xl:max-w-[600px]"
      colapsedHeader={(toggle) => {
        return (
          <button
            className="group daisybtn glass daisybtn-md flex w-full justify-center px-csm"
            onClick={() => toggle()}
          >
            <Icon.BiArrowFromRight className="!cursor-pointer !text-fluid-cmd group-hover:!text-neutral" />
          </button>
        )
      }}
      expandedHeader={<h1 className="pb-cmd text-fluid-cmd font-bold">Image Gallery</h1>}
      footer={(toggle) => (
        <div className="flex w-full flex-col justify-center">
          <button
            className="group daisybtn glass daisybtn-md flex w-full justify-center px-csm"
            onClick={() => toggle()}
          >
            <Icon.BiArrowFromLeft className="!cursor-pointer !text-fluid-cmd group-hover:!text-neutral" />
          </button>
        </div>
      )}
    >
      <div className="flex w-screen max-w-full flex-col items-start justify-start p-4 dark:text-gray-300 sm:w-[calc(60vw)] lg:w-[calc(50vw)] 2xl:w-[calc(40vw)]">
        <>
          <div className="mt-4 flex w-full flex-row items-center justify-start">
            <Icon.FaFileImage className="h-auto w-6 align-middle" />
            <h5 className="text-1xl ml-2 align-middle font-bold">Images</h5>
          </div>
          <div className="mt-4 flex w-full flex-col items-start justify-start">
            {isLoading ? (
              <div className="flex w-full flex-col items-center justify-center py-6 pt-10">
                <Icon.BiLoaderAlt className="h-auto w-7 animate-spin opacity-70" />
                <span className="mt-2 font-mono text-sm text-gray-500">{"Loading images..."}</span>
              </div>
            ) : (
              <>
                {images.length > 0 ? (
                  <div className="grid w-full grid-cols-2 gap-4">
                    {images.map((image, index) => (
                      <img key={index} src={image.url} alt={image.description} className="h-auto w-full rounded-lg" />
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500">No images available.</p>
                )}
              </>
            )}
          </div>
        </>
      </div>
    </Drawer>
  )
}

export default SideDrawer

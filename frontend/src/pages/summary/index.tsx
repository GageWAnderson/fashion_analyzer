import React, { useEffect, useState } from "react"
import { type NextPage } from "next"
import { SummaryService } from "~/api-client/services/SummaryService"
import { type WeeklySummaryResponse } from "~/api-client/models/WeeklySummaryResponse"
import { ResponseState } from "~/utils/response"
import { Markdown } from "~/components/CodeView/Markdown"
import Icon from "~/components/CustomIcons/Icon"

const SummaryText: React.FC<{ text: string }> = ({ text }) => {
  return (
    <div className="h-full overflow-y-auto">
      <h1>Summary</h1>
      <Markdown text={text} />
    </div>
  )
}

const Examples: React.FC<{ images: string[] }> = ({ images }) => {
  return (
    <div className="h-full overflow-y-auto">
      <h1>Examples</h1>
      {images.length > 0 ? (
        <div className="grid w-full grid-cols-2 gap-4">
          {images.map((image, index) => (
            <div key={index} className="markdown-image">
              <Markdown text={`![${image}](${image})`} />
            </div>
          ))}
        </div>
      ) : (
        <p className="text-gray-500">No images available.</p>
      )}
    </div>
  )
}

const Summary: NextPage = () => {
  const [responseState, setResponseState] = useState<ResponseState>(ResponseState.LOADING)
  const [summary, setSummary] = useState<WeeklySummaryResponse | null>(null)

  useEffect(() => {
    SummaryService.getWeeklySummaryTextApiV1SummaryWeeklyTextGet()
      .then((summary) => {
        setSummary(summary)
        setResponseState(ResponseState.SUCCESS)
      })
      .catch((error) => {
        console.error(error)
        setResponseState(ResponseState.ERROR)
      })
  }, [])

  if (responseState === ResponseState.LOADING) {
    return (
      <div className="flex w-full flex-col items-center justify-center py-6 pt-10">
        <Icon.BiLoaderAlt className="h-auto w-7 animate-spin opacity-70" />
        <span className="mt-2 font-mono text-sm text-gray-500">{"Loading images..."}</span>
      </div>
    )
  } else if (responseState === ResponseState.ERROR) {
    return (
      <div className="flex w-full flex-col items-center justify-center py-6 pt-10">
        <Icon.BiErrorAlt className="h-auto w-7 opacity-70" />
        <span className="mt-2 font-mono text-sm text-red-500">{"Error loading summary. Please try again later."}</span>
      </div>
    )
  } else {
    return (
      <div className="flex size-full flex-row !overflow-hidden">
        <div className="w-1/2 p-4">
          <SummaryText text={summary?.text ?? ""} />
        </div>
        <div className="w-1/2 p-4">
          <Examples images={summary?.images ?? []} />
        </div>
      </div>
    )
  }
}

export default Summary

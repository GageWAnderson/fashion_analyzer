import FileSaver from "file-saver"
import { useCallback, useEffect, useMemo, useState } from "react"
import { CSVLink } from "react-csv"
import { toast } from "react-hot-toast"
import { useCurrentPng } from "recharts-to-png"
import { type ExecutionResult } from "~/api-client"
import { Markdown } from "~/components/CodeView/Markdown"
import { Tooltip } from "~/components/Common/Tooltip/Tooltip"
import Icon from "~/components/CustomIcons/Icon"
import { env } from "~/env.mjs"
import { useCustomState } from "~/hooks/useCustomState"
import { useQueryStore } from "~/stores"
import { SUPPORTED_SYNTAX_LANGUAGES } from "~/types"
import { checkStatementIsSelect } from "~/utils"
import ResultsView from "./ResultsView"

interface Props {
  language: string
  value: string
  title: string
  messageId: string
  conversationId: string
  defaultHidden?: boolean
}

const SUPPORTED_LANG: string[] = [
  SUPPORTED_SYNTAX_LANGUAGES.SQL,
  SUPPORTED_SYNTAX_LANGUAGES.JSX,
  SUPPORTED_SYNTAX_LANGUAGES.CLINGOV_URL,
  SUPPORTED_SYNTAX_LANGUAGES.PLOTLY,
  SUPPORTED_SYNTAX_LANGUAGES.IMAGEURL,
]

const SUPPORT_EDITING_LANG: string[] = [SUPPORTED_SYNTAX_LANGUAGES.YAML, SUPPORTED_SYNTAX_LANGUAGES.JSON]

const CodeFlipCard = (props: Props) => {
  const { language, value, title, defaultHidden = false, messageId, conversationId } = props
  const queryStore = useQueryStore()
  const [showCode, setShowCode] = useState(!SUPPORTED_LANG.includes(language))
  const [isHidden, setIsHidden] = useState(defaultHidden)
  const [executionResult, setExecutionResult] = useState<ExecutionResult | undefined>(undefined)
  const [isLoading, setIsLoading] = useCustomState(false)
  const [getPng, { ref }] = useCurrentPng()
  const filename = `${title.toLowerCase()}_${messageId}`

  const handleGraphDownload = useCallback(async () => {
    const png = await getPng()
    if (png) {
      FileSaver.saveAs(png, filename)
    }
  }, [getPng, filename])

  const cachedResults = Object.values(queryStore.getQueryCacheAll())
  const resultRows = cachedResults.map((result) => result.resultRow)

  useEffect(() => {
    if (!isHidden && !executionResult && !isLoading) {
      setIsLoading(true)
      if (language === SUPPORTED_SYNTAX_LANGUAGES.SQL) {
        if (value !== "" && checkStatementIsSelect(value)) {
          executeStatement(value)
        }
      } else if (language === SUPPORTED_SYNTAX_LANGUAGES.JSX) {
        fetchGraphData(value)
      } else if (language === SUPPORTED_SYNTAX_LANGUAGES.YAML) {
        setExecutionResult({
          rawResult: [],
        })
        setIsLoading(false)
      } else if (language === SUPPORTED_SYNTAX_LANGUAGES.JSON) {
        setExecutionResult({
          rawResult: [],
        })
        setIsLoading(false)
      } else if (language === SUPPORTED_SYNTAX_LANGUAGES.PLOTLY) {
        setExecutionResult({
          rawResult: [],
        })
        setIsLoading(false)
      } else if (language === SUPPORTED_SYNTAX_LANGUAGES.IMAGEURL) {
        setExecutionResult({
          rawResult: [],
        })
        setIsLoading(false)
      }
    }
  }, [language, value, resultRows, isHidden, isLoading, executionResult])

  const fetchGraphData = async (jsx: string) => {
    const regex = /dataKey="([^"]*)"/g
    const matches = jsx.matchAll(regex)
    const extractedDataKeys = Array.from(matches, (m) => m[1] || "")

    // Retrieve the latest cached result from SQL query that contains all the data keys
    const cachedResult = cachedResults
      .filter((result) => result.conversationId === conversationId)
      .sort((a, b) => b.createdAt - a.createdAt)
      .find((result) => {
        const resultDataKeys = result.resultRow ? Object.keys(result.resultRow) : []
        return extractedDataKeys.every((dataKey) =>
          resultDataKeys.some((resultDataKey) => resultDataKey.toLowerCase() === dataKey.toLowerCase())
        )
      })
    if (cachedResult?.resultRow) {
      executeStatement(cachedResult?.statement)
    } else {
      setIsLoading(false)
    }
  }

  const executeStatement = async (statement: string) => {
    if (!statement) {
      toast.error("Please enter a statement.")
      setIsLoading(false)
      setExecutionResult(undefined)
      return
    }

    try {
      const response = await fetch(
        `${env.NEXT_PUBLIC_API_URL}/sql/execute?statement=${encodeURIComponent(statement)}`,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        }
      )
      const result = (await response.json()) as { [key: string]: any }
      if (result.data) {
        setExecutionResult(result.data)
        queryStore.setQueryCache(statement, result.data.rawResult, messageId, conversationId)
      } else if (!result.data && result.message) {
        setExecutionResult({
          rawResult: [],
          error: result.message,
        })
      }
    } catch (error) {
      console.error(error)
      toast.error("Failed to execute statement")
      setExecutionResult({
        rawResult: [],
        error: "Failed to execute statement",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const ResultIcon = useMemo(() => {
    switch (language) {
      case SUPPORTED_SYNTAX_LANGUAGES.JSX:
        return Icon.BsGraphUp
      case SUPPORTED_SYNTAX_LANGUAGES.SQL:
        return Icon.BsTable
      case SUPPORTED_SYNTAX_LANGUAGES.CLINGOV_URL:
        return Icon.BsTable
      case SUPPORTED_SYNTAX_LANGUAGES.PLOTLY:
        return Icon.BsGraphUp
      case SUPPORTED_SYNTAX_LANGUAGES.IMAGEURL:
        return Icon.BsGraphUp
      case SUPPORTED_SYNTAX_LANGUAGES.YAML:
        return Icon.BiEdit
      case SUPPORTED_SYNTAX_LANGUAGES.JSON:
        return Icon.BiEdit
      default:
        return Icon.BiQuestionMark
    }
  }, [language])

  const ResultTitle = useMemo(() => {
    switch (language) {
      case SUPPORTED_SYNTAX_LANGUAGES.JSX:
        return "Show Graph"
      case SUPPORTED_SYNTAX_LANGUAGES.SQL:
        return "Show Table"
      case SUPPORTED_SYNTAX_LANGUAGES.CLINGOV_URL:
        return "Show Table"
      case SUPPORTED_SYNTAX_LANGUAGES.PLOTLY:
        return "Show Graph"
      case SUPPORTED_SYNTAX_LANGUAGES.IMAGEURL:
        return "Show Image"
      case SUPPORTED_SYNTAX_LANGUAGES.YAML:
        return "Show Editor (Coming soon)"
      case SUPPORTED_SYNTAX_LANGUAGES.JSON:
        return "Show Editor (Coming soon)"
      default:
        return "Show Result"
    }
  }, [language])

  const separator = useMemo(() => {
    const list = ["a", "b"]
    const s = list.toLocaleString()
    const match = s.substring(1, s.length - 1)
    const sep = match.length > 0 ? match : ";"
    return sep
  }, [])

  const hasCSVDownload =
    !isHidden &&
    executionResult?.rawResult &&
    executionResult.rawResult.length > 0 &&
    (language === SUPPORTED_SYNTAX_LANGUAGES.SQL || language === SUPPORTED_SYNTAX_LANGUAGES.CLINGOV_URL)

  const hasGraphDownload =
    !isHidden &&
    executionResult?.rawResult &&
    executionResult.rawResult.length > 0 &&
    language === SUPPORTED_SYNTAX_LANGUAGES.JSX

  // if (executionResult?.error || !executionResult?.rawResult || executionResult.rawResult.length == 0) {
  //     return null;
  // }

  return (
    <div className="relative w-full">
      <div className="relative mx-auto w-11/12 max-w-[1200px]">
        <div className="mb-6 overflow-hidden rounded-xl bg-base-100 px-6 py-4 shadow-sm transition-all hover:shadow-md dark:bg-base-100">
          <div className="mb-3 flex items-center">
            <div className="text-lg font-medium">{title}</div>
            <div className="ml-auto flex items-center gap-2">
              {hasCSVDownload && (
                <CSVLink data={executionResult?.rawResult} filename={filename} separator={separator}>
                  <Tooltip content="Download as CSV" position="daisytooltip-top">
                    <button className="flex size-7 items-center justify-center rounded-lg bg-accent p-1.5 text-white transition-opacity hover:opacity-90">
                      <Icon.AiOutlineDownload className="h-auto w-full" />
                    </button>
                  </Tooltip>
                </CSVLink>
              )}
              {hasGraphDownload && (
                <Tooltip content="Download as PNG" position="daisytooltip-top">
                  <button
                    className="flex size-7 items-center justify-center rounded-lg bg-accent p-1.5 text-white transition-opacity hover:opacity-90"
                    onClick={handleGraphDownload}
                  >
                    <Icon.AiOutlineDownload className="h-auto w-full" />
                  </button>
                </Tooltip>
              )}
              <Tooltip content={isHidden ? "Show" : "Collapse"} position="daisytooltip-top">
                <button
                  className="flex size-7 items-center justify-center rounded-lg bg-accent p-1.5 text-white transition-opacity hover:opacity-90"
                  onClick={() => setIsHidden(!isHidden)}
                >
                  {isHidden ? (
                    <Icon.BiExpandAlt className="h-auto w-full" />
                  ) : (
                    <Icon.BiCollapseAlt className="h-auto w-full" />
                  )}
                </button>
              </Tooltip>
            </div>
          </div>
          {!isHidden &&
            (showCode ? (
              <div className="rounded-xl bg-secondary p-6 dark:bg-secondary">
                <Markdown text={value} messageId={messageId} conversationId={conversationId} />
              </div>
            ) : (
              <ResultsView
                executionResult={executionResult}
                isLoading={isLoading}
                language={language}
                code={value}
                graph_ref={ref}
              />
            ))}
        </div>
      </div>
    </div>
  )
}

export default CodeFlipCard

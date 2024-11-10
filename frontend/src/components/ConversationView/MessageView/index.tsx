import dayjs from "dayjs"
import { motion } from "framer-motion"
import { useSession } from "next-auth/react"
import { useMemo, useState } from "react"

import Avatar from "react-avatar"
import { Collapse } from "react-collapse"
import { toast } from "react-hot-toast"
import { StreamingDataTypeEnum, StreamingSignalsEnum } from "~/api-client"
import { Dropdown, DropdownItem, Tooltip } from "~/components/Common"
import Icon from "~/components/CustomIcons/Icon"

import ToolAppendixRenderer from "~/components/ToolAppendixRenderer"
import { env } from "~/env.mjs"
import { useMessageStore, useUserStore } from "~/stores"
import {
  type Message,
  type MessageEvent as MessageEventT,
  SUPPORTED_SYNTAX_LANGUAGES,
  type ToolAppendixData,
} from "~/types"

import { groupBy } from "~/utils"

import FeedbackView from "./FeedbackView"
import { LLMResponse } from "./MessageEvents/MessageEvent/LLMResponse"
import { MessageEvents } from "./MessageEvents/MessageEvents"
import ThreeDotsLoader from "../../CustomIcons/ThreeDotsLoader"
import { CONVERSATION_VIEW_SELECTORS } from "../ConversationView.selectors"

interface Props {
  message: Message
  isLatestMessage: boolean
  conversationId: string
}

const MessageView = (props: Props) => {
  const { message, isLatestMessage, conversationId } = props
  const userStore = useUserStore()
  const messageStore = useMessageStore()
  const [isActionsCollapsed, setIsActionsCollapsed] = useState(true)
  const isCurrentUser = message.creatorId === userStore.currentUser.id
  const { data: session } = useSession()
  const showFeedback = env.NEXT_PUBLIC_ENABLE_MESSAGE_FEEDBACK

  const copyMessage = () => {
    navigator.clipboard.writeText(message.content)
    toast.success("Copied to clipboard")
  }

  const deleteMessage = (message: Message) => {
    messageStore.clearMessage((item) => item.id !== message.id)
  }

  const getClothingInfoMarkdown = (metadata: Record<string, any>) => {
    return `\n**Name:** ${metadata.name}  \n**Price:** ${metadata.price}  \n**Link:** [${metadata.link}](${metadata.link})  \n![${metadata.name}](${metadata.image_url})`
      .replace("\n", " ")
      .trim()
  }

  const appendixEvents = useMemo(() => {
    const appendixEvents = [] as ToolAppendixData[]

    message.events
      .filter((e) => e.data_type === StreamingDataTypeEnum.APPENDIX && e.data === StreamingSignalsEnum.EXTRACTED_ITEM)
      .forEach(async (event) => {
        try {
          // Only display the item if the image link works on the client side
          const response = await fetch(event.metadata.image_url || "", { method: "HEAD" })
          if (response.ok) {
            appendixEvents.push({
              value: getClothingInfoMarkdown(event.metadata),
              language: SUPPORTED_SYNTAX_LANGUAGES.CLOTHING_INFO,
              title: event.metadata.name || "Clothing Item",
              event: event,
            })
          }
        } catch (error) {
          console.warn(`Failed to verify image URL: ${event.metadata.image_url}`)
        }
      })

    Object.values(SUPPORTED_SYNTAX_LANGUAGES).forEach((language) => {
      const regex = new RegExp("```" + language + "([\\s\\S]*?)```", "g")
      let match
      let idx = 1

      message.events
        .filter((e) => e.data_type === "appendix")
        .forEach((event) => {
          while ((match = regex.exec(event.data)) !== null) {
            appendixEvents.push({
              value: (match[1] as string).replace("\n", " ").trim(),
              language: language,
              title: event.metadata.title || `Appendix ${idx}`,
              event: event,
            })
            idx += 1
          }
        })
    })

    return appendixEvents
  }, [message.events.length])

  const [groupedToolEvents, otherEvents] = useMemo(() => {
    return [
      groupBy(
        message.events.filter((e) => !!e.metadata.tool),
        "metadata.tool"
      ) as { [key: string]: MessageEventT[] },
      message.events.filter((e) => !e.metadata.tool),
    ]
  }, [message.events.length])

  const isRecentMessage = useMemo(() => {
    const minutesBefore = new Date()
    minutesBefore.setMinutes(minutesBefore.getMinutes() - 5)
    return isLatestMessage && dayjs(message.createdAt).isAfter(dayjs(minutesBefore))
  }, [isLatestMessage, message.createdAt])

  return (
    <div
      className={`group mx-auto flex w-full max-w-full flex-row items-start justify-start px-8 py-4 xl:px-16 ${
        isCurrentUser
          ? "bg-gradient-to-r from-blue-50 to-transparent dark:from-blue-900/20"
          : "bg-gradient-to-r from-gray-50 to-transparent dark:from-gray-800/20"
      }`}
      data-cy={CONVERSATION_VIEW_SELECTORS.filledChatMessageAreaWrapper}
    >
      {isCurrentUser ? (
        <>
          <div className="mr-3 flex size-10 shrink-0 items-center justify-center rounded-full shadow-sm [&_span]:!text-neutral">
            {session?.user?.name ? (
              <div data-cy={CONVERSATION_VIEW_SELECTORS.userAvatar} className="size-full">
                <Avatar name={session.user.name.replace("-", " ")} size="40" round={true} />
              </div>
            ) : (
              <Icon.AiOutlineUser className="size-6" />
            )}
          </div>
          <div className="flex w-auto max-w-[calc(100%-2rem)] flex-col items-start justify-start">
            <div className="w-full whitespace-pre-wrap break-all rounded-2xl bg-white/80 px-6 py-3 shadow-sm dark:bg-gray-800/80">
              <p data-cy={CONVERSATION_VIEW_SELECTORS.userMessage}>{message.content}</p>
            </div>
          </div>
          <div className="invisible group-hover:visible">
            <Dropdown
              tigger={
                <button className="ml-2 mt-2 flex size-6 shrink-0 items-center justify-center">
                  <Icon.IoMdMore className="h-auto w-5 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200" />
                </button>
              }
            >
              <div className="flex flex-col items-start justify-start rounded-xl bg-white p-1.5 shadow-lg dark:bg-gray-800">
                <DropdownItem
                  className="flex w-full cursor-pointer flex-row items-center justify-start rounded-lg p-2 hover:bg-blue-50 dark:hover:bg-blue-900/30"
                  onClick={copyMessage}
                >
                  <Icon.BiClipboard className="mr-2 h-auto w-4 opacity-70" />
                  Copy
                </DropdownItem>
                <DropdownItem
                  className="flex w-full cursor-pointer flex-row items-center justify-start rounded-lg p-2 hover:bg-red-50 dark:hover:bg-red-900/30"
                  onClick={() => deleteMessage(message)}
                >
                  <Icon.BiTrash className="mr-2 h-auto w-4 opacity-70" />
                  Delete
                </DropdownItem>
              </div>
            </Dropdown>
          </div>
        </>
      ) : (
        <>
          {message.status === "LOADING" && message.content === "" && message.events.length === 0 ? (
            <div
              className="mt-0.5 w-12 rounded-lg bg-transparent px-4 py-2"
              data-cy={CONVERSATION_VIEW_SELECTORS.stepsLoading}
            >
              <ThreeDotsLoader />
            </div>
          ) : (
            <>
              <div
                className="flex w-full max-w-[calc(100%-2rem)] flex-col items-start justify-start"
                data-cy={CONVERSATION_VIEW_SELECTORS.stepsWrapper}
              >
                <div
                  className={`prose prose-neutral w-full max-w-full rounded-2xl bg-white/90 px-6 py-4 shadow-sm dark:bg-gray-800/90 ${
                    message.status === "FAILED" && "border-2 border-red-400 bg-red-50 text-red-500 dark:bg-red-900/20"
                  }`}
                >
                  <div className="rounded-xl border border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-900/50">
                    <div className="flex items-center justify-start p-2">
                      <div className="ml-2">
                        <Icon.MdListAlt className="h-auto w-6 text-blue-500 dark:text-blue-400" />
                      </div>
                      <div className="ml-2">
                        <span className="text-lg font-medium text-gray-700 dark:text-gray-300">Details</span>
                      </div>
                      {message.status === "LOADING" && (
                        <div className="ml-3" data-cy={CONVERSATION_VIEW_SELECTORS.stepsLoading}>
                          <ThreeDotsLoader />
                        </div>
                      )}
                      <div className="ml-auto">
                        <Tooltip content={isActionsCollapsed ? "Show steps" : "Hide steps"} position="daisytooltip-top">
                          <button
                            className="flex size-8 items-center justify-center rounded-lg bg-blue-100 p-1.5 text-blue-600 transition-colors hover:bg-blue-200 dark:bg-blue-900/50 dark:text-blue-300 dark:hover:bg-blue-800/70"
                            onClick={() => setIsActionsCollapsed(!isActionsCollapsed)}
                          >
                            {isActionsCollapsed ? (
                              <Icon.BiChevronDown className="h-auto w-full" />
                            ) : (
                              <Icon.BiChevronUp className="h-auto w-full" />
                            )}
                          </button>
                        </Tooltip>
                      </div>
                    </div>
                    <Collapse isOpened={!isActionsCollapsed}>
                      <div className="border-t border-gray-200 p-4 dark:border-gray-700">
                        {Object.keys(groupedToolEvents).map((tool) => (
                          <MessageEvents key={tool} events={groupedToolEvents[tool] || []} message={message} />
                        ))}
                      </div>
                    </Collapse>
                  </div>
                  <LLMResponse text={message.content} messageId={message.id} conversationId={conversationId} />
                  {message.status === "DONE" &&
                    showFeedback &&
                    (isRecentMessage ? (
                      <motion.div
                        initial={{ opacity: 0, scale: 0.5 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 0.5 }}
                      >
                        <FeedbackView
                          feedback={message.feedback}
                          conversationId={conversationId}
                          messageId={message.id}
                          user={session?.user.name}
                        />
                      </motion.div>
                    ) : (
                      <FeedbackView
                        feedback={message.feedback}
                        conversationId={conversationId}
                        messageId={message.id}
                        user={session?.user.name}
                      />
                    ))}
                </div>
                {appendixEvents.length > 0 && (
                  <div className="mt-3 flex w-full flex-col items-center justify-start space-y-2">
                    {appendixEvents.map((data, index) => (
                      <ToolAppendixRenderer
                        key={index}
                        data={data}
                        message={message}
                        isLatestMessage={isLatestMessage}
                        conversationId={conversationId}
                      />
                    ))}
                  </div>
                )}
                <span className="self-end pr-2 pt-2 text-sm text-gray-500 dark:text-gray-400">
                  {dayjs(message.createdAt).format("lll")}
                </span>
              </div>
              <div className="invisible group-hover:visible">
                <Dropdown
                  tigger={
                    <button className="ml-2 mt-2 flex size-6 shrink-0 items-center justify-center">
                      <Icon.IoMdMore className="h-auto w-5 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200" />
                    </button>
                  }
                >
                  <div className="flex flex-col items-start justify-start rounded-xl bg-white p-1.5 shadow-lg dark:bg-gray-800">
                    <DropdownItem
                      className="flex w-full cursor-pointer flex-row items-center justify-start rounded-lg p-2 hover:bg-blue-50 dark:hover:bg-blue-900/30"
                      onClick={copyMessage}
                    >
                      <Icon.BiClipboard className="mr-2 h-auto w-4 opacity-70" />
                      Copy
                    </DropdownItem>
                    <DropdownItem
                      className="flex w-full cursor-pointer flex-row items-center justify-start rounded-lg p-2 hover:bg-red-50 dark:hover:bg-red-900/30"
                      onClick={() => deleteMessage(message)}
                    >
                      <Icon.BiTrash className="mr-2 h-auto w-4 opacity-70" />
                      Delete
                    </DropdownItem>
                  </div>
                </Dropdown>
              </div>
            </>
          )}
        </>
      )}
    </div>
  )
}

export default MessageView

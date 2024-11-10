import { useEffect, useRef, useState } from "react"

import { toast } from "react-hot-toast"
import TextareaAutosize from "react-textarea-autosize"

import { ICreatorRole } from "~/api-client"
import Icon from "~/components/CustomIcons/Icon"
import { useConversationStore, useMessageStore, useUserStore } from "~/stores"
import { generateUUID } from "~/utils"

import { CONVERSATION_VIEW_SELECTORS } from "./ConversationView.selectors"

interface Props {
  disabled?: boolean
  sendMessage: () => Promise<void>
}

const MessageTextarea = (props: Props) => {
  const { disabled, sendMessage } = props
  const userStore = useUserStore()
  const conversationStore = useConversationStore()
  const messageStore = useMessageStore()
  const [value, setValue] = useState<string>("")
  const [isInIME, setIsInIME] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.focus()
    }
  }, [])

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setValue(e.target.value)
  }

  const handleSend = async () => {
    let conversation = conversationStore.getConversationById(conversationStore.currentConversationId)
    if (!conversation) {
      conversation = conversationStore.createConversation()
    }
    if (!value) {
      toast.error("Please enter a message.")
      return
    }
    if (disabled) {
      return
    }

    messageStore.addMessage({
      id: generateUUID(),
      conversationId: conversation.id,
      creatorId: userStore.currentUser.id,
      creatorRole: ICreatorRole.USER,
      createdAt: Date.now(),
      content: value,
      events: [],
      status: "DONE",
    })
    setValue("")
    textareaRef.current!.value = ""
    await sendMessage()
  }

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === "Enter" && !event.shiftKey && !isInIME) {
      event.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex h-auto w-full flex-row items-end justify-between rounded-xl border-2 border-base-200 bg-neutral/50 px-3 py-2 shadow-sm">
      <TextareaAutosize
        ref={textareaRef}
        className="hide-scrollbar size-full resize-none border-none bg-transparent p-2 leading-7 outline-none placeholder:text-base-200/70"
        placeholder={"What would you like to ask?"}
        rows={1}
        minRows={1}
        maxRows={5}
        onCompositionStart={() => setIsInIME(true)}
        onCompositionEnd={() => setIsInIME(false)}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        data-cy={CONVERSATION_VIEW_SELECTORS.textInputArea}
      />
      <button
        className="glass ml-1 w-10 cursor-pointer rounded-lg bg-primary/10 p-2 transition-all hover:bg-primary/20 hover:shadow-md disabled:cursor-not-allowed disabled:opacity-50"
        disabled={disabled}
        onClick={handleSend}
        data-cy={CONVERSATION_VIEW_SELECTORS.sendMessageButton}
      >
        <Icon.IoArrowUp className="h-auto w-full text-primary" />
      </button>
    </div>
  )
}

export default MessageTextarea

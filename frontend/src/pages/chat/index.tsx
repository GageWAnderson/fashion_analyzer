import { type NextPage } from "next"
import dynamic from "next/dynamic"

// Use dynamic import to avoid page hydrated.
// reference: https://github.com/pmndrs/zustand/issues/1145#issuecomment-1316431268
const ConversationSidebar = dynamic(() => import("~/components/ConversationSidebar"), {
  ssr: false,
})
const ConversationView = dynamic(() => import("~/components/ConversationView"), {
  ssr: false,
})
const SideDrawer = dynamic(() => import("~/components/CodeView/SideDrawer"), {
  ssr: false,
})

const ChatLanding: NextPage = () => {
  return (
    <div className="border-top flex size-full flex-row !overflow-hidden border-base-200 bg-base-100 pt-2">
      <ConversationSidebar />
      <ConversationView />
      <SideDrawer />
    </div>
  )
}

export default ChatLanding

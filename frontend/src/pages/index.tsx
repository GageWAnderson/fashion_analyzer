import { type NextPage } from "next"
import Head from "next/head"

import { TopWarningBanner } from "~/components/Common"
import { TabItem, Tabs } from "~/components/Common"
import { APPLICATION_TITLE } from "~/utils"
import ChatLanding from "./chat"
import Summary from "./summary"

const Home: NextPage = () => {
  return (
    <>
      <Head>
        <title>{APPLICATION_TITLE}</title>
        <meta name="FashionAgent" content="By Gage Anderson" />
        {/* <link rel="icon" href="/favicon.ico" TODO: Uncomment when you make an icon /> */}
      </Head>
      <main className="flex size-full flex-col bg-neutral dark:bg-base-300">
        <div className="sticky top-0 z-1 flex w-full flex-col items-start justify-start bg-accent dark:bg-accent dark:text-neutral">
          <TopWarningBanner />
        </div>

        <Tabs>
          <TabItem label="Chat">
            <ChatLanding />
          </TabItem>
          <TabItem label="Summary">
            <Summary />
          </TabItem>
        </Tabs>
      </main>
    </>
  )
}

export default Home

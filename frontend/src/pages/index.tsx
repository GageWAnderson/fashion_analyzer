import { type NextPage } from "next"
import Head from "next/head"

import { TabItem, Tabs } from "~/components/Common"
import Header from "~/components/Header/Header"
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
        <Header />
        <Tabs classNames="pb-10 pt-16 h-full">
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

import { CONVERSATION_VIEW_SELECTORS } from "./ConversationView.selectors"

// examples are used to show some examples to the user.
const examples = [
  "What are some women's fall fashion trends?",
  "Look up the hottest clothing from Prada for me",
  "Search for the best affordable men's winter jackets",
]

interface Props {
  className?: string
  sendMessage: () => Promise<void>
}

const EmptyView = (props: Props) => {
  const { className } = props

  return (
    <div
      className={`${className || ""} flex size-full flex-col items-center justify-start text-black dark:text-black`}
      data-cy={CONVERSATION_VIEW_SELECTORS.emptyChatMessageAreaWrapper}
    >
      <div className="mb-12 flex w-96 max-w-full items-center justify-center font-medium leading-loose"></div>
      <div className="group mx-auto flex w-full max-w-full flex-row items-start justify-start rounded-xl bg-base-100 p-6 shadow-sm">
        <div className="mb-4 w-full px-6 py-4">
          <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200">
            Ask me about fashion, style, and the latest trends!
          </h3>
          <div className="mt-4 text-base leading-relaxed text-gray-600 dark:text-gray-400">
            <p className="mb-3">Here are some examples to get you started:</p>
            <ol className="mb-4 list-decimal space-y-2 pl-8">
              {examples.map((example, index) => (
                <li key={index} className="transition-colors duration-200 hover:text-gray-800 dark:hover:text-gray-200">
                  <span>{example}</span>
                </li>
              ))}
            </ol>
          </div>
        </div>
      </div>
    </div>
  )
}

export default EmptyView

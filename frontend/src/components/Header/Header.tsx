import { Modal, SettingsModal } from "~/components/Common"
import Icon from "~/components/CustomIcons/Icon"
import { ThemeSwitch } from "../Common"
import { CONVERSATION_VIEW_SELECTORS } from "../ConversationView/ConversationView.selectors"

const Header = () => {
  const getSettingsModalId = () => "conversation-sidebar-settings-modal"
  return (
    <div
      className="daisynavbar absolute inset-x-0 top-0 z-[1000] items-center justify-center border-b-2 bg-base-100 p-csm dark:border-b-base-100 dark:!bg-base-200"
      data-cy={CONVERSATION_VIEW_SELECTORS.topbarWrapper}
    >
      <div className="absolute !right-csm !top-cmd z-[1000] flex gap-csm">
        <button className="group hover:daisybtn-secondary" onClick={() => Modal.openModal(getSettingsModalId())}>
          <Icon.FiSettings className="!text-fluid-cmd text-base-200 group-hover:!text-neutral dark:!text-neutral" />
        </button>
        <ThemeSwitch />
      </div>

      <h1 className="text-overflow-ellipsis text-fluid-3xl max-w-full overflow-hidden p-1 text-center font-bold">
        Fashion <tspan className="text-accent">Analyzer</tspan>
      </h1>
      {<SettingsModal getSettingsModalId={getSettingsModalId} />}
    </div>
  )
}

export default Header

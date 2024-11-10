import { useEffect, useState } from "react"

import Icon from "~/components/CustomIcons/Icon"

import { useSettingStore } from "~/stores"
import { Modal } from "../Modal/Modal"

interface Props {
  getSettingsModalId: (id?: string) => string
}

export const SettingsModal = (props: Props) => {
  const { getSettingsModalId } = props
  const settingsStore = useSettingStore()
  const [runMode, setRunMode] = useState<string>("")

  useEffect(() => {
    const runMode = localStorage.getItem("runMode")

    if (runMode) {
      setRunMode(runMode)
    }
  }, [])

  const saveSettings = () => {
    localStorage.setItem("runMode", runMode)
    settingsStore.setSetting({
      data: {
        run_mode: runMode,
      },
    })
    Modal.closeModal(modalId)
  }

  const modalId = getSettingsModalId()

  return (
    <Modal.Component
      uniqueModalId={modalId}
      actionButtons={
        <div className="flex w-64 flex-row items-center justify-end gap-csm">
          <button
            className="daisybtn daisybtn-secondary daisybtn-sm  font-normal capitalize lg:daisybtn-md"
            onClick={() => saveSettings()}
          >
            <Icon.FiSave className="mr-1 h-auto w-5" />
            Save
          </button>
          <button
            className="daisybtn glass daisybtn-sm font-normal capitalize lg:daisybtn-md hover:text-neutral"
            onClick={() => Modal.closeModal(modalId)}
          >
            <Icon.FiX className="mr-1 h-auto w-5" />
            Cancel
          </button>
        </div>
      }
    >
      <div className="flex flex-col items-center justify-center rounded-lg bg-transparent px-cmd py-cxl dark:bg-base-100">
        <h3 className="m-0 p-0 !text-fluid-cmd font-bold">Settings</h3>
        <div className="daisydivider" />
        <div className="flex size-full flex-col gap-cmd">
          <div className="flex flex-row items-center justify-between">
            <span className="text-xl font-medium">Run Mode</span>
            <label className="relative inline-flex cursor-pointer items-center">
              <input
                type="checkbox"
                className="peer sr-only"
                checked={runMode === "openai"}
                onChange={() => setRunMode(runMode === "openai" ? "local" : "openai")}
              />
              <div className="peer h-10 w-16 rounded-full bg-gray-200 after:absolute after:left-c3xs after:top-c3xs after:size-9 after:rounded-full after:border after:border-gray-300 after:bg-white after:transition-all after:content-[''] peer-checked:bg-accent peer-checked:after:translate-x-full peer-checked:after:border-white peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-accent/50 dark:bg-gray-700 dark:peer-focus:ring-accent/50"></div>
              <span className="ml-3 text-xl font-medium text-gray-900 dark:text-gray-300">
                {runMode === "openai" ? "OpenAI" : "Local"}
              </span>
            </label>
          </div>
        </div>
      </div>
    </Modal.Component>
  )
}

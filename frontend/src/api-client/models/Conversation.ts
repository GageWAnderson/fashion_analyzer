/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { ChatMessage } from "./ChatMessage"
import type { UserSettings } from "./UserSettings"

export type Conversation = {
  messages: Array<ChatMessage>
  conversationId: string
  newMessageId: string
  userEmail: string
  settings: UserSettings | null
}

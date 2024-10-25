/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Conversation } from "../models/Conversation"

import type { CancelablePromise } from "../core/CancelablePromise"
import { OpenAPI } from "../core/OpenAPI"
import { request as __request } from "../core/request"

export class ChatService {
  /**
   * Agent
   * @param requestBody
   * @returns any Successful Response
   * @throws ApiError
   */
  public static agentApiV1ChatAgentPost(requestBody: Conversation): CancelablePromise<any> {
    return __request(OpenAPI, {
      method: "POST",
      url: "/api/v1/chat/agent",
      body: requestBody,
      mediaType: "application/json",
      errors: {
        422: `Validation Error`,
      },
    })
  }

  /**
   * Run Cancel
   * @param runId
   * @returns boolean Successful Response
   * @throws ApiError
   */
  public static runCancelApiV1ChatRunRunIdCancelGet(runId: string): CancelablePromise<boolean> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/v1/chat/run/{run_id}/cancel",
      path: {
        run_id: runId,
      },
      errors: {
        422: `Validation Error`,
      },
    })
  }
}

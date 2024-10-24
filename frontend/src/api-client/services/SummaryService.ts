/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { WeeklySummaryResponse } from "../models/WeeklySummaryResponse"

import type { CancelablePromise } from "../core/CancelablePromise"
import { OpenAPI } from "../core/OpenAPI"
import { request as __request } from "../core/request"

export class SummaryService {
  /**
   * Get Weekly Summary Text
   * @returns WeeklySummaryResponse Successful Response
   * @throws ApiError
   */
  public static getWeeklySummaryTextApiV1SummaryWeeklyTextGet(): CancelablePromise<WeeklySummaryResponse> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/v1/summary/weekly/text",
    })
  }
}

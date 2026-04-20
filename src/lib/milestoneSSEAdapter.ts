import { MilestoneEvent } from "../types/milestone-flow.schema";

type EventCallback = (event: MilestoneEvent) => void;
type ErrorCallback = (error: Event) => void;

const SUPPORTED_EVENT_TYPES: MilestoneEvent["type"][] = [
  "flow_created",
  "node_ready",
  "node_started",
  "node_progress",
  "node_paused_for_approval",
  "node_blocked",
  "node_completed",
  "review_updated",
  "stable_view_updated",
];

function parseMilestoneEvent(
  type: MilestoneEvent["type"],
  raw: string,
): MilestoneEvent | null {
  try {
    const payload = JSON.parse(raw);
    return {
      type,
      payload,
    } as MilestoneEvent;
  } catch (error) {
    console.error(`[milestone-sse] failed to parse event ${type}`, error, raw);
    return null;
  }
}

export type MilestoneSSEConnection = {
  close: () => void;
};

export function connectMilestoneSSE(
  url: string,
  onEvent: EventCallback,
  onError?: ErrorCallback,
): MilestoneSSEConnection {
  const source = new EventSource(url);

  SUPPORTED_EVENT_TYPES.forEach((type) => {
    source.addEventListener(type, (evt) => {
      const message = evt as MessageEvent<string>;
      const parsed = parseMilestoneEvent(type, message.data);

      if (parsed) {
        onEvent(parsed);
      }
    });
  });

  source.onerror = (error) => {
    console.error("[milestone-sse] connection error", error);
    onError?.(error);
  };

  return {
    close: () => {
      source.close();
    },
  };
}

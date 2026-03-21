/* ========================================
   Veritas — Event Sequencer Hook
   Buffers and reorders WebSocket events by sequence number
   ======================================== */

import { useEffect, useRef } from "react";

/**
 * A sequenced event from the backend WebSocket
 */
export interface SequencedEvent {
  sequence: number;
  type: string;
  data: Record<string, unknown>;
}

/**
 * Event buffer for handling out-of-order WebSocket messages
 * Maintains a buffer of events and returns them in sequential order
 */
export class EventSequencer {
  private store: Map<number, SequencedEvent>;
  private nextSequence: number;

  constructor() {
    this.store = new Map();
    this.nextSequence = 1;
  }

  /**
   * Add an event to the buffer
   * @param event - The sequenced event to buffer
   */
  addEvent(event: SequencedEvent): void {
    this.store.set(event.sequence, event);
    this.flushReady();
  }

  /**
   * Get all ready events in sequential order
   * @returns Array of events that can be processed (consecutive sequence numbers)
   */
  getReadyEvents(): SequencedEvent[] {
    const ready: SequencedEvent[] = [];

    // Collect all consecutive events starting from nextSequence
    while (this.store.has(this.nextSequence)) {
      const event = this.store.get(this.nextSequence);
      if (event) {
        ready.push(event);
        this.store.delete(this.nextSequence);
        this.nextSequence++;
      } else {
        break;
      }
    }

    return ready;
  }

  /**
   * Get the expected next sequence number
   * @returns The next sequence number we expect to receive
   */
  getNextSequence(): number {
    return this.nextSequence;
  }

  /**
   * Reset the sequencer state
   * Clears all buffered events and resets the sequence counter
   */
  reset(): void {
    this.store.clear();
    this.nextSequence = 1;
  }

  /**
   * Get the number of buffered events waiting for their turn
   * @returns Count of events in the buffer
   */
  getBufferSize(): number {
    return this.store.size;
  }

  /**
   * Internal method to flush ready events to the ready array
   * Called automatically by addEvent
   */
  private flushReady(): void {
    // This is a no-op - actual flushing happens in getReadyEvents()
    // which allows the caller to control when events are processed
  }
}

/**
 * React hook for event sequencing
 * Maintains a sequencer instance across re-renders
 * @returns Object containing the sequencer and helper functions
 */
export function useEventSequencer() {
  const sequencerRef = useRef<EventSequencer | null>(null);

  // Initialize sequencer on first render
  useEffect(() => {
    sequencerRef.current = new EventSequencer();

    return () => {
      // Cleanup on unmount
      sequencerRef.current = null;
    };
  }, []);

  /**
   * Add an event to the sequencer buffer
   */
  const addEvent = (event: SequencedEvent) => {
    if (sequencerRef.current) {
      sequencerRef.current.addEvent(event);
    }
  };

  /**
   * Get all ready events in order
   */
  const getReadyEvents = (): SequencedEvent[] => {
    return sequencerRef.current?.getReadyEvents() ?? [];
  };

  /**
   * Get the expected next sequence number
   */
  const getNextSequence = (): number => {
    return sequencerRef.current?.getNextSequence() ?? 0;
  };

  /**
   * Get the current buffer size
   */
  const getBufferSize = (): number => {
    return sequencerRef.current?.getBufferSize() ?? 0;
  };

  /**
   * Reset the sequencer
   */
  const reset = () => {
    sequencerRef.current?.reset();
  };

  return {
    eventSequencer: sequencerRef.current,
    addEvent,
    getReadyEvents,
    getNextSequence,
    getBufferSize,
    reset,
  };
}

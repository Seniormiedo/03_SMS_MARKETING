import { useCallback, useEffect, useState } from "react";

interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

/**
 * Hook for managing async operations
 * @param asyncFunction - The async function to execute
 * @param immediate - Whether to execute immediately on mount
 * @returns [state, execute, reset]
 */
export function useAsync<T>(
  asyncFunction: () => Promise<T>,
  immediate: boolean = true
): [AsyncState<T>, () => Promise<void>, () => void] {
  const [state, setState] = useState<AsyncState<T>>({
    data: null,
    loading: immediate,
    error: null,
  });

  const execute = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));

    try {
      const data = await asyncFunction();
      setState({ data, loading: false, error: null });
    } catch (error) {
      setState({
        data: null,
        loading: false,
        error: error instanceof Error ? error.message : "An error occurred",
      });
    }
  }, [asyncFunction]);

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null });
  }, []);

  useEffect(() => {
    if (immediate) {
      execute();
    }
  }, [execute, immediate]);

  return [state, execute, reset];
}

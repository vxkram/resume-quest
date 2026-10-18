import { useCallback, useEffect, useState } from "react";
import { useLocation } from "react-router";

import { api } from "../api";

// Load an analysis by id, reusing the copy handed over by navigation when there is one.
export function useAnalysis(id) {
  const location = useLocation();
  const handed = location.state?.analysis;
  const [analysis, setAnalysis] = useState(handed?.id === id ? handed : null);
  const [error, setError] = useState(null);

  const reload = useCallback(() => api.analysis(id).then(setAnalysis, setError), [id]);

  useEffect(() => {
    if (analysis?.id !== id) reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  return { analysis, setAnalysis, error, reload };
}

import { useEffect, useState } from "react";

export function useAsyncData(loader, initialValue = null) {
  const [data, setData] = useState(initialValue);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function run() {
      try {
        setLoading(true);
        setError("");
        const result = await loader();
        if (active) {
          setData(result);
        }
      } catch (err) {
        if (active) {
          setError(err.message || "Something went wrong");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    run();

    return () => {
      active = false;
    };
  }, [loader]);

  return { data, loading, error };
}
